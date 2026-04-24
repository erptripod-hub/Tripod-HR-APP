import frappe


@frappe.whitelist()
def get_my_guideline():
	user = frappe.session.user

	# Get employee record for current user
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": user, "status": "Active"},
		["name", "employee_name", "company", "image"],
		as_dict=True
	)

	# If no employee found, try by name match or use first company for admin
	if not employee:
		is_admin = "System Manager" in frappe.get_roles(user) or "HR Manager" in frappe.get_roles(user)
		if is_admin:
			# Show all guidelines for admin
			guidelines = frappe.get_all(
				"Appointment Guideline",
				fields=["name", "title", "company", "effective_date", "guideline_file"],
				filters={"status": "Active"},
				order_by="company asc"
			)
			return {
				"success": True,
				"is_admin": True,
				"employee": {"name": "Administrator", "company": "All Companies", "image": ""},
				"guidelines": guidelines,
				"guideline": guidelines[0] if guidelines else None
			}
		return {"success": False, "error": "No active employee record found for your account. Please ask HR to link your user to an Employee record."}

	company = employee.get("company")
	if not company:
		return {"success": False, "error": "No company assigned to your employee record. Please contact HR."}

	guideline = frappe.db.get_value(
		"Appointment Guideline",
		{"company": company, "status": "Active"},
		["name", "title", "company", "effective_date", "guideline_file"],
		as_dict=True
	)

	return {
		"success": True,
		"is_admin": False,
		"employee": {
			"name": employee.employee_name,
			"company": company,
			"image": employee.image
		},
		"guideline": guideline
	}
