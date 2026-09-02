import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Plan"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Leave Plan Request",
			"width": 140,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 160,
		},
		{
			"label": _("Employment Type"),
			"fieldname": "employment_type",
			"fieldtype": "Link",
			"options": "Employment Type",
			"width": 130,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 120},
		{
			"label": _("Leave Type"),
			"fieldname": "leave_type",
			"fieldtype": "Link",
			"options": "Leave Type",
			"width": 160,
		},
		{"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 100},
		{"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 100},
		{"label": _("Days"), "fieldname": "total_days", "fieldtype": "Float", "width": 80},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{
			"label": _("Leave Application"),
			"fieldname": "leave_application",
			"fieldtype": "Link",
			"options": "Leave Application",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = []
	values = {}

	for fieldname in ("company", "employment_type", "department", "section", "leave_type", "status"):
		if filters.get(fieldname):
			conditions.append("and plan.{0} = %({0})s".format(fieldname))
			values[fieldname] = filters.get(fieldname)

	if filters.get("employee"):
		conditions.append("and plan.employee = %(employee)s")
		values["employee"] = filters.get("employee")

	if filters.get("from_date"):
		conditions.append("and plan.to_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("and plan.from_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	return frappe.db.sql(
		"""
		select
			plan.name, plan.employee, plan.employee_name, plan.company,
			plan.employment_type, plan.department, plan.section,
			plan.leave_type, plan.from_date, plan.to_date,
			plan.total_days, plan.status, plan.leave_application
		from `tabLeave Plan Request` plan
		where 1 = 1
			{conditions}
		order by plan.from_date, plan.employee_name
		""".format(conditions=" ".join(conditions)),
		values,
		as_dict=True,
	)
