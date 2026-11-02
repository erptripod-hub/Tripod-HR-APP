import frappe
from frappe.utils import now_datetime


def _is_acknowledged(employee, guideline, file_url):
	"""Acknowledged only if the record exists AND was for the current file.
	Legacy records with no stored file count as acknowledged."""
	ack = frappe.db.get_value(
		"Guideline Acknowledgement",
		{"employee": employee, "guideline": guideline},
		["name", "guideline_file"], as_dict=True
	)
	if not ack:
		return False
	return (not ack.guideline_file) or ack.guideline_file == (file_url or "")


@frappe.whitelist()
def get_pending_guideline():
	"""Used by the login popup. Returns the guideline the current user still
	has to acknowledge, or None."""
	user = frappe.session.user
	if user in ("Administrator", "Guest"):
		return None

	emp = frappe.db.get_value(
		"Employee",
		{"user_id": user, "status": "Active", "employment_type": "Office Staff"},
		["name", "employee_name", "company"], as_dict=True
	)
	if not emp or not emp.company:
		return None

	g = frappe.db.get_value(
		"Appointment Guideline",
		{"company": emp.company, "status": "Active"},
		["name", "title", "guideline_file"], as_dict=True
	)
	if not g or not g.guideline_file:
		return None
	if _is_acknowledged(emp.name, g.name, g.guideline_file):
		return None

	return {
		"employee": emp.name,
		"employee_name": emp.employee_name,
		"company": emp.company,
		"guideline": g.name,
		"title": g.title,
		"file": g.guideline_file,
	}


@frappe.whitelist()
def get_my_guideline():
	user = frappe.session.user
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": user, "status": "Active"},
		["name", "employee_name", "company", "image"],
		as_dict=True
	)

	if not employee:
		is_admin = bool(set(frappe.get_roles(user)) & {"System Manager", "HR Manager", "HR User"})
		if is_admin:
			guidelines = frappe.get_all(
				"Appointment Guideline",
				fields=["name", "title", "company", "effective_date", "guideline_file"],
				filters={"status": "Active"},
				order_by="company asc"
			)
			return {"success": True, "is_admin": True,
					"employee": {"name": "Administrator", "company": "All Companies", "image": "", "id": ""},
					"guidelines": guidelines,
					"guideline": guidelines[0] if guidelines else None}
		return {"success": False, "error": "No active employee record found. Ask HR to link your user to an Employee record."}

	company = employee.get("company")
	if not company:
		return {"success": False, "error": "No company assigned to your employee record. Contact HR."}

	guideline = frappe.db.get_value(
		"Appointment Guideline",
		{"company": company, "status": "Active"},
		["name", "title", "company", "effective_date", "guideline_file"],
		as_dict=True
	)

	acknowledged = False
	if guideline:
		acknowledged = _is_acknowledged(employee.name, guideline.name, guideline.guideline_file)

	return {
		"success": True, "is_admin": False,
		"employee": {"name": employee.employee_name, "company": company,
					 "image": employee.image, "id": employee.name},
		"guideline": guideline,
		"acknowledged": acknowledged
	}


@frappe.whitelist()
def acknowledge(employee, guideline):
	user = frappe.session.user
	emp_user = frappe.db.get_value("Employee", employee, "user_id")
	is_admin = bool(set(frappe.get_roles(user)) & {"System Manager", "HR Manager", "HR User"})

	if emp_user != user and not is_admin:
		frappe.throw("Not permitted", frappe.PermissionError)

	file_url = frappe.db.get_value("Appointment Guideline", guideline, "guideline_file") or ""

	if _is_acknowledged(employee, guideline, file_url):
		return {"already_done": True}

	existing = frappe.db.get_value(
		"Guideline Acknowledgement", {"employee": employee, "guideline": guideline}, "name"
	)
	if existing:
		# File was replaced since last acknowledgement - refresh the record
		doc = frappe.get_doc("Guideline Acknowledgement", existing)
		doc.acknowledged_on = now_datetime()
		doc.guideline_file = file_url
		doc.flags.ignore_permissions = True
		doc.save()
	else:
		doc = frappe.get_doc({
			"doctype": "Guideline Acknowledgement",
			"employee": employee,
			"guideline": guideline,
			"guideline_file": file_url,
			"acknowledged_on": now_datetime()
		})
		doc.flags.ignore_permissions = True
		doc.insert()
	frappe.db.commit()
	return {"success": True, "acknowledged_on": str(doc.acknowledged_on)}


@frappe.whitelist()
def get_acknowledgement_report(guideline):
	if not bool(set(frappe.get_roles(frappe.session.user)) & {"System Manager", "HR Manager", "HR User"}):
		frappe.throw("Not permitted", frappe.PermissionError)

	g = frappe.db.get_value("Appointment Guideline", guideline,
							["name", "title", "company", "guideline_file"], as_dict=True)
	if not g:
		frappe.throw("Guideline not found")

	# Only active Office Staff
	all_emp = frappe.get_all("Employee",
		filters={"company": g.company, "status": "Active", "employment_type": "Office Staff"},
		fields=["name", "employee_name", "designation", "department"])

	acks = {a.employee: a.acknowledged_on for a in frappe.get_all(
		"Guideline Acknowledgement",
		filters={"guideline": guideline},
		fields=["employee", "acknowledged_on", "guideline_file"]
	) if (not a.guideline_file) or a.guideline_file == (g.guideline_file or "")}

	acknowledged = []
	pending = []
	for e in all_emp:
		if e.name in acks:
			acknowledged.append({**e, "acknowledged_on": str(acks[e.name])})
		else:
			pending.append(e)

	return {
		"guideline": g,
		"acknowledged": acknowledged,
		"pending": pending,
		"total": len(all_emp),
		"ack_count": len(acknowledged),
		"pending_count": len(pending)
	}
