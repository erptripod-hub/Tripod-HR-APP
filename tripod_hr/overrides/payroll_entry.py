import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry


class CustomPayrollEntry(PayrollEntry):
    """Adds a custom `employment_type` filter to Payroll Entry's Get Employees flow.

    The custom field `employment_type` is added on Payroll Entry via the
    installer at `tripod_hr.tripod_hr.payroll_filter.install_employment_type_field`.

    When the user picks an Employment Type before clicking "Get Employees",
    only employees matching that Employment Type are pulled in.
    Leaving it blank keeps the standard HRMS behavior unchanged.
    """

    @frappe.whitelist()
    def fill_employee_details(self):
        # Let standard HRMS populate the employees child table normally
        result = super().fill_employee_details()

        # If user picked an employment type, filter out non-matching rows
        emp_type = getattr(self, "employment_type", None)
        if not emp_type:
            return result

        # Pull employment_type for everyone currently in the child table
        emp_ids = [row.employee for row in self.employees]
        if not emp_ids:
            return result

        emp_type_map = dict(
            frappe.get_all(
                "Employee",
                filters={"name": ("in", emp_ids)},
                fields=["name", "employment_type"],
                as_list=True,
            )
        )

        filtered = [row for row in self.employees if emp_type_map.get(row.employee) == emp_type]

        # If filter removed every row, give the user a clear message instead of silent empty
        if not filtered:
            frappe.throw(
                _("No employees found with Employment Type: {0}").format(frappe.bold(emp_type)),
                title=_("No employees found"),
            )

        self.set("employees", filtered)
        self.number_of_employees = len(self.employees)
        return result
