import frappe
from frappe.model.document import Document
from frappe.utils import today


class IdeaVault(Document):
	def before_insert(self):
		"""Auto-fill submitted_by and submitted_on if not set."""
		if not self.submitted_by:
			self.submitted_by = frappe.session.user
		if not self.submitted_on:
			self.submitted_on = today()

		# Try to set department from the employee record linked to the user
		if not self.department:
			employee = frappe.db.get_value(
				"Employee",
				{"user_id": frappe.session.user},
				"department"
			)
			if employee:
				self.department = employee

	def on_update(self):
		"""Record reviewer info when status moves away from Submitted."""
		if self.has_value_changed("status") and self.status != "Submitted":
			if not self.reviewed_by:
				self.reviewed_by = frappe.session.user
			if not self.reviewed_on:
				self.reviewed_on = today()
