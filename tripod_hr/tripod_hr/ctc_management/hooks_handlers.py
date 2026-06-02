import frappe
from frappe.utils import getdate, today, add_days, flt, nowdate
try:
    from .ctc_engine import (
        calculate_employee_ctc, sync_employee_fields, sync_ssa_fields,
        recalculate_and_sync, get_active_ssa, get_active_deployment, get_ctc_defaults
    )
except ImportError:
    from ctc_engine import (
        calculate_employee_ctc, sync_employee_fields, sync_ssa_fields,
        recalculate_and_sync, get_active_ssa, get_active_deployment, get_ctc_defaults
    )


def employee_before_save(doc, method=None):
    """Apply defaults from branch when CTC fields are blank."""
    if not doc.branch:
        return
    
    defaults = get_ctc_defaults(doc.branch)
    if not defaults:
        return
    
    if defaults.is_ksa_national_branch:
        doc.custom_accommodation = 0
        doc.custom_visa = 0
        doc.custom_iqama = 0
        doc.custom_medical_insurance = 0
        doc.custom_ticket_allowance = 0
        doc.custom_transport = 0
        return
    
    if not flt(doc.custom_accommodation):
        doc.custom_accommodation = flt(defaults.default_accommodation)
    if not flt(doc.custom_visa) and defaults.country == "UAE":
        doc.custom_visa = flt(defaults.default_visa)
    if not flt(doc.custom_iqama) and defaults.country == "KSA":
        doc.custom_iqama = flt(defaults.default_iqama)
    if not flt(doc.custom_medical_insurance):
        doc.custom_medical_insurance = flt(defaults.default_medical_insurance)
    if not flt(doc.custom_ticket_allowance):
        doc.custom_ticket_allowance = flt(defaults.default_ticket_allowance)
    if not flt(doc.custom_transport):
        doc.custom_transport = flt(defaults.default_transport)


def employee_after_save(doc, method=None):
    """Recalculate CTC after Employee save."""
    try:
        ctc = calculate_employee_ctc(doc.name)
        
        frappe.db.set_value("Employee", doc.name, {
            "custom_total_salary": ctc["total_salary"],
            "custom_gratuity_monthly": ctc["gratuity_monthly"],
            "custom_monthly_ctc": ctc["monthly_ctc"],
            "custom_annual_ctc": ctc["annual_ctc"]
        }, update_modified=False)
        
        if ctc["ssa_name"]:
            sync_ssa_fields(ctc["ssa_name"], ctc, doc.name)
    except Exception as e:
        frappe.log_error(f"CTC sync failed for {doc.name}: {str(e)}", "CTC Engine")


def ssa_before_save(doc, method=None):
    """When SSA is being saved (before submit), fetch CTC components from Employee."""
    if not doc.employee:
        return
    
    emp = frappe.get_doc("Employee", doc.employee)
    
    doc.custom_accommodation = flt(emp.get("custom_accommodation"))
    doc.custom_visa = flt(emp.get("custom_visa"))
    doc.custom_iqama = flt(emp.get("custom_iqama"))
    doc.custom_medical_insurance = flt(emp.get("custom_medical_insurance"))
    doc.custom_ticket_allowance = flt(emp.get("custom_ticket_allowance"))
    doc.custom_transport = flt(emp.get("custom_transport"))
    
    total_salary = 0
    basic = 0
    if doc.get("salary_details"):
        for row in doc.salary_details:
            total_salary += flt(row.amount)
            if row.salary_component and "basic" in row.salary_component.lower():
                basic = flt(row.amount)
    elif doc.get("base"):
        total_salary = flt(doc.base)
        basic = flt(doc.base)
    
    doc.custom_total_salary = total_salary
    
    try:
        from .ctc_engine import calculate_gratuity_monthly, get_years_of_service
    except ImportError:
        from ctc_engine import calculate_gratuity_monthly, get_years_of_service
    years = get_years_of_service(doc.employee, doc.from_date)
    gratuity = calculate_gratuity_monthly(basic, emp.branch, years)
    doc.custom_gratuity_monthly = gratuity
    
    monthly_ctc = (total_salary + doc.custom_accommodation + doc.custom_visa + 
                   doc.custom_iqama + doc.custom_medical_insurance + 
                   doc.custom_ticket_allowance + doc.custom_transport + gratuity)
    
    defaults = get_ctc_defaults(emp.branch)
    if defaults and defaults.is_ksa_national_branch:
        doc.custom_accommodation = 0
        doc.custom_visa = 0
        doc.custom_iqama = 0
        doc.custom_medical_insurance = 0
        doc.custom_ticket_allowance = 0
        doc.custom_transport = 0
        doc.custom_gratuity_monthly = 0
        monthly_ctc = total_salary
    
    doc.custom_monthly_ctc = monthly_ctc


