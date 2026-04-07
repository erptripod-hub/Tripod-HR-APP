import frappe
import json
import os


def execute():
	"""
	Patch: Import ESS Guidelines Page + Employee Self Service Workspace.
	Runs automatically on bench migrate.
	"""
	base = os.path.join(os.path.dirname(__file__), "..", "tripod_hr")

	# 1. Reload DocTypes
	for dt in ("Appointment Guideline", "Company Policy"):
		if frappe.db.exists("DocType", dt):
			frappe.reload_doc("tripod_hr", "doctype", dt.lower().replace(" ", "_"))

	# 2. Install ESS Guidelines Page
	page_json_path = os.path.abspath(
		os.path.join(base, "page", "ess_guidelines", "ess_guidelines.json")
	)
	if os.path.exists(page_json_path):
		with open(page_json_path, "r") as f:
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

	# 3. Install ESS Workspace
	ws_json_path = os.path.abspath(
		os.path.join(base, "workspace", "employee_self_service", "employee_self_service.json")
	)
	if os.path.exists(ws_json_path):
		with open(ws_json_path, "r") as f:
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
