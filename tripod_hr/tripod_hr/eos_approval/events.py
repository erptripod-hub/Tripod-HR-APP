# Copyright (c) 2026, Tripod Mena
# EOS approval stamps + payment status from Journal Entries.

import frappe
from frappe import _
from frappe.utils import flt, now_datetime, nowdate

EOS_DOCTYPES = ("UAE EOS Calculation", "KSA EOS Calculation")
# State names as configured in the UAE / KSA EOS workflows
CPO_STATE = "Pending CPO Review & Approval"
FINANCE_STATE = "Pending Finance Approval"
APPROVED_STATE = "Approved"
HR_STATES = ("Draft", "HR Review", "Rejected")

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

	# Leaving HR's hands: every checklist item must be answered
	if new_state not in HR_STATES:
		_validate_checklist(doc)

	user, now = frappe.session.user, now_datetime()

	if new_state == FINANCE_STATE:
		doc.custom_cpo_approved_by = user
		doc.custom_cpo_approved_on = now
	elif new_state == APPROVED_STATE:
		doc.custom_finance_approved_by = user
		doc.custom_finance_approved_on = now
		if not doc.get("custom_payment_status"):
			doc.custom_payment_status = "Unpaid"
	elif new_state in HR_STATES or new_state == CPO_STATE:
		for f in APPROVAL_FIELDS:
			doc.set(f, None)


def eos_before_validate(doc, method=None):
	"""New EOS gets the checklist items from EOS Checklist Settings."""
	if doc.docstatus == 0 and not doc.get("custom_exit_checklist"):
		for item in get_checklist_items():
			doc.append("custom_exit_checklist", {"checklist_item": item})


def _validate_checklist(doc):
	missing = [d.checklist_item for d in doc.get("custom_exit_checklist") or [] if not d.answer]
	if missing:
		frappe.throw(
			_("Answer all Exit Checklist items before Submit for Approval:") + "<br>• " + "<br>• ".join(missing),
			title=_("Exit Checklist Incomplete"),
		)


@frappe.whitelist()
def get_checklist_items():
	return [d.checklist_item for d in frappe.get_single("EOS Checklist Settings").items]


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
	je.insert()  # left as Draft: payable team reviews and submits it
	frappe.msgprint(_("EOS liability Journal Entry {0} created as Draft for the payable team.").format(
		frappe.utils.get_link_to_form("Journal Entry", je.name)))


def eos_on_cancel(doc, method=None):
	jes = frappe.get_all(
		"Journal Entry",
		filters={"custom_eos_doctype": doc.doctype, "custom_eos_reference": doc.name, "docstatus": ["<", 2]},
		fields=["name", "docstatus"],
	)
	for je in jes:
		if je.docstatus == 1 and _bank_paid(je.name):
			frappe.throw(_("Cancel the payment Journal Entry {0} first.").format(je.name))
	for je in jes:
		if je.docstatus == 0:
			frappe.delete_doc("Journal Entry", je.name, ignore_permissions=True)
		else:
			d = frappe.get_doc("Journal Entry", je.name)
			d.flags.ignore_permissions = True
			d.cancel()


def _bank_paid(je_name):
	return frappe.db.sql(
		"""SELECT 1 FROM `tabJournal Entry Account` jea
		JOIN `tabAccount` acc ON acc.name = jea.account
		WHERE jea.parent = %s AND acc.account_type IN ('Bank', 'Cash') LIMIT 1""",
		je_name,
	)


def _liability_jv(dt, name):
	"""Submitted liability JV of an EOS (the one without bank / cash rows)."""
	for je in frappe.get_all(
		"Journal Entry",
		filters={"custom_eos_doctype": dt, "custom_eos_reference": name, "docstatus": 1},
		pluck="name", order_by="creation asc",
	):
		if not _bank_paid(je):
			return je


@frappe.whitelist()
def make_eos_bank_entry(source_name=None, eos_doctype=None, eos_name=None):
	"""Bank Entry against EOS Payable. Called from the liability JV (source_name)
	or from the EOS form (eos_doctype + eos_name)."""
	if eos_name:
		source_name = _liability_jv(eos_doctype, eos_name)
		if not source_name:
			frappe.throw(_("The liability Journal Entry for {0} is not submitted yet. The payable team must submit it first.").format(eos_name))

	jv = frappe.get_doc("Journal Entry", source_name)
	dt, name = jv.get("custom_eos_doctype"), jv.get("custom_eos_reference")
	if jv.docstatus != 1 or dt not in EOS_DOCTYPES or not name:
		frappe.throw(_("Make Bank Entry works only on a submitted EOS liability Journal Entry."))

	payable_row = next((r for r in jv.accounts if r.party_type == "Employee" and flt(r.credit_in_account_currency)), None)
	if not payable_row:
		frappe.throw(_("No EOS Payable (Employee) row found on {0}.").format(jv.name))

	eos = frappe.db.get_value(dt, name, ["net_payable", "custom_paid_amount", "employee", "employee_name"], as_dict=True)
	remaining = flt(eos.net_payable) - flt(eos.custom_paid_amount)
	if remaining <= 0:
		frappe.throw(_("{0} is already fully paid.").format(name))

	be = frappe.new_doc("Journal Entry")
	be.voucher_type = "Bank Entry"
	be.company = jv.company
	be.posting_date = nowdate()
	be.custom_eos_doctype = dt
	be.custom_eos_reference = name
	be.user_remark = f"End of Service payment - {eos.employee} {eos.employee_name or ''} ({name})"
	be.append("accounts", {
		"account": payable_row.account,
		"party_type": "Employee",
		"party": payable_row.party,
		"debit_in_account_currency": remaining,
		"reference_type": "Journal Entry",
		"reference_name": jv.name,
		"cost_center": payable_row.cost_center,
	})
	be.append("accounts", {
		"account": frappe.get_cached_value("Company", jv.company, "default_bank_account"),
		"credit_in_account_currency": remaining,
		"cost_center": payable_row.cost_center,
	})
	return be


# ----------------------------------------------------------------------
# Journal Entry: keep the linked EOS payment status in sync
# ----------------------------------------------------------------------
def je_validate(doc, method=None):
	if not doc.get("custom_eos_reference"):
		for row in doc.accounts:
			if row.reference_type == "Journal Entry" and row.reference_name:
				ref = frappe.db.get_value(
					"Journal Entry", row.reference_name, ["custom_eos_doctype", "custom_eos_reference"], as_dict=True
				)
				if ref and ref.custom_eos_reference:
					doc.custom_eos_doctype, doc.custom_eos_reference = ref.custom_eos_doctype, ref.custom_eos_reference
					break
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
