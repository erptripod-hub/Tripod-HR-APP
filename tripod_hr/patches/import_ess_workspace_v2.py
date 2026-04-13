import frappe
import json
import os
from frappe.utils import now


def execute():
	"""
	Patch v2: Install ESS Guidelines Page + ESS Workspace via raw SQL only.
	No doc.insert() calls - fully bypasses Developer Mode and validate hooks.
	"""
	base = os.path.join(os.path.dirname(__file__), "..", "tripod_hr")
	ts = now()

	# ── 1. Reload DocTypes ────────────────────────────────────────────────
	for dt in ("Appointment Guideline", "Company Policy"):
		if frappe.db.exists("DocType", dt):
			frappe.reload_doc("tripod_hr", "doctype", dt.lower().replace(" ", "_"))

	# ── 2. Install ESS Guidelines Page via raw SQL ────────────────────────
	page_name = "ess-guidelines"

	frappe.db.sql("DELETE FROM `tabHas Role` WHERE parent=%s AND parenttype='Page'", page_name)
	frappe.db.sql("DELETE FROM `tabPage` WHERE name=%s", page_name)
	frappe.db.commit()

	frappe.db.sql("""
		INSERT INTO `tabPage`
			(name, page_name, title, module, standard, system_page,
			 owner, modified_by, creation, modified, docstatus)
		VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""", (page_name, "ESS Guidelines", "ESS Guidelines & Policies",
		  "Tripod HR", "Yes", 0,
		  "Administrator", "Administrator", ts, ts, 0))

	for i, role in enumerate(["Employee Self Service", "Employee", "HR Manager", "HR User", "System Manager"]):
		frappe.db.sql("""
			INSERT INTO `tabHas Role`
				(name, parent, parenttype, parentfield, role, idx,
				 owner, modified_by, creation, modified, docstatus)
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
		""", (f"ess-role-{i}", page_name, "Page", "roles", role,
			  i + 1, "Administrator", "Administrator", ts, ts, 0))

	frappe.db.commit()

	# ── 3. Install ESS Workspace via raw SQL ──────────────────────────────
	ws_name = "Employee Self Service"

	frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent=%s", ws_name)
	frappe.db.sql("DELETE FROM `tabHas Role` WHERE parent=%s AND parenttype='Workspace'", ws_name)
	frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name=%s", ws_name)
	frappe.db.commit()

	frappe.db.sql("""
		INSERT INTO `tabWorkspace`
			(name, title, label, module, public, is_hidden, hide_custom,
			 sequence_id, owner, modified_by, creation, modified, docstatus)
		VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""", (ws_name, "Employee Self Service", "Employee Self Service",
		  "Tripod HR", 1, 0, 0,
		  1.0, "Administrator", "Administrator", ts, ts, 0))

	# Workspace roles
	for i, role in enumerate(["Employee Self Service", "Employee", "HR Manager", "HR User"]):
		frappe.db.sql("""
			INSERT INTO `tabHas Role`
				(name, parent, parenttype, parentfield, role, idx,
				 owner, modified_by, creation, modified, docstatus)
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
		""", (f"ws-role-{i}", ws_name, "Workspace", "roles", role,
			  i + 1, "Administrator", "Administrator", ts, ts, 0))

	# Workspace shortcuts
	shortcuts = [
		(1, "Employee Advance",        "Employee Advance",           "DocType", "Blue",   "calendar"),
		(2, "Employee",                 "Employee",                   "DocType", "Blue",   "users"),
		(3, "Leave Application",        "Leave Application",          "DocType", "Blue",   "calendar"),
		(4, "Documents Request F...",   "Documents Request Form",     "DocType", "Gray",   "file-text"),
		(5, "Attendance",               "Attendance",                 "DocType", "Green",  "check-circle"),
		(6, "Expense Claim",            "Expense Claim",              "DocType", "Red",    "file"),
		(7, "Compensatory Leave...",    "Compensatory Leave Request", "DocType", "Purple", "star"),
		(8, "Appointment Guidelines",   "ess-guidelines",             "Page",    "Blue",   "calendar"),
		(9, "Company Policies",         "ess-guidelines",             "Page",    "Green",  "file-text"),
	]

	for idx, label, link_to, stype, color, icon in shortcuts:
		frappe.db.sql("""
			INSERT INTO `tabWorkspace Shortcut`
				(name, parent, parenttype, parentfield, idx, label,
				 link_to, type, color, icon, doc_view,
				 owner, modified_by, creation, modified, docstatus)
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
		""", (f"ws-sc-{idx}", ws_name, "Workspace", "shortcuts", idx, label,
			  link_to, stype, color, icon, "List",
			  "Administrator", "Administrator", ts, ts, 0))

	frappe.db.commit()
	frappe.clear_cache()
	frappe.logger().info("Tripod HR: ESS patch v2 complete.")
