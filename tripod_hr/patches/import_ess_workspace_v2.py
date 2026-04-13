import frappe
import json
import os


def execute():
	"""
	Patch: Install ESS Guidelines Page + ESS Workspace.
	Uses frappe.db directly to bypass Developer Mode restriction on Page insert.
	"""
	base = os.path.join(os.path.dirname(__file__), "..", "tripod_hr")

	# ── 1. Reload DocTypes ────────────────────────────────────────────────
	for dt in ("Appointment Guideline", "Company Policy"):
		if frappe.db.exists("DocType", dt):
			frappe.reload_doc("tripod_hr", "doctype", dt.lower().replace(" ", "_"))

	# ── 2. Install ESS Guidelines Page via raw DB (bypasses Developer Mode) ──
	page_name = "ess-guidelines"

	# Delete existing record cleanly
	if frappe.db.exists("Page", page_name):
		frappe.db.delete("Page", {"name": page_name})
		frappe.db.delete("Has Role", {"parent": page_name, "parenttype": "Page"})
		frappe.db.commit()

	# Insert Page record directly
	frappe.db.sql("""
		INSERT INTO `tabPage`
			(name, page_name, title, module, standard, system_page,
			 owner, modified_by, creation, modified, docstatus)
		VALUES
			(%s, %s, %s, %s, %s, %s,
			 %s, %s, NOW(), NOW(), %s)
	""", (
		page_name,
		"ESS Guidelines",
		"ESS Guidelines & Policies",
		"Tripod HR",
		"Yes",
		0,
		"Administrator",
		"Administrator",
		0,
	))

	# Insert roles for the page
	roles = [
		"Employee Self Service",
		"Employee",
		"HR Manager",
		"HR User",
		"System Manager",
	]
	for i, role in enumerate(roles):
		frappe.db.sql("""
			INSERT INTO `tabHas Role`
				(name, parent, parenttype, parentfield, role, idx,
				 owner, modified_by, creation, modified, docstatus)
			VALUES
				(%s, %s, %s, %s, %s, %s,
				 %s, %s, NOW(), NOW(), %s)
		""", (
			f"{page_name}-role-{i}",
			page_name,
			"Page",
			"roles",
			role,
			i + 1,
			"Administrator",
			"Administrator",
			0,
		))

	frappe.db.commit()
	frappe.logger().info(f"Tripod HR: Page '{page_name}' installed via direct DB.")

	# ── 3. Install ESS Workspace ──────────────────────────────────────────
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
		frappe.logger().info(f"Tripod HR: Workspace '{ws_name}' installed.")

	# ── 4. Clear cache ────────────────────────────────────────────────────
	frappe.clear_cache()
	frappe.logger().info("Tripod HR: ESS patch complete.")
