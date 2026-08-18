# Copyright (c) 2026, Tripod HR
# Manpower Matrix — Department -> Section (rows) x Location state (columns).
# Company aware: Tripod Media labour is spread across UAE visa locations, while
# Tripod Global labour all sits in KSA, so each company gets its own column set.

import frappe
from frappe import _

TM_COMPANY = "Tripod Media FZ LLC"
TG_COMPANY = "TRIPOD GLOBAL SHOPFIT MANUFACTURING COMPANY"
LAMEF_COMPANY = "Luxxe Atelier Middle East FZ-LLC"

TM_CONFIG = {
    "locations": [
        "DXB",
        "DXB - Logistics",
        "DXB Staff on Leave",
        "KSA (DXB Visa)",
        "Luxxe (TM Visa)",
        "Cancel",
        "Admin - Home/ Security",
    ],
    "keys": {
        "DXB": "dxb",
        "DXB - Logistics": "dxb_logistics",
        "DXB Staff on Leave": "dxb_leave",
        "KSA (DXB Visa)": "ksa",
        "Luxxe (TM Visa)": "luxxe",
        "Cancel": "cancel",
        "Admin - Home/ Security": "admin_home",
    },
    "dept_order": {"ADMIN": 1, "Fitout - TM": 2, "Logistics - TM": 3, "Production  - TM": 4},
    "chart_labels": ["Dubai", "Logistics", "On Leave", "KSA", "Luxxe", "Cancel", "Admin/Home"],
    "chart_colors": ["#378ADD", "#85B7EB", "#888780", "#1D9E75", "#534AB7", "#B4B2A9", "#888780"],
    "summary": [
        ("total", "Total Manpower", "Blue"),
        ("dxb", "In Dubai (DXB)", "Blue"),
        ("ksa", "KSA (DXB Visa)", "Green"),
        ("luxxe", "Luxxe (TM Visa)", "Purple"),
        ("dxb_leave", "Staff on Leave", "Orange"),
    ],
}

TG_CONFIG = {
    "locations": [
        "KSA",
        "KSA Staff on Leave",
        "Cancel",
    ],
    "keys": {
        "KSA": "ksa_loc",
        "KSA Staff on Leave": "ksa_leave",
        "Cancel": "cancel",
    },
    "dept_order": {
        "Admin - TDMFCL": 1,
        "Fitout - TDMFCL": 2,
        "Logistics - TDMFCL": 3,
        "Production-Team  - TDMFCL": 4,
    },
    "chart_labels": ["In KSA", "On Leave", "Cancel"],
    "chart_colors": ["#1D9E75", "#888780", "#B4B2A9"],
    "summary": [
        ("total", "Total Manpower", "Blue"),
        ("ksa_loc", "In KSA", "Green"),
        ("ksa_leave", "Staff on Leave", "Orange"),
    ],
}


LAMEF_CONFIG = {
    "locations": [
        "Luxxe Warehouse",
        "Luxxe - Logistics",
        "Luxxe Staff on Leave",
        "Luxxe (TM Visa)",
        "Cancel",
        "Admin - Home/ Security",
    ],
    "keys": {
        "Luxxe Warehouse": "warehouse",
        "Luxxe - Logistics": "logistics",
        "Luxxe Staff on Leave": "on_leave",
        "Luxxe (TM Visa)": "tm_visa",
        "Cancel": "cancel",
        "Admin - Home/ Security": "admin_home",
    },
    "dept_order": {
        "Management - LAMEF": 1,
        "Operations - LAMEF": 2,
        "Design - LAMEF": 3,
        "Projects - LAMEF": 4,
        "Purchase - LAMEF": 5,
        "Logistics - LAMEF": 6,
        "Production - LAMEF": 7,
    },
    "chart_labels": ["Warehouse", "Logistics", "On Leave", "TM Visa", "Cancel", "Admin/Home"],
    "chart_colors": ["#378ADD", "#85B7EB", "#888780", "#534AB7", "#B4B2A9", "#888780"],
    "summary": [
        ("total", "Total Manpower", "Blue"),
        ("warehouse", "In Warehouse", "Blue"),
        ("logistics", "Logistics", "Green"),
        ("on_leave", "Staff on Leave", "Orange"),
    ],
}


def get_config(company):
    if company == TG_COMPANY:
        return TG_CONFIG
    if company == LAMEF_COMPANY:
        return LAMEF_CONFIG
    return TM_CONFIG


def execute(filters=None):
    filters = filters or {}
    company = filters.get("company") or TM_COMPANY
    cfg = get_config(company)

    data = get_data(company, cfg, filters.get("employment_type"))
    return get_columns(cfg), data, None, get_chart(data, cfg), get_report_summary(data, cfg)


def get_columns(cfg):
    cols = [
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 190},
        {"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 180},
    ]
    for loc in cfg["locations"]:
        cols.append({"label": _(loc), "fieldname": cfg["keys"][loc], "fieldtype": "Int", "width": 130})
    cols.append({"label": _("Unmapped"), "fieldname": "unmapped", "fieldtype": "Int", "width": 100})
    cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 90})
    return cols


def get_data(company, cfg, employment_type=None):
    conditions = ""
    values = {"company": company}

    if employment_type and employment_type != "All":
        conditions = "AND e.employment_type = %(employment_type)s"
        values["employment_type"] = employment_type
    elif not employment_type:
        conditions = "AND e.employment_type = 'Labour'"

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
          {conditions}
        GROUP BY e.department, e.custom_sub_department, e.location
        """.format(conditions=conditions),
        values,
        as_dict=True,
    )

    keys = cfg["keys"]
    dept_order = cfg["dept_order"]

    # dept -> section -> {loc_key: count}
    tree = {}
    for r in rows:
        dept = r["department"]
        sec = r["section"]
        key = keys.get(r["location"]) or "unmapped"
        tree.setdefault(dept, {}).setdefault(sec, {})
        tree[dept][sec][key] = tree[dept][sec].get(key, 0) + r["cnt"]

    col_keys = [keys[l] for l in cfg["locations"]] + ["unmapped"]
    data = []
    grand = {k: 0 for k in col_keys}
    grand_total = 0

    for dept in sorted(tree, key=lambda d: dept_order.get(d, 9)):
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

    grand_row = {"department": "GRAND TOTAL", "section": "", "total": grand_total, "_grand": 1}
    for k in col_keys:
        grand_row[k] = grand[k]
    data.append(grand_row)

    return data


def get_chart(data, cfg):
    grand = next((r for r in data if r.get("_grand")), {})
    values = [grand.get(cfg["keys"][l], 0) for l in cfg["locations"]]
    return {
        "type": "bar",
        "data": {"labels": cfg["chart_labels"], "datasets": [{"name": "Headcount", "values": values}]},
        "colors": cfg["chart_colors"],
    }


def get_report_summary(data, cfg):
    grand = next((r for r in data if r.get("_grand")), {})
    return [
        {"value": grand.get(key, 0), "label": _(label), "datatype": "Int", "indicator": colour}
        for key, label, colour in cfg["summary"]
    ]