def ssa_after_submit(doc, method=None):
    """After SSA submission, sync values back to Employee master."""
    try:
        emp_name = doc.employee
        ctc = calculate_employee_ctc(emp_name)
        sync_employee_fields(emp_name, ctc)
    except Exception as e:
        frappe.log_error(f"Employee sync failed after SSA submit {doc.name}: {str(e)}", "CTC Engine")


def salary_increment_on_submit(doc, method=None):
    """When Salary Increment is submitted, auto-create new SSA."""
    if not doc.employee:
        frappe.throw("Employee required on Salary Increment")
    
    if frappe.db.exists("Salary Structure Assignment", {
        "employee": doc.employee,
        "from_date": doc.effective_date,
        "docstatus": ["!=", 2]
    }):
        existing = frappe.db.get_value("Salary Structure Assignment", {
            "employee": doc.employee,
            "from_date": doc.effective_date,
            "docstatus": ["!=", 2]
        }, "name")
        frappe.msgprint(f"SSA already exists for this date: {existing}")
        return
    
    new_ssa = frappe.new_doc("Salary Structure Assignment")
    new_ssa.employee = doc.employee
    new_ssa.salary_structure = doc.new_salary_structure
    new_ssa.from_date = doc.effective_date
    new_ssa.company = doc.company
    new_ssa.base = doc.total_new_salary
    
    if doc.get("new_components"):
        for row in doc.new_components:
            new_ssa.append("salary_details", {
                "salary_component": row.salary_component,
                "amount": row.new_amount
            })
    
    new_ssa.insert(ignore_permissions=True)
    new_ssa.submit()
    
    frappe.msgprint(f"New SSA created: {new_ssa.name}")


def daily_ctc_recalculation():
    """Nightly scheduled job: recalc all active employees, catch tenure crossings."""
    employees = frappe.db.sql("""
        SELECT name FROM `tabEmployee` 
        WHERE status = 'Active'
    """, as_dict=True)
    
    success = 0
    errors = []
    
    for emp in employees:
        try:
            emp_name = emp["name"] if isinstance(emp, dict) else emp.name
            recalculate_and_sync(emp_name)
            success += 1
        except Exception as e:
            emp_name = emp.get("name", "unknown") if isinstance(emp, dict) else getattr(emp, "name", "unknown")
            errors.append(f"{emp_name}: {str(e)}")
    
    if errors:
        frappe.log_error(
            f"Daily CTC recalc: {success} success, {len(errors)} errors\n" + "\n".join(errors[:50]),
            "CTC Daily Recalc"
        )
    
    return {"success": success, "errors": len(errors)}


@frappe.whitelist()
def transfer_employee_deployment(employee, new_branch, effective_date, reason=None):
    """Public API: transfer an employee to a new branch (UAE <-> KSA)."""
    if not frappe.db.exists("Branch", new_branch):
        frappe.throw(f"Branch {new_branch} does not exist")
    
    emp = frappe.get_doc("Employee", employee)
    new_branch_company = frappe.db.get_value("CTC Component Default", new_branch, "company")
    
    if not new_branch_company:
        frappe.throw(f"No CTC Component Default configured for branch {new_branch}")
    
    if emp.get("custom_deployment_history"):
        for row in emp.custom_deployment_history:
            if not row.to_date:
                row.to_date = add_days(getdate(effective_date), -1)
    
    emp.append("custom_deployment_history", {
        "from_date": effective_date,
        "to_date": None,
        "deployed_to_branch": new_branch,
        "deployed_to_company": new_branch_company,
        "reason": reason or f"Transfer to {new_branch}"
    })
    
    emp.save(ignore_permissions=True)
    recalculate_and_sync(employee)
    
    return {"status": "success", "message": f"Transferred to {new_branch} effective {effective_date}"}


@frappe.whitelist()
def manual_recalculate(employee=None):
    """Manual trigger from UI button."""
    if employee:
        return recalculate_and_sync(employee)
    else:
        return daily_ctc_recalculation()
