import frappe
from frappe.utils import now


def execute():
	"""Restore ESS Workspace + install ESS Guidelines page via direct SQL."""
	ts = now()

	# ── 1. Install ess-guidelines Page ────────────────────────────────────
	page = "ess-guidelines"
	frappe.db.sql("DELETE FROM `tabHas Role` WHERE parent=%s AND parenttype='Page'", page)
	frappe.db.sql("DELETE FROM `tabPage` WHERE name=%s", page)
	frappe.db.commit()

	frappe.db.sql("""INSERT INTO `tabPage`
		(name,page_name,title,module,standard,system_page,owner,modified_by,creation,modified,docstatus)
		VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
		(page, "ESS Guidelines", "Appointment Guidelines", "Tripod HR",
		 "Yes", 0, "Administrator", "Administrator", ts, ts, 0))

	for i, role in enumerate(["Employee Self Service","Employee","HR Manager","HR User","System Manager"]):
		frappe.db.sql("""INSERT INTO `tabHas Role`
			(name,parent,parenttype,parentfield,role,idx,owner,modified_by,creation,modified,docstatus)
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
			(f"ess-pg-r{i}", page, "Page", "roles", role, i+1,
			 "Administrator", "Administrator", ts, ts, 0))

	frappe.db.commit()

	# ── 2. Restore ESS Workspace ─────────────────────────────────────────
	ws = "Employee Self Service"
	frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent=%s", ws)
	frappe.db.sql("DELETE FROM `tabHas Role` WHERE parent=%s AND parenttype='Workspace'", ws)
	frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name=%s", ws)
	frappe.db.commit()

	cols = [c['Field'] for c in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace`", as_dict=True)]
	data = {'name': ws, 'module': 'Tripod HR', 'public': 1, 'is_hidden': 0,
			'hide_custom': 0, 'sequence_id': 1.0, 'owner': 'Administrator',
			'modified_by': 'Administrator', 'creation': ts, 'modified': ts, 'docstatus': 0}
	for f in ['title', 'label']:
		if f in cols: data[f] = ws
	if 'content' in cols:
		data['content'] = '[{"id":"sc1","type":"shortcut","data":{}}]'
	if 'parent_page' in cols: data['parent_page'] = ''

	c = ','.join(f'`{k}`' for k in data)
	v = ','.join(['%s'] * len(data))
	frappe.db.sql(f"INSERT INTO `tabWorkspace` ({c}) VALUES ({v})", list(data.values()))

	for i, role in enumerate(['Employee Self Service','Employee','HR Manager','HR User']):
		frappe.db.sql("""INSERT INTO `tabHas Role`
			(name,parent,parenttype,parentfield,role,idx,owner,modified_by,creation,modified,docstatus)
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
			(f'ess-wr-{i}', ws, 'Workspace', 'roles', role, i+1,
			 'Administrator', 'Administrator', ts, ts, 0))

	sc_cols = [c['Field'] for c in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace Shortcut`", as_dict=True)]
	shortcuts = [
		(1,'Employee Advance','Employee Advance','DocType','Blue','calendar'),
		(2,'Employee','Employee','DocType','Blue','users'),
		(3,'Leave Application','Leave Application','DocType','Blue','calendar'),
		(4,'Documents Request F...','Documents Request Form','DocType','Gray','file-text'),
		(5,'Attendance','Attendance','DocType','Green','check-circle'),
		(6,'Expense Claim','Expense Claim','DocType','Red','file'),
		(7,'Compensatory Leave...','Compensatory Leave Request','DocType','Purple','star'),
		(8,'Appointment Guidelines','ess-guidelines','Page','Blue','calendar'),
		(9,'Company Policies','Company Policy','DocType','Green','file-text'),
	]

	for idx, label, link_to, stype, color, icon in shortcuts:
		sc = {'name': f'ess-sc-{idx}', 'parent': ws, 'parenttype': 'Workspace',
			  'parentfield': 'shortcuts', 'idx': idx, 'label': label,
			  'link_to': link_to, 'type': stype, 'owner': 'Administrator',
			  'modified_by': 'Administrator', 'creation': ts, 'modified': ts, 'docstatus': 0}
		if 'color' in sc_cols: sc['color'] = color
		if 'icon' in sc_cols: sc['icon'] = icon
		if 'doc_view' in sc_cols: sc['doc_view'] = 'List'
		c = ','.join(f'`{k}`' for k in sc)
		v = ','.join(['%s'] * len(sc))
		frappe.db.sql(f"INSERT INTO `tabWorkspace Shortcut` ({c}) VALUES ({v})", list(sc.values()))

	frappe.db.commit()
	frappe.clear_cache()
