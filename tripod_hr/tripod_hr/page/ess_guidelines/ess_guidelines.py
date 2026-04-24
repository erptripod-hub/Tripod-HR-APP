import frappe


@frappe.whitelist()
def get_my_guideline():
	"""
	Returns the Appointment Guideline for the current employee's company.
	Employees only see their own company's file.
	"""
	user = frappe.session.user

	# Get employee record for current user
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": user, "status": "Active"},
		["name", "employee_name", "company", "image"],
		as_dict=True
	)

	if not employee:
		return {"success": False, "error": "No active employee record found for your account."}

	company = employee.get("company")
	if not company:
		return {"success": False, "error": "No company assigned to your employee record."}

	# Get guideline for this company
	guideline = frappe.db.get_value(
		"Appointment Guideline",
		{"company": company, "status": "Active"},
		["name", "title", "company", "effective_date", "guideline_file"],
		as_dict=True
	)

	return {
		"success": True,
		"employee": {
			"name": employee.employee_name,
			"company": company,
			"image": employee.image
		},
		"guideline": guideline
	}
