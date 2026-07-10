# Copyright (c) 2026, Tripod HR
# Manpower Matrix — Department -> Section (rows) x Location state (columns).
# Tripod Media only. Mirrors the management pivot (Sheet4). No budget/cost.

import frappe
from frappe import _

LOCATIONS = [
    "DXB",
    "DXB - Logistics",
    "DXB Staff on Leave",
    "KSA (DXB Visa)",
    "Luxxe (TM Visa)",
    "Cancel",
    "Admin - Home/ Security",
]

LOC_KEY = {
    "DXB": "dxb",
    "DXB - Logistics": "dxb_logistics",
    "DXB Staff on Leave": "dxb_leave",
    "KSA (DXB Visa)": "ksa",
    "Luxxe (TM Visa)": "luxxe",
    "Cancel": "cancel",
    "Admin - Home/ Security": "admin_home",
}

DEPT_ORDER = {"ADMIN": 1, "Fitout - TM": 2, "Logistics - TM": 3, "Production  - TM": 4}


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    report_summary = get_report_summary(data)
    return columns, data, None, chart, report_summary


def get_columns():
    cols = [
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 150},
        {"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 170},
    ]
    for loc in LOCATIONS:
        cols.append({"label": _(loc), "fieldname": LOC_KEY[loc], "fieldtype": "Int", "width": 115})
    cols.append({"label": _("Unmapped"), "fieldname": "unmapped", "fieldtype": "Int", "width": 100})
    cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 90})
    return cols


def get_data(filters):
    company = filters.get("company") or "Tripod Media FZ LLC"

    rows = frappe.db.sql(
        """
        SELECT
            COALESCE(e.department, '(none)')             AS department,
            COALESCE(e.custom_sub_department, '(none)')  AS section,
            e.location                                   AS location,
            COUNT(e.name)                                AS cnt
        FROM `tabEmployee` e
        WHERE e.company = %(company)s
          AND e.status != 'Left'
        GROUP BY e.department, e.custom_sub_department, e.location
        """,
        {"company": company},
        as_dict=True,
    )

    # dept -> section -> {loc_key: count}
    tree = {}
    for r in rows:
        dept = r["department"]
        sec = r["section"]
        key = LOC_KEY.get(r["location"]) or "unmapped"
        tree.setdefault(dept, {}).setdefault(sec, {})
        tree[dept][sec][key] = tree[dept][sec].get(key, 0) + r["cnt"]

    col_keys = [LOC_KEY[l] for l in LOCATIONS] + ["unmapped"]
    data = []
    grand = {k: 0 for k in col_keys}
    grand_total = 0

    for dept in sorted(tree, key=lambda d: DEPT_ORDER.get(d, 9)):
        dept_tot = {k: 0 for k in col_keys}
        sec_rows = []
        for sec in sorted(tree[dept], key=lambda s: -sum(tree[dept][s].values())):
            row = {"department": "", "section": sec}
            st = 0
            for k in col_keys:
                v = tree[dept][sec].get(k, 0)
                row[k] = v
                dept_tot[k] += v
                st += v
            row["total"] = st
            sec_rows.append(row)

        # Department header row (bold, with its totals)
        dept_row = {"department": dept, "section": "", "_dept": 1}
        dt = 0
        for k in col_keys:
            dept_row[k] = dept_tot[k]
            grand[k] += dept_tot[k]
            dt += dept_tot[k]
        dept_row["total"] = dt
        grand_total += dt

        data.append(dept_row)
        data.extend(sec_rows)

    # Grand total row
    grand_row = {"department": "GRAND TOTAL", "section": "", "total": grand_total, "_grand": 1}
    for k in col_keys:
        grand_row[k] = grand[k]
    data.append(grand_row)

    return data


def get_chart(data):
    grand = next((r for r in data if r.get("_grand")), {})
    labels = ["Dubai", "Logistics", "On Leave", "KSA", "Luxxe", "Cancel", "Admin/Home"]
    values = [grand.get(LOC_KEY[l], 0) for l in LOCATIONS]
    return {
        "type": "bar",
        "data": {"labels": labels, "datasets": [{"name": "Headcount", "values": values}]},
        "colors": ["#378ADD", "#85B7EB", "#888780", "#1D9E75", "#534AB7", "#B4B2A9", "#888780"],
    }


def get_report_summary(data):
    grand = next((r for r in data if r.get("_grand")), {})
    dxb = grand.get("dxb", 0)
    return [
        {"value": grand.get("total", 0), "label": _("Total Manpower"), "datatype": "Int", "indicator": "Blue"},
        {"value": dxb, "label": _("In Dubai (DXB)"), "datatype": "Int", "indicator": "Blue"},
        {"value": grand.get("ksa", 0), "label": _("KSA (DXB Visa)"), "datatype": "Int", "indicator": "Green"},
        {"value": grand.get("luxxe", 0), "label": _("Luxxe (TM Visa)"), "datatype": "Int", "indicator": "Purple"},
        {"value": grand.get("dxb_leave", 0), "label": _("Staff on Leave"), "datatype": "Int", "indicator": "Orange"},
    ]
