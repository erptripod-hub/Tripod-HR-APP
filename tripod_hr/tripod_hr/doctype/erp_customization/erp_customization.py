# Copyright (c) 2026, Tripod and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, nowdate


class ERPCustomization(Document):
	def validate(self):
		self.set_registration_status()
		self.sync_change_count()

	def set_registration_status(self):
		"""Registration is a one-time act. Once both names are present the record
		is Registered and stays that way; later changes only append to the log."""
		if self.requested_by and self.approved_by:
			self.registration_status = "Registered"
			if not self.approved_on:
				self.approved_on = nowdate()
			if not self.requested_on:
				self.requested_on = self.approved_on
		else:
			self.registration_status = "Needs Names"

	def sync_change_count(self):
		if not self.name or self.is_new():
			return
		self.change_count = frappe.db.count("ERP Change Log", {"customization": self.name})

	def before_insert(self):
		if not self.discovered_on:
			self.discovered_on = now_datetime()


@frappe.whitelist()
def set_approval(customization, requested_by, approved_by, approval_reference=None):
	"""Assign the two names once. Called from the register page."""
	doc = frappe.get_doc("ERP Customization", customization)
	if doc.registration_status == "Registered":
		frappe.throw("This customization is already registered. Approval is set once.")

	doc.requested_by = requested_by
	doc.approved_by = approved_by
	doc.approved_on = nowdate()
	doc.requested_on = doc.requested_on or nowdate()
	if approval_reference:
		doc.approval_reference = approval_reference
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "registration_status": doc.registration_status}
