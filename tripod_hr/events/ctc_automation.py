import frappe

# Monthly CTC = total salary + accommodation + visa + iqama + medical + ticket + GOSI
# (gratuity and transport are excluded)
CTC_COMPONENTS = [
    "custom_accommodation",
    "custom_visa",
    "custom_iqama",
    "custom_medical_insurance",
    "custom_ticket_allowance",
    "custom_gosi",
]


def _compute(doc):
    """Set custom_monthly_ctc / custom_annual_ctc from salary + components."""
    total = float(doc.get("custom_total_salary") or 0)
    for f in CTC_COMPONENTS:
        total += float(doc.get(f) or 0)
    doc.custom_monthly_ctc = total
    doc.custom_annual_ctc = total * 12


def employee_before_save(doc, method=None):
    """Recompute CTC whenever an Employee is saved (salary or any component edited)."""
    _compute(doc)


def ssa_on_submit(doc, method=None):
    """On Salary Structure Assignment submit, push salary to Employee and recompute CTC."""
    _sync_from_ssa(doc.employee)


def ssa_on_cancel(doc, method=None):
    """On cancel, fall back to whatever the latest remaining submitted SSA says."""
    _sync_from_ssa(doc.employee)


def _sync_from_ssa(employee):
    if not employee:
        return

    latest = frappe.db.sql(
        """
        SELECT custom_total_salary
        FROM `tabSalary Structure Assignment`
        WHERE employee = %s AND docstatus = 1
        ORDER BY from_date DESC, creation DESC
        LIMIT 1
        """,
        employee,
    )
    if not latest:
        return

    salary = float(latest[0][0] or 0)

    emp = frappe.get_doc("Employee", employee)
    emp.custom_total_salary = salary
    _compute(emp)
    emp.flags.ignore_permissions = True
    emp.flags.ignore_mandatory = True
    emp.save()
