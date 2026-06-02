import frappe
from frappe.utils import getdate, today, add_days, date_diff, flt, nowdate, get_first_day, get_last_day
from datetime import datetime


def get_active_deployment(employee, on_date=None):
    """Get the deployment row active on a given date (defaults to today)."""
    on_date = getdate(on_date or today())
    emp_doc = frappe.get_doc("Employee", employee)
    
    if not emp_doc.get("custom_deployment_history"):
        return {
            "branch": emp_doc.branch,
            "company": emp_doc.company
        }
    
    for row in emp_doc.custom_deployment_history:
        from_date = getdate(row.from_date)
        to_date = getdate(row.to_date) if row.to_date else getdate("2099-12-31")
        if from_date <= on_date <= to_date:
            return {
                "branch": row.deployed_to_branch,
                "company": row.deployed_to_company
            }
    
    return {
        "branch": emp_doc.branch,
        "company": emp_doc.company
    }


def get_ctc_defaults(branch):
    """Get CTC component defaults for a branch."""
    if not branch:
        return None
    
    if not frappe.db.exists("CTC Component Default", branch):
        return None
    
    return frappe.get_doc("CTC Component Default", branch)


def get_years_of_service(employee, as_of_date=None):
    """Calculate completed years of service."""
    as_of_date = getdate(as_of_date or today())
    emp_doc = frappe.get_doc("Employee", employee)
    
    if not emp_doc.date_of_joining:
        return 0
    
    joining = getdate(emp_doc.date_of_joining)
    days = date_diff(as_of_date, joining)
    return days / 365.25


def calculate_gratuity_monthly(basic_salary, branch, years_of_service):
    """Calculate monthly gratuity accrual based on country, tenure, basic salary."""
    if not basic_salary or basic_salary <= 0:
        return 0
    
    defaults = get_ctc_defaults(branch)
    if not defaults:
        return 0
    
    if defaults.is_ksa_national_branch:
        return 0
    
    if years_of_service < defaults.probation_years_no_gratuity:
        return 0
    
    if years_of_service < 5:
        days_per_year = defaults.gratuity_days_year1to5
    else:
        days_per_year = defaults.gratuity_days_year5plus
    
    yearly_gratuity = (flt(basic_salary) / 30.0) * flt(days_per_year)
    return yearly_gratuity / 12.0


def get_basic_from_ssa(ssa_name):
    """Extract the Basic component amount from SSA's salary_details child table."""
    if not ssa_name:
        return 0
    
    ssa = frappe.get_doc("Salary Structure Assignment", ssa_name)
    
    if not ssa.get("salary_details"):
        return flt(ssa.base) if ssa.get("base") else 0
    
    for row in ssa.salary_details:
        if row.salary_component and "basic" in row.salary_component.lower():
            return flt(row.amount)
    
    return flt(ssa.base) if ssa.get("base") else 0


def get_total_salary_from_ssa(ssa_name):
    """Sum all earnings components from SSA's salary_details."""
    if not ssa_name:
        return 0
    
    ssa = frappe.get_doc("Salary Structure Assignment", ssa_name)
    
    if not ssa.get("salary_details"):
        return flt(ssa.base) if ssa.get("base") else 0
    
    total = 0
    for row in ssa.salary_details:
        total += flt(row.amount)
    
    return total


def get_active_ssa(employee, on_date=None):
    """Get the currently active SSA for an employee."""
    on_date = getdate(on_date or today())
    
    ssa = frappe.db.sql("""
        SELECT name FROM `tabSalary Structure Assignment`
        WHERE employee = %s
          AND docstatus = 1
          AND from_date <= %s
        ORDER BY from_date DESC
        LIMIT 1
    """, (employee, on_date), as_dict=True)
    
    return ssa[0]["name"] if ssa else None


