import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, get_last_day, add_months
from datetime import date


def execute(filters=None):
    filters = filters or {}
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters):
    year = int(filters.get("year", date.today().year))
    
    cols = [
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 160},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 160},
    ]
    
    for m in range(1, 13):
        month_name = date(year, m, 1).strftime("%b")
        cols.append({
            "label": f"{month_name}",
            "fieldname": f"month_{m}",
            "fieldtype": "Currency",
            "width": 110
        })
    
    cols.append({"label": _("YTD"), "fieldname": "ytd", "fieldtype": "Currency", "width": 130})
    
    return cols


def get_data(filters):
    year = int(filters.get("year", date.today().year))
    company_filter = filters.get("company")
    
    where = ["emp.status IN ('Active', 'Left')"]
    values = {}
    if company_filter:
        where.append("emp.company = %(company)s")
        values["company"] = company_filter
    
    employees = frappe.db.sql(f"""
        SELECT 
            emp.name,
            emp.company,
            emp.branch,
            emp.date_of_joining,
            emp.relieving_date,
            COALESCE(emp.custom_monthly_ctc, 0) AS monthly_ctc
        FROM `tabEmployee` emp
        WHERE {' AND '.join(where)}
    """, values=values, as_dict=True)
    
    by_branch = {}
    
    for emp in employees:
        key = (emp["company"], emp["branch"])
        if key not in by_branch:
            by_branch[key] = {
                "company": emp["company"],
                "branch": emp["branch"]
            }
            for m in range(1, 13):
                by_branch[key][f"month_{m}"] = 0
            by_branch[key]["ytd"] = 0
        
        doj = getdate(emp["date_of_joining"]) if emp["date_of_joining"] else None
        relieving = getdate(emp["relieving_date"]) if emp["relieving_date"] else None
        
        for m in range(1, 13):
            month_start = date(year, m, 1)
            month_end = get_last_day(month_start)
            
            if doj and doj > month_end:
                continue
            if relieving and relieving < month_start:
                continue
            
            by_branch[key][f"month_{m}"] += emp["monthly_ctc"]
            by_branch[key]["ytd"] += emp["monthly_ctc"]
    
    rows = sorted(by_branch.values(), key=lambda x: (x["company"], x["branch"]))
    
    if rows:
        totals = {"company": "<b>TOTAL</b>", "branch": ""}
        for m in range(1, 13):
            totals[f"month_{m}"] = sum(r[f"month_{m}"] for r in rows)
        totals["ytd"] = sum(r["ytd"] for r in rows)
        rows.append(totals)
    
    return rows
