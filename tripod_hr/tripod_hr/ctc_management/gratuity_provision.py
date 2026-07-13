# Copyright (c) 2026, Tripod Mena
# Gratuity Provision — accrued End-of-Service liability from Date of Joining to today.
# Runs monthly (scheduler) and updates custom_gratuity_monthly on each active employee.
# NOT part of CTC — shown separately as a provision.
#
# Rules:
#   UAE (company != KSA): basic-wage basis
#        < 5 years : 21 days per year
#        >= 5 years: 21 days/yr for first 5 yrs + 30 days/yr thereafter
#   KSA (Tripod Global): full-wage basis (Article 84)
#        < 5 years : 15 days per year
#        >= 5 years: 15 days/yr for first 5 yrs + 30 days/yr thereafter
#
# Accrued = (days_earned / 30) * monthly_wage
# where days_earned integrates the per-year rate across the service period.

import frappe
from frappe.utils import getdate, nowdate, date_diff

KSA_COMPANY = "TRIPOD GLOBAL SHOPFIT MANUFACTURING COMPANY"


def _service_years(doj, today):
    if not doj:
        return 0.0
    days = date_diff(today, doj)
    if days <= 0:
        return 0.0
    return days / 365.25


def _days_earned(years, first_rate, later_rate=30.0):
    """Total EOS days accrued for `years` of service."""
    if years <= 0:
        return 0.0
    if years <= 5:
        return first_rate * years
    return (first_rate * 5) + (later_rate * (years - 5))


def calculate_accrued_gratuity(company, basic_or_wage, doj, today=None):
    today = today or nowdate()
    years = _service_years(getdate(doj), getdate(today))
    if years <= 0 or not basic_or_wage:
        return 0.0
    first_rate = 15.0 if company == KSA_COMPANY else 21.0
    days = _days_earned(years, first_rate, 30.0)
    accrued = (days / 30.0) * float(basic_or_wage)
    return round(accrued, 2)


def _get_wage_basis(emp):
    """UAE uses basic from latest SSA; KSA uses full total salary (custom_total_salary)."""
    if emp.company == KSA_COMPANY:
        return emp.get("custom_total_salary") or 0.0
    # UAE: basic component from latest submitted Salary Structure Assignment
    basic = frappe.db.sql(
        """
        SELECT sc_basic
        FROM `tabSalary Structure Assignment`
        WHERE employee = %s AND docstatus = 1
        ORDER BY from_date DESC, creation DESC
        LIMIT 1
        """,
        emp.name,
    )
    if basic and basic[0][0]:
        return float(basic[0][0])
    # Fallback: if no SSA basic, use custom_total_salary
    return emp.get("custom_total_salary") or 0.0


def update_all_gratuity_provisions():
    """Scheduled monthly: recompute accrued gratuity provision for all active employees."""
    today = nowdate()
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "company", "date_of_joining", "custom_total_salary"],
    )
    updated = 0
    for emp in employees:
        wage = _get_wage_basis(frappe._dict(emp))
        accrued = calculate_accrued_gratuity(emp.company, wage, emp.date_of_joining, today)
        frappe.db.set_value("Employee", emp.name, "custom_gratuity_monthly", accrued, update_modified=False)
        updated += 1
    frappe.db.commit()
    frappe.logger().info(f"[gratuity_provision] Updated {updated} employees on {today}")
    return updated


@frappe.whitelist()
def run_now():
    """Manual trigger from UI/console."""
    return update_all_gratuity_provisions()
