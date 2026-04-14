"""
Emergency fix script - run with:
bench --site tripod.k.frappe.cloud execute fix_ess.execute

Or copy contents into bench console:
bench --site tripod.k.frappe.cloud console
"""

import frappe
from frappe.utils import now_datetime
import json


def execute():
	ts = str(now_datetime())

	print("Step 1: Checking tabWorkspace columns...")
	cols = frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace`", as_dict=True)
	col_names = [c['Field'] for c in cols]
	print("Columns:", col_names)

	print("\nStep 2: Checking tabWorkspace Shortcut columns...")
	sc_cols = frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace Shortcut`", as_dict=True)
	sc_col_names = [c['Field'] for c in sc_cols]
	print("Columns:", sc_col_names)

	print("\nStep 3: Restoring ESS Workspace...")

	# Clean up
	frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent='Employee Self Service'")
	frappe.db.sql("DELETE FROM `tabHas Role` WHERE parent='Employee Self Service' AND parenttype='Workspace'")
	frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name='Employee Self Service'")
	frappe.db.commit()

	# Build insert with only columns that exist
	ws_data = {
		'name': 'Employee Self Service',
		'module': 'Tripod HR',
		'public': 1,
		'is_hidden': 0,
		'hide_custom': 0,
		'sequence_id': 1.0,
		'owner': 'Administrator',
		'modified_by': 'Administrator',
		'creation': ts,
		'modified': ts,
		'docstatus': 0,
	}

	# Add optional columns only if they exist
	if 'title' in col_names:
		ws_data['title'] = 'Employee Self Service'
	if 'label' in col_names:
		ws_data['label'] = 'Employee Self Service'
	if 'content' in col_names:
		ws_data['content'] = '[]'
	if 'parent_page' in col_names:
		ws_data['parent_page'] = ''
	if 'restrict_to_domain' in col_names:
		ws_data['restrict_to_domain'] = ''

	cols_str = ', '.join(f'`{k}`' for k in ws_data.keys())
	vals_str = ', '.join(['%s'] * len(ws_data))
	frappe.db.sql(
		f"INSERT INTO `tabWorkspace` ({cols_str}) VALUES ({vals_str})",
		list(ws_data.values())
	)
	print("Workspace inserted.")

	# Roles
	for i, role in enumerate(['Employee Self Service', 'Employee', 'HR Manager', 'HR User']):
		frappe.db.sql("""
			INSERT INTO `tabHas Role`
				(name, parent, parenttype, parentfield, role, idx,
				 owner, modified_by, creation, modified, docstatus)
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
		""", (f'ws-role-{i}', 'Employee Self Service', 'Workspace', 'roles',
			  role, i+1, 'Administrator', 'Administrator', ts, ts, 0))
	print("Workspace roles inserted.")

	# Shortcuts - check which columns exist first
	shortcuts = [
		('Employee Advance',       'Employee Advance',           'DocType', 'Blue',   'calendar',    'List'),
		('Employee',                'Employee',                   'DocType', 'Blue',   'users',        'List'),
		('Leave Application',       'Leave Application',          'DocType', 'Blue',   'calendar',    'List'),
		('Documents Request F...',  'Documents Request Form',     'DocType', 'Gray',   'file-text',   'List'),
		('Attendance',              'Attendance',                 'DocType', 'Green',  'check-circle','List'),
		('Expense Claim',           'Expense Claim',              'DocType', 'Red',    'file',        'List'),
		('Compensatory Leave...',   'Compensatory Leave Request', 'DocType', 'Purple', 'star',        'List'),
		('Appointment Guidelines',  'ess-guidelines',             'Page',    'Blue',   'calendar',    'List'),
		('Company Policies',        'ess-guidelines',             'Page',    'Green',  'file-text',   'List'),
	]

	for idx, (label, link_to, stype, color, icon, doc_view) in enumerate(shortcuts, 1):
		sc_data = {
			'name': f'ess-sc-{idx}',
			'parent': 'Employee Self Service',
			'parenttype': 'Workspace',
			'parentfield': 'shortcuts',
			'idx': idx,
			'label': label,
			'link_to': link_to,
			'type': stype,
			'owner': 'Administrator',
			'modified_by': 'Administrator',
			'creation': ts,
			'modified': ts,
			'docstatus': 0,
		}
		if 'color' in sc_col_names:
			sc_data['color'] = color
		if 'icon' in sc_col_names:
			sc_data['icon'] = icon
		if 'doc_view' in sc_col_names:
			sc_data['doc_view'] = doc_view

		c = ', '.join(f'`{k}`' for k in sc_data.keys())
		v = ', '.join(['%s'] * len(sc_data))
		frappe.db.sql(f"INSERT INTO `tabWorkspace Shortcut` ({c}) VALUES ({v})", list(sc_data.values()))

	frappe.db.commit()
	print("Shortcuts inserted.")

	# ESS Guidelines Page
	print("\nStep 4: Installing ESS Guidelines Page...")
	frappe.db.sql("DELETE FROM `tabHas Role` WHERE parent='ess-guidelines' AND parenttype='Page'")
	frappe.db.sql("DELETE FROM `tabPage` WHERE name='ess-guidelines'")
	frappe.db.commit()

	frappe.db.sql("""
		INSERT INTO `tabPage`
			(name, page_name, title, module, standard, system_page,
			 owner, modified_by, creation, modified, docstatus)
		VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""", ('ess-guidelines', 'ESS Guidelines', 'ESS Guidelines & Policies',
		  'Tripod HR', 'Yes', 0,
		  'Administrator', 'Administrator', ts, ts, 0))

	for i, role in enumerate(['Employee Self Service', 'Employee', 'HR Manager', 'HR User', 'System Manager']):
		frappe.db.sql("""
			INSERT INTO `tabHas Role`
				(name, parent, parenttype, parentfield, role, idx,
				 owner, modified_by, creation, modified, docstatus)
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
		""", (f'ess-pg-role-{i}', 'ess-guidelines', 'Page', 'roles',
			  role, i+1, 'Administrator', 'Administrator', ts, ts, 0))

	frappe.db.commit()
	print("Page installed.")

	frappe.clear_cache()
	print("\nDONE. ESS Workspace and Page restored successfully.")
