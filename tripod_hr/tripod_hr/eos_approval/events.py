# Copyright (c) 2026, Tripod Mena
# EOS approval stamps + payment status from Journal Entries.

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

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
