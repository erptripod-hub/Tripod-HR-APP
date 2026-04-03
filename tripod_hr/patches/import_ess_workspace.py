import frappe
import json
import os


def execute():
	"""
	Patch: Import Employee Self Service workspace and ensure
	Appointment Guideline + Company Policy doctypes are installed.
	Runs on bench migrate.
	"""

	# ── 1. Reload DocTypes so fields/permissions are current ──────────────
	for dt in ("Appointment Guideline", "Company Policy"):
		if frappe.db.exists("DocType", dt):
			frappe.reload_doc("tripod_hr", "doctype", dt.lower().replace(" ", "_"))

	# ── 2. Force-import the ESS Workspace from the JSON fixture ───────────
	workspace_json_path = os.path.join(
		os.path.dirname(__file__),
		"..",
		"tripod_hr",
		"workspace",
		"employee_self_service",
		"employee_self_service.json",
	)
	workspace_json_path = os.path.abspath(workspace_json_path)

	if os.path.exists(workspace_json_path):
		with open(workspace_json_path, "r") as f:
			workspace_data = json.load(f)

		workspace_name = workspace_data.get("name", "Employee Self Service")

		# Delete existing workspace record so we can re-import cleanly
		if frappe.db.exists("Workspace", workspace_name):
			frappe.delete_doc("Workspace", workspace_name, force=True, ignore_permissions=True)
			frappe.db.commit()

		# Insert fresh from JSON
		doc = frappe.get_doc(workspace_data)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert()
		frappe.db.commit()

		frappe.logger().info(f"Tripod HR: Workspace '{workspace_name}' imported successfully.")
	else:
		frappe.logger().warning(f"Tripod HR: Workspace JSON not found at {workspace_json_path}")

	# ── 3. Clear cache so changes show immediately ────────────────────────
	frappe.clear_cache()
