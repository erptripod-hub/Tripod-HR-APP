import frappe
import json
import os


def execute():
	"""
	Patch: Install ESS Guidelines page + update ESS Workspace.
	Runs automatically on bench migrate.
	"""

	# 1. Reload DocTypes
	for dt_snake, dt_name in [
		("appointment_guideline", "Appointment Guideline"),
		("company_policy", "Company Policy"),
	]:
		if frappe.db.exists("DocType", dt_name):
			try:
				frappe.reload_doc("tripod_hr", "doctype", dt_snake)
			except Exception:
				pass

	# 2. Import ESS Guidelines Page
	page_json_path = os.path.abspath(os.path.join(
		os.path.dirname(__file__), "..",
		"tripod_hr", "page", "ess_guidelines", "ess_guidelines.json",
	))
	if os.path.exists(page_json_path):
		with open(page_json_path) as f:
			page_data = json.load(f)
		page_name = page_data.get("name", "ess-guidelines")
		if frappe.db.exists("Page", page_name):
			frappe.delete_doc("Page", page_name, force=True, ignore_permissions=True)
			frappe.db.commit()
		doc = frappe.get_doc(page_data)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert()
		frappe.db.commit()

	# 3. Import ESS Workspace
	workspace_json_path = os.path.abspath(os.path.join(
		os.path.dirname(__file__), "..",
		"tripod_hr", "workspace", "employee_self_service", "employee_self_service.json",
	))
	if os.path.exists(workspace_json_path):
		with open(workspace_json_path) as f:
			ws_data = json.load(f)
		ws_name = ws_data.get("name", "Employee Self Service")
		if frappe.db.exists("Workspace", ws_name):
			frappe.delete_doc("Workspace", ws_name, force=True, ignore_permissions=True)
			frappe.db.commit()
		doc = frappe.get_doc(ws_data)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert()
		frappe.db.commit()

	frappe.clear_cache()