def calculate_employee_ctc(employee, on_date=None):
    """
    Calculate full CTC breakdown for an employee.
    Returns dict with all components + monthly_ctc + annual_ctc.
    """
    on_date = getdate(on_date or today())
    emp = frappe.get_doc("Employee", employee)
    
    deployment = get_active_deployment(employee, on_date)
    branch = deployment["branch"]
    company = deployment["company"]
    
    defaults = get_ctc_defaults(branch)
    
    ssa_name = get_active_ssa(employee, on_date)
    total_salary = get_total_salary_from_ssa(ssa_name) if ssa_name else 0
    basic = get_basic_from_ssa(ssa_name) if ssa_name else 0
    
    years = get_years_of_service(employee, on_date)
    
    if defaults and defaults.is_ksa_national_branch:
        return {
            "branch": branch,
            "company": company,
            "total_salary": total_salary,
            "basic": basic,
            "accommodation": 0,
            "visa": 0,
            "iqama": 0,
            "medical_insurance": 0,
            "ticket_allowance": 0,
            "transport": 0,
            "gratuity_monthly": 0,
            "monthly_ctc": total_salary,
            "annual_ctc": total_salary * 12,
            "years_of_service": years,
            "ssa_name": ssa_name
        }
    
    home_branch = emp.branch
    in_home_branch = (branch == home_branch)
    
    if in_home_branch:
        accommodation = flt(emp.get("custom_accommodation")) or (flt(defaults.default_accommodation) if defaults else 0)
        visa = flt(emp.get("custom_visa")) or (flt(defaults.default_visa) if defaults else 0)
        iqama = flt(emp.get("custom_iqama")) or (flt(defaults.default_iqama) if defaults else 0)
        medical = flt(emp.get("custom_medical_insurance")) or (flt(defaults.default_medical_insurance) if defaults else 0)
        ticket = flt(emp.get("custom_ticket_allowance")) or (flt(defaults.default_ticket_allowance) if defaults else 0)
        transport = flt(emp.get("custom_transport")) or (flt(defaults.default_transport) if defaults else 0)
    else:
        accommodation = flt(defaults.default_accommodation) if defaults else 0
        visa = flt(defaults.default_visa) if defaults else 0
        iqama = flt(defaults.default_iqama) if defaults else 0
        medical = flt(defaults.default_medical_insurance) if defaults else 0
        home_defaults = get_ctc_defaults(home_branch)
        ticket = flt(emp.get("custom_ticket_allowance")) or (flt(home_defaults.default_ticket_allowance) if home_defaults else 0)
        transport = flt(emp.get("custom_transport")) or (flt(home_defaults.default_transport) if home_defaults else 0)
    
    gratuity = calculate_gratuity_monthly(basic, home_branch, years)
    
    monthly_ctc = total_salary + accommodation + visa + iqama + medical + ticket + transport + gratuity
    
    return {
        "branch": branch,
        "company": company,
        "total_salary": total_salary,
        "basic": basic,
        "accommodation": accommodation,
        "visa": visa,
        "iqama": iqama,
        "medical_insurance": medical,
        "ticket_allowance": ticket,
        "transport": transport,
        "gratuity_monthly": gratuity,
        "monthly_ctc": monthly_ctc,
        "annual_ctc": monthly_ctc * 12,
        "years_of_service": years,
        "ssa_name": ssa_name
    }


def sync_employee_fields(employee, ctc=None):
    """Update Employee master CTC display fields from calculation."""
    if ctc is None:
        ctc = calculate_employee_ctc(employee)
    
    frappe.db.set_value("Employee", employee, {
        "custom_total_salary": ctc["total_salary"],
        "custom_gratuity_monthly": ctc["gratuity_monthly"],
        "custom_monthly_ctc": ctc["monthly_ctc"],
        "custom_annual_ctc": ctc["annual_ctc"],
        "custom_ctc_last_updated_on": frappe.utils.now(),
        "custom_ctc_last_updated_by": frappe.session.user if frappe.session else "Administrator"
    }, update_modified=False)


def sync_ssa_fields(ssa_name, ctc=None, employee=None):
    """Update SSA CTC fields using db_set (works on submitted docs)."""
    if not ssa_name:
        return
    
    if ctc is None:
        if not employee:
            employee = frappe.db.get_value("Salary Structure Assignment", ssa_name, "employee")
        ctc = calculate_employee_ctc(employee)
    
    frappe.db.set_value("Salary Structure Assignment", ssa_name, {
        "custom_total_salary": ctc["total_salary"],
        "custom_accommodation": ctc["accommodation"],
        "custom_visa": ctc["visa"],
        "custom_iqama": ctc["iqama"],
        "custom_medical_insurance": ctc["medical_insurance"],
        "custom_ticket_allowance": ctc["ticket_allowance"],
        "custom_transport": ctc["transport"],
        "custom_gratuity_monthly": ctc["gratuity_monthly"],
        "custom_monthly_ctc": ctc["monthly_ctc"]
    }, update_modified=False)


def recalculate_and_sync(employee):
    """Master function: calc + sync to both Employee and active SSA."""
    ctc = calculate_employee_ctc(employee)
    sync_employee_fields(employee, ctc)
    if ctc["ssa_name"]:
        sync_ssa_fields(ctc["ssa_name"], ctc, employee)
    return ctc


def get_company_split_for_month(employee, year, month):
    """
    For deployment proration: returns {company: days} for a given month.
    """
    from calendar import monthrange
    start_date = datetime(year, month, 1).date()
    _, last_day = monthrange(year, month)
    end_date = datetime(year, month, last_day).date()
    total_days = (end_date - start_date).days + 1
    
    emp = frappe.get_doc("Employee", employee)
    
    if not emp.get("custom_deployment_history"):
        return {emp.company: total_days}
    
    company_days = {}
    current = start_date
    while current <= end_date:
        deployment = get_active_deployment(employee, current)
        comp = deployment["company"]
        company_days[comp] = company_days.get(comp, 0) + 1
        current = add_days(current, 1)
    
    return company_days


def calculate_company_split_ctc(employee, year, month):
    """
    Calculate prorated CTC per company for a month.
    Returns {company: {monthly_ctc, days, prorated_amount}}.
    """
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    total_days = last_day
    
    company_days = get_company_split_for_month(employee, year, month)
    
    result = {}
    for company, days in company_days.items():
        sample_date = datetime(year, month, min(days, last_day)).date()
        ctc = calculate_employee_ctc(employee, sample_date)
        prorated = (ctc["monthly_ctc"] * days) / total_days
        result[company] = {
            "monthly_ctc_at_company_rate": ctc["monthly_ctc"],
            "days": days,
            "prorated_amount": prorated,
            "branch": ctc["branch"]
        }
    
    return result
