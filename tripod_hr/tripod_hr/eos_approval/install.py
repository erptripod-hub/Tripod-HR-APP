# Copyright (c) 2026, Tripod Mena
# EOS approval + payment tracking setup (UAE / KSA EOS Calculation).
# Idempotent: safe on every migrate.
#   - Approval / payment fields on both EOS doctypes
#   - Signature image field on User (used by the EOS print formats)
#   - EOS link fields on Journal Entry (payment JE -> EOS)
#   - Workflow: Draft -> Pending CPO Approval -> Pending Finance Approval -> Approved
#     (created only if the doctype has no workflow yet, so later UI edits are kept)

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

EOS_DOCTYPES = ("UAE EOS Calculation", "KSA EOS Calculation")

HR_ROLE = "EOS Creator"
CPO_ROLE = "CPO Approver"
FINANCE_ROLE = "Finance Approval"

STATES = [
	("Draft", "Warning"),
	("Pending CPO Review & Approval", "Warning"),
	("Pending Finance Approval", "Primary"),
	("Approved", "Success"),
	("HR Review", "Warning"),
	("Rejected", "Danger"),
	("Cancelled", "Danger"),
]
ACTIONS = ["Submit for Approval", "Approve", "Reject", "Cancel"]


DEFAULT_CHECKLIST = [
	"Laptop / desktop and charger returned",
	"Email disabled and forwarding set",
	"ERPNext and system access removed",
	"Accommodation vacated and keys returned",
	"Handover of work and files done",
	"Loans and advances cleared",
]


def _eos_fields():
	return [
		{"fieldname": "custom_exit_checklist_section", "label": "Exit Checklist", "fieldtype": "Section Break", "insert_after": "payment_date"},
		{"fieldname": "custom_exit_checklist", "label": "Exit Checklist", "fieldtype": "Table", "options": "EOS Exit Checklist Item", "insert_after": "custom_exit_checklist_section",
		 "description": "Answer every item (Yes / No / Not Applicable) before Submit for Approval."},
		{"fieldname": "custom_approval_section", "label": "Approvals", "fieldtype": "Section Break", "insert_after": "cleared_on"},
		{"fieldname": "custom_cpo_approved_by", "label": "CPO Approved By", "fieldtype": "Link", "options": "User", "read_only": 1, "insert_after": "custom_approval_section"},
		{"fieldname": "custom_cpo_approved_on", "label": "CPO Approved On", "fieldtype": "Datetime", "read_only": 1, "insert_after": "custom_cpo_approved_by"},
		{"fieldname": "custom_approval_cb", "fieldtype": "Column Break", "insert_after": "custom_cpo_approved_on"},
		{"fieldname": "custom_finance_approved_by", "label": "Finance Approved By", "fieldtype": "Link", "options": "User", "read_only": 1, "insert_after": "custom_approval_cb"},
		{"fieldname": "custom_finance_approved_on", "label": "Finance Approved On", "fieldtype": "Datetime", "read_only": 1, "insert_after": "custom_finance_approved_by"},
		{"fieldname": "custom_payment_section", "label": "Payment Status", "fieldtype": "Section Break", "insert_after": "custom_finance_approved_on"},
		{"fieldname": "custom_payment_status", "label": "Payment Status", "fieldtype": "Select", "options": "\nUnpaid\nPartly Paid\nPaid", "read_only": 1, "allow_on_submit": 1, "in_list_view": 1, "in_standard_filter": 1, "insert_after": "custom_payment_section"},
		{"fieldname": "custom_paid_amount", "label": "Paid Amount", "fieldtype": "Currency", "read_only": 1, "allow_on_submit": 1, "insert_after": "custom_payment_status"},
		{"fieldname": "custom_payment_cb", "fieldtype": "Column Break", "insert_after": "custom_paid_amount"},
		{"fieldname": "custom_payment_reference", "label": "Payment Journal Entry", "fieldtype": "Link", "options": "Journal Entry", "read_only": 1, "allow_on_submit": 1, "insert_after": "custom_payment_cb"},
	]


