import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data


def get_columns():
    return [
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 180},
        {"label": _("Total"), "fieldname": "headcount", "fieldtype": "Int", "width": 100},
        {"label": _("Hires 30d"), "fieldname": "hires_30d", "fieldtype": "Int", "width": 110},
        {"label": _("Exits 30d"), "fieldname": "exits_30d", "fieldtype": "Int", "width": 110},
        {"label": _("Net Change 30d"), "fieldname": "net_change", "fieldtype": "Int", "width": 130},
    ]


def get_data(filters):
    conditions = ["emp.status = 'Active'"]
    values = {}
    
    if filters.get("company"):
        conditions.append("emp.company = %(company)s")
        values["company"] = filters["company"]
    
    where_clause = " AND ".join(conditions)
    
    headcount_rows = frappe.db.sql(f"""
        SELECT
            emp.company AS company,
            emp.branch AS branch,
            COUNT(emp.name) AS headcount
        FROM `tabEmployee` emp
        WHERE {where_clause}
        GROUP BY emp.company, emp.branch
        ORDER BY emp.company, emp.branch
    """, values=values, as_dict=True)
    
    hires = frappe.db.sql("""
        SELECT branch, COUNT(name) AS cnt
        FROM `tabEmployee`
        WHERE date_of_joining >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY branch
    """, as_dict=True)
    hire_map = {h["branch"]: h["cnt"] for h in hires}
    
    exits = frappe.db.sql("""
        SELECT branch, COUNT(name) AS cnt
        FROM `tabEmployee`
        WHERE status = 'Left'
          AND relieving_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY branch
    """, as_dict=True)
    exit_map = {e["branch"]: e["cnt"] for e in exits}
    
    for row in headcount_rows:
        h = hire_map.get(row["branch"], 0)
        e = exit_map.get(row["branch"], 0)
        row["hires_30d"] = h
        row["exits_30d"] = e
        row["net_change"] = h - e
    
    if headcount_rows:
        headcount_rows.append({
            "company": "<b>TOTAL</b>",
            "branch": "",
            "headcount": sum(r["headcount"] for r in headcount_rows),
            "hires_30d": sum(r["hires_30d"] for r in headcount_rows),
            "exits_30d": sum(r["exits_30d"] for r in headcount_rows),
            "net_change": sum(r["net_change"] for r in headcount_rows),
        })
    
    return headcount_rows
