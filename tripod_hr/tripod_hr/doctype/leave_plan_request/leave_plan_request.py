import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import date_diff, getdate, flt

SECTION_FIELD_CANDIDATES = (
	"custom_sub_department",
	"custom_section",
	"section",
	"custom_section_name",
	"custom_department_section",
)


def get_section_fieldname():
	meta = frappe.get_meta("Employee")
	for fieldname in SECTION_FIELD_CANDIDATES:
		if meta.has_field(fieldname):
			return fieldname
	return None


def get_employee_section(employee):
	fieldname = get_section_fieldname()
	if not fieldname or not employee:
		return None
	return frappe.db.get_value("Employee", employee, fieldname)


class LeavePlanRequest(Document):
	def validate(self):
		self.set_section()
		self.validate_dates()
		self.set_total_days()
		self.validate_overlap()

	def set_section(self):
		if not self.section:
			self.section = get_employee_section(self.employee)

	def validate_dates(self):
		if not (self.from_date and self.to_date):
			return
		if getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date."))

	def set_total_days(self):
		if not (self.from_date and self.to_date):
			return
		if not flt(self.total_days):
			self.total_days = date_diff(self.to_date, self.from_date) + 1

	def validate_overlap(self):
		if not (self.employee and self.from_date and self.to_date):
			return

		overlapping = frappe.db.sql(
			"""
			select name, from_date, to_date
			from `tabLeave Plan Request`
			where employee = %(employee)s
				and name != %(name)s
				and status not in ('Cancelled', 'Rejected')
				and from_date <= %(to_date)s
				and to_date >= %(from_date)s
			limit 1
			""",
			{
				"employee": self.employee,
				"name": self.name or "New Leave Plan Request",
				"from_date": self.from_date,
				"to_date": self.to_date,
			},
			as_dict=True,
		)

		if overlapping:
			row = overlapping[0]
			frappe.throw(
				_("This employee already has a plan from {0} to {1} ({2}).").format(
					frappe.format(row.from_date, {"fieldtype": "Date"}),
					frappe.format(row.to_date, {"fieldtype": "Date"}),
					row.name,
				)
			)


@frappe.whitelist()
def get_events(start, end, filters=None):
	from frappe.desk.reportview import get_filters_cond

	conditions = get_filters_cond("Leave Plan Request", filters, [])

	events = frappe.db.sql(
		"""
		select
			name, employee, employee_name, leave_type, reason,
			from_date, to_date, total_days, status,
			company, employment_type, department, section
		from `tabLeave Plan Request`
		where status not in ('Cancelled', 'Rejected')
			and from_date <= %(end)s
			and to_date >= %(start)s
			{conditions}
		order by from_date
		""".format(conditions=conditions),
		{"start": start, "end": end},
		as_dict=True,
	)

	for row in events:
		row["title"] = "{0} - {1}".format(row.employee_name or row.employee, row.leave_type)

	return events


@frappe.whitelist()
def get_filter_options():
	section_field = get_section_fieldname()

	sections = []
	if section_field:
		sections = [
			row[0]
			for row in frappe.db.sql(
				"select distinct `{0}` from `tabEmployee` where ifnull(`{0}`, '') != '' order by 1".format(
					section_field
				)
			)
		]

	return {
		"companies": frappe.get_all("Company", pluck="name", order_by="name"),
		"employment_types": frappe.get_all("Employment Type", pluck="name", order_by="name"),
		"departments": frappe.get_all("Department", pluck="name", order_by="name"),
		"sections": sections,
		"leave_types": frappe.get_all("Leave Type", pluck="name", order_by="name"),
		"section_field": section_field,
	}


@frappe.whitelist()
def get_board_data(start, end, company=None, employment_type=None, department=None, section=None):
	conditions = []
	values = {"start": start, "end": end}

	if company:
		conditions.append("and plan.company = %(company)s")
		values["company"] = company
	if employment_type:
		conditions.append("and plan.employment_type = %(employment_type)s")
		values["employment_type"] = employment_type
	if department:
		conditions.append("and plan.department = %(department)s")
		values["department"] = department
	if section:
		conditions.append("and plan.section = %(section)s")
		values["section"] = section

	plans = frappe.db.sql(
		"""
		select
			plan.name, plan.employee, plan.employee_name, plan.leave_type,
			plan.from_date, plan.to_date, plan.total_days, plan.status,
			plan.department, plan.section, plan.reason
		from `tabLeave Plan Request` plan
		where plan.status not in ('Cancelled', 'Rejected')
			and plan.from_date <= %(end)s
			and plan.to_date >= %(start)s
			{conditions}
		order by plan.employee_name, plan.from_date
		""".format(conditions=" ".join(conditions)),
		values,
		as_dict=True,
	)

	return {"plans": plans}


@frappe.whitelist()
def make_leave_application(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.status = "Open"
		target.description = source.reason or _("Created from leave plan {0}").format(source.name)

	doc = get_mapped_doc(
		"Leave Plan Request",
		source_name,
		{
			"Leave Plan Request": {
				"doctype": "Leave Application",
				"field_map": {
					"employee": "employee",
					"employee_name": "employee_name",
					"leave_type": "leave_type",
					"from_date": "from_date",
					"to_date": "to_date",
					"company": "company",
				},
			}
		},
		target_doc,
		set_missing_values,
	)

	return doc


@frappe.whitelist()
def mark_converted(plan, leave_application):
	frappe.db.set_value(
		"Leave Plan Request",
		plan,
		{"status": "Converted", "leave_application": leave_application},
	)
	return True
