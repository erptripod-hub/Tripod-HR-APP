# Copyright (c) 2026, Tripod Mena
# Captures a monthly snapshot of every active employee's budget figures.
# Run monthly (scheduler) or manually. Enables month-over-month comparison.

import frappe
from frappe.utils import nowdate, getdate


def capture_snapshot(month=None):
    """Freeze current budget figures for all active employees under a budget unit.
    month format: 'YYYY-MM' (defaults to current month)."""
    if not month:
        month = getdate(nowdate()).strftime("%Y-%m")

    employees = frappe.db.sql(
        """
        SELECT name, employee_name,
               COALESCE(custom_region,'') AS region,
               COALESCE(custom_budget_unit,'') AS budget_unit,
               COALESCE(custom_sub_department,'') AS sub_department,
               COALESCE(designation,'') AS designation,
               status,
               COALESCE(custom_total_salary,0) AS total_salary,
               (COALESCE(custom_accommodation,0)+COALESCE(custom_visa,0)+COALESCE(custom_iqama,0)
                +COALESCE(custom_medical_insurance,0)+COALESCE(custom_ticket_allowance,0)) AS allowances,
               COALESCE(custom_gosi,0) AS gosi,
               COALESCE(custom_monthly_ctc,0) AS monthly_ctc,
               COALESCE(custom_annual_ctc,0) AS annual_ctc,
               COALESCE(custom_gratuity_monthly,0) AS gratuity_provision
        FROM `tabEmployee`
        WHERE status='Active' AND custom_budget_unit IS NOT NULL AND custom_budget_unit!=''
        """,
        as_dict=True,
    )

    count = 0
    for e in employees:
        snap_name = f"SNAP-{month}-{e.name}"
        if frappe.db.exists("HR Budget Snapshot", snap_name):
            frappe.delete_doc("HR Budget Snapshot", snap_name, force=1, ignore_permissions=True)
        doc = frappe.get_doc({
            "doctype": "HR Budget Snapshot",
            "snapshot_month": month,
            "employee": e.name,
            "employee_name": e.employee_name,
            "region": e.region,
            "budget_unit": e.budget_unit,
            "sub_department": e.sub_department,
            "designation": e.designation,
            "status": e.status,
            "total_salary": e.total_salary,
            "allowances": e.allowances,
            "gosi": e.gosi,
            "monthly_ctc": e.monthly_ctc,
            "annual_ctc": e.annual_ctc,
            "gratuity_provision": e.gratuity_provision,
        })
        doc.insert(ignore_permissions=True)
        count += 1

    frappe.db.commit()
    frappe.logger().info(f"[budget_snapshot] Captured {count} for {month}")
    return count


@frappe.whitelist()
def capture_now(month=None):
    return capture_snapshot(month)


def monthly_capture():
    """Scheduler: capture snapshot for the month that just ended, on the 1st."""
    from frappe.utils import add_months
    prev = getdate(nowdate())
    month = prev.strftime("%Y-%m")
    return capture_snapshot(month)