def install():
	fields = {dt: _eos_fields() for dt in EOS_DOCTYPES}
	fields["User"] = [
		{"fieldname": "custom_signature", "label": "Signature", "fieldtype": "Attach Image", "insert_after": "user_image",
		 "description": "Transparent PNG. Printed on approval documents (e.g. EOS) when this user approves."},
	]
	fields["Company"] = [
		{"fieldname": "custom_eos_accounts_section", "label": "End of Service Accounts", "fieldtype": "Section Break", "insert_after": "default_expense_account", "collapsible": 1},
		{"fieldname": "custom_eos_expense_account", "label": "EOS Expense Account", "fieldtype": "Link", "options": "Account", "insert_after": "custom_eos_accounts_section"},
		{"fieldname": "custom_eos_payable_account", "label": "EOS Payable Account", "fieldtype": "Link", "options": "Account", "insert_after": "custom_eos_expense_account",
		 "description": "Liability ledger with Account Type = Payable. EOS is booked here per employee on Finance approval."},
	]
	fields["Journal Entry"] = [
		{"fieldname": "custom_eos_doctype", "label": "EOS Type", "fieldtype": "Link", "options": "DocType", "allow_on_submit": 1, "insert_after": "user_remark"},
		{"fieldname": "custom_eos_reference", "label": "End of Service", "fieldtype": "Dynamic Link", "options": "custom_eos_doctype", "allow_on_submit": 1, "insert_after": "custom_eos_doctype"},
	]
	create_custom_fields(fields, update=True)

	# Old Mark as Cleared button is replaced by the workflow
	for dt in EOS_DOCTYPES:
		frappe.make_property_setter(
			{"doctype": dt, "fieldname": "mark_as_cleared", "property": "hidden", "value": "1", "property_type": "Check"},
			validate_fields_for_doctype=False,
		)

	_ensure_masters()
	_ensure_checklist_settings()
	for dt in EOS_DOCTYPES:
		_ensure_workflow(dt)
		# EOS submitted before this setup were paid outside the system
		frappe.db.sql(
			f"""UPDATE `tab{dt}` SET custom_payment_status = 'Paid'
			WHERE docstatus = 1 AND IFNULL(custom_payment_status, '') = ''"""
		)
		_fill_draft_checklists(dt)
	frappe.db.commit()


def _ensure_masters():
	if not frappe.db.exists("Role", CPO_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": CPO_ROLE, "desk_access": 1}).insert(ignore_permissions=True)
	for state, style in STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state, "style": style}).insert(ignore_permissions=True)
	for action in ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)


def _ensure_workflow(dt):
	if frappe.db.exists("Workflow", {"document_type": dt}):
		return

	def tr(state, action, next_state, role):
		return {"state": state, "action": action, "next_state": next_state, "allowed": role, "allow_self_approval": 1}

	frappe.get_doc({
		"doctype": "Workflow",
		"workflow_name": f"{dt} Approval",
		"document_type": dt,
		"is_active": 1,
		"send_email_alert": 1,
		"workflow_state_field": "workflow_state",
		"states": [
			{"state": "Draft", "doc_status": "0", "allow_edit": HR_ROLE},
			{"state": "Pending CPO Review & Approval", "doc_status": "0", "allow_edit": CPO_ROLE},
			{"state": "Pending Finance Approval", "doc_status": "0", "allow_edit": FINANCE_ROLE},
			{"state": "Approved", "doc_status": "1", "allow_edit": FINANCE_ROLE},
			{"state": "HR Review", "doc_status": "0", "allow_edit": HR_ROLE},
			{"state": "Cancelled", "doc_status": "2", "allow_edit": FINANCE_ROLE},
		],
		"transitions": [
			tr("Draft", "Submit for Approval", "Pending CPO Review & Approval", HR_ROLE),
			tr("HR Review", "Submit for Approval", "Pending CPO Review & Approval", HR_ROLE),
			tr("Pending CPO Review & Approval", "Approve", "Pending Finance Approval", CPO_ROLE),
			tr("Pending CPO Review & Approval", "Reject", "HR Review", CPO_ROLE),
			tr("Pending Finance Approval", "Approve", "Approved", FINANCE_ROLE),
			tr("Pending Finance Approval", "Reject", "HR Review", FINANCE_ROLE),
			tr("Approved", "Cancel", "Cancelled", FINANCE_ROLE),
		],
	}).insert(ignore_permissions=True)


def _ensure_checklist_settings():
	settings = frappe.get_single("EOS Checklist Settings")
	if settings.get("items"):
		return
	for item in DEFAULT_CHECKLIST:
		settings.append("items", {"checklist_item": item})
	settings.flags.ignore_permissions = True
	settings.save()


def _fill_draft_checklists(dt):
	"""Add the checklist rows (blank answers) to drafts that have none yet."""
	items = [d.checklist_item for d in frappe.get_single("EOS Checklist Settings").items]
	if not items:
		return
	drafts = frappe.db.sql_list(
		f"""SELECT name FROM `tab{dt}` p WHERE docstatus = 0 AND NOT EXISTS (
			SELECT 1 FROM `tabEOS Exit Checklist Item` c
			WHERE c.parent = p.name AND c.parenttype = %s)""",
		dt,
	)
	for name in drafts:
		for idx, item in enumerate(items, start=1):
			frappe.get_doc({
				"doctype": "EOS Exit Checklist Item",
				"parent": name, "parenttype": dt, "parentfield": "custom_exit_checklist",
				"idx": idx, "checklist_item": item,
			}).db_insert()
