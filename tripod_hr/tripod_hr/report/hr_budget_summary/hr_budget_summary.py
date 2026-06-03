import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data


def get_columns():
    return [
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 160},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 160},
        {"label": _("Headcount"), "fieldname": "headcount", "fieldtype": "Int", "width": 90},
        {"label": _("Total Salary"), "fieldname": "total_salary", "fieldtype": "Currency", "width": 130},
        {"label": _("Accommodation"), "fieldname": "accommodation", "fieldtype": "Currency", "width": 120},
        {"label": _("Visa"), "fieldname": "visa", "fieldtype": "Currency", "width": 90},
        {"label": _("Iqama"), "fieldname": "iqama", "fieldtype": "Currency", "width": 90},
        {"label": _("Medical"), "fieldname": "medical_insurance", "fieldtype": "Currency", "width": 100},
        {"label": _("Ticket"), "fieldname": "ticket_allowance", "fieldtype": "Currency", "width": 100},
        {"label": _("Transport"), "fieldname": "transport", "fieldtype": "Currency", "width": 100},
        {"label": _("Gratuity"), "fieldname": "gratuity_monthly", "fieldtype": "Currency", "width": 110},
        {"label": _("Monthly CTC"), "fieldname": "monthly_ctc", "fieldtype": "Currency", "width": 140},
        {"label": _("Annual CTC"), "fieldname": "annual_ctc", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    conditions = ["emp.status = 'Active'"]
    values = {}
    
    if filters.get("company"):
        conditions.append("emp.company = %(company)s")
        values["company"] = filters["company"]
    
    if filters.get("branch"):
        conditions.append("emp.branch = %(branch)s")
        values["branch"] = filters["branch"]
    
    if filters.get("department"):
        conditions.append("emp.department = %(department)s")
        values["department"] = filters["department"]
    
    where_clause = " AND ".join(conditions)
    
    rows = frappe.db.sql(f"""
        SELECT
            emp.company AS company,
            emp.branch AS branch,
            COUNT(emp.name) AS headcount,
            SUM(COALESCE(emp.custom_total_salary, 0)) AS total_salary,
            SUM(COALESCE(emp.custom_accommodation, 0)) AS accommodation,
            SUM(COALESCE(emp.custom_visa, 0)) AS visa,
            SUM(COALESCE(emp.custom_iqama, 0)) AS iqama,
            SUM(COALESCE(emp.custom_medical_insurance, 0)) AS medical_insurance,
            SUM(COALESCE(emp.custom_ticket_allowance, 0)) AS ticket_allowance,
            SUM(COALESCE(emp.custom_transport, 0)) AS transport,
            SUM(COALESCE(emp.custom_gratuity_monthly, 0)) AS gratuity_monthly,
            SUM(COALESCE(emp.custom_monthly_ctc, 0)) AS monthly_ctc,
            SUM(COALESCE(emp.custom_annual_ctc, 0)) AS annual_ctc
        FROM `tabEmployee` emp
        WHERE {where_clause}
        GROUP BY emp.company, emp.branch
        ORDER BY emp.company, emp.branch
    """, values=values, as_dict=True)
    
    totals = {
        "company": "<b>TOTAL</b>", "branch": "",
        "headcount": sum(r["headcount"] for r in rows),
        "total_salary": sum(r["total_salary"] for r in rows),
        "accommodation": sum(r["accommodation"] for r in rows),
        "visa": sum(r["visa"] for r in rows),
        "iqama": sum(r["iqama"] for r in rows),
        "medical_insurance": sum(r["medical_insurance"] for r in rows),
        "ticket_allowance": sum(r["ticket_allowance"] for r in rows),
        "transport": sum(r["transport"] for r in rows),
        "gratuity_monthly": sum(r["gratuity_monthly"] for r in rows),
        "monthly_ctc": sum(r["monthly_ctc"] for r in rows),
        "annual_ctc": sum(r["annual_ctc"] for r in rows),
    }
    
    if rows:
        rows.append(totals)
    
    return rows
