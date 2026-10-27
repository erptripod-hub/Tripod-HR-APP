# Copyright (c) 2026, Tripod Mena
# EOS approval stamps + payment status from Journal Entries.

import frappe
from frappe import _
from frappe.utils import flt, now_datetime, nowdate

EOS_DOCTYPES = ("UAE EOS Calculation", "KSA EOS Calculation")
APPROVAL_FIELDS = (
	"custom_cpo_approved_by", "custom_cpo_approved_on",
	"custom_finance_approved_by", "custom_finance_approved_on",
)


# ----------------------------------------------------------------------
# EOS: record who approved and when, from the workflow state change
# ----------------------------------------------------------------------
def eos_validate(doc, method=None):
	new_state = doc.get("workflow_state")
	old = doc.get_doc_before_save()
	old_state = old.get("workflow_state") if old else None
	if not new_state or new_state == old_state:
		return

	user, now = frappe.session.user, now_datetime()

	if new_state == "Pending Finance Approval":
		doc.custom_cpo_approved_by = user
		doc.custom_cpo_approved_on = now
	elif new_state == "Approved":
		doc.custom_finance_approved_by = user
		doc.custom_finance_approved_on = now
		if not doc.get("custom_payment_status"):
			doc.custom_payment_status = "Unpaid"
	elif new_state in ("Draft", "Rejected", "Pending CPO Approval"):
		for f in APPROVAL_FIELDS:
			doc.set(f, None)


# ----------------------------------------------------------------------
# EOS: on Finance approval book the liability per employee (auto JV)
#   Dr EOS Expense            (cost center of employee)
#   Cr EOS Payable  Employee  (net payable)
# Bank payment is then made by Finance against EOS Payable.
# ----------------------------------------------------------------------
def _eos_accounts(company):
	expense, payable = frappe.db.get_value(
		"Company", company, ["custom_eos_expense_account", "custom_eos_payable_account"]
	) or (None, None)
	if not expense or not payable:
		frappe.throw(_("Set EOS Expense Account and EOS Payable Account on Company {0} (End of Service Accounts section).").format(company))
	if frappe.db.get_value("Account", payable, "account_type") != "Payable":
		frappe.throw(_("EOS Payable Account {0} must have Account Type = Payable.").format(payable))
	return expense, payable


def eos_on_submit(doc, method=None):
	amount = flt(doc.net_payable, 2)
	if amount <= 0:
		frappe.db.set_value(doc.doctype, doc.name, "custom_payment_status", "Paid")
		return

	expense, payable = _eos_accounts(doc.company)
	cost_center = (
		frappe.db.get_value("Employee", doc.employee, "payroll_cost_center")
		or frappe.get_cached_value("Company", doc.company, "cost_center")
	)

	je = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Journal Entry",
		"company": doc.company,
		"posting_date": nowdate(),
		"custom_eos_doctype": doc.doctype,
		"custom_eos_reference": doc.name,
		"user_remark": f"End of Service liability - {doc.employee} {doc.employee_name or ''} ({doc.name})",
		"accounts": [
			{"account": expense, "debit_in_account_currency": amount, "cost_center": cost_center},
			{"account": payable, "party_type": "Employee", "party": doc.employee,
			 "credit_in_account_currency": amount, "cost_center": cost_center},
		],
	})
	je.flags.ignore_permissions = True
	je.insert()
	je.submit()
	frappe.msgprint(_("EOS liability booked: {0}").format(frappe.utils.get_link_to_form("Journal Entry", je.name)))


def eos_on_cancel(doc, method=None):
	jes = frappe.get_all(
		"Journal Entry",
		filters={"custom_eos_doctype": doc.doctype, "custom_eos_reference": doc.name, "docstatus": 1},
		pluck="name",
	)
	for name in jes:
		if _bank_paid(name):
			frappe.throw(_("Cancel the payment Journal Entry {0} first.").format(name))
	for name in jes:
		je = frappe.get_doc("Journal Entry", name)
		je.flags.ignore_permissions = True
		je.cancel()


def _bank_paid(je_name):
	return frappe.db.sql(
		"""SELECT 1 FROM `tabJournal Entry Account` jea
		JOIN `tabAccount` acc ON acc.name = jea.account
		WHERE jea.parent = %s AND acc.account_type IN ('Bank', 'Cash') LIMIT 1""",
		je_name,
	)


@frappe.whitelist()
def get_payment_defaults(company):
	return {
		"payable_account": frappe.db.get_value("Company", company, "custom_eos_payable_account"),
		"bank_account": frappe.db.get_value("Company", company, "default_bank_account"),
	}


# ----------------------------------------------------------------------
# Journal Entry: keep the linked EOS payment status in sync
# ----------------------------------------------------------------------
def je_validate(doc, method=None):
	dt, name = doc.get("custom_eos_doctype"), doc.get("custom_eos_reference")
	if not name:
		return
	if dt not in EOS_DOCTYPES:
		frappe.throw(_("EOS Type must be UAE EOS Calculation or KSA EOS Calculation."))
	if frappe.db.get_value(dt, name, "docstatus") != 1:
		frappe.throw(_("{0} {1} is not approved yet. Payment can be made only after Finance approval.").format(dt, name))


def je_sync_eos(doc, method=None):
	refs = set()
	if doc.get("custom_eos_reference"):
		refs.add((doc.custom_eos_doctype, doc.custom_eos_reference))
	old = doc.get_doc_before_save()
	if old and old.get("custom_eos_reference"):
		refs.add((old.custom_eos_doctype, old.custom_eos_reference))
	for dt, name in refs:
		if dt in EOS_DOCTYPES:
			update_eos_payment(dt, name)


def update_eos_payment(dt, name):
	if not frappe.db.exists(dt, name):
		return
	net_payable = flt(frappe.db.get_value(dt, name, "net_payable"))

	rows = frappe.db.sql(
		"""
		SELECT je.name, SUM(jea.credit) - SUM(jea.debit) AS paid
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		JOIN `tabAccount` acc ON acc.name = jea.account
		WHERE je.docstatus = 1
			AND je.custom_eos_doctype = %s
			AND je.custom_eos_reference = %s
			AND acc.account_type IN ('Bank', 'Cash')
		GROUP BY je.name
		ORDER BY je.posting_date DESC, je.creation DESC
		""",
		(dt, name),
		as_dict=True,
	)
	paid = flt(sum(flt(r.paid) for r in rows), 2)

	if paid <= 0:
		status = "Unpaid"
	elif paid >= net_payable - 0.01:
		status = "Paid"
	else:
		status = "Partly Paid"

	frappe.db.set_value(dt, name, {
		"custom_payment_status": status,
		"custom_paid_amount": paid,
		"custom_payment_reference": rows[0].name if rows else None,
	})
