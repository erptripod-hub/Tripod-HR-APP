# Copyright (c) 2026, Tripod Mena
# CTC Budget Summary — Region -> Budget Unit -> Section.
# Region-aware columns: UAE shows Visa; KSA shows Iqama, GOSI, MOL Fee, Royalty Fee.
# Gratuity Provision (total accrued DOJ->today) shown as a column + summary card,
# but NOT included in Monthly CTC. Reads live from Employee master.

import frappe
from frappe import _

REGION_ORDER = {"UAE": 1, "KSA": 2}
UNIT_ORDER = {
    "Fit Out UAE": 1, "Dubai Production": 2, "Dubai Office": 3,
    "KSA Office": 4, "KSA National": 5, "KSA Production": 6, "KSA Fit Out": 7,
    "Logistics": 8, "Admin": 9, "Tap Gulf": 10,
}
UNIT_REGION = {
    "Fit Out UAE": "UAE", "Dubai Production": "UAE", "Dubai Office": "UAE",
    "KSA Office": "KSA", "KSA National": "KSA", "KSA Production": "KSA", "KSA Fit Out": "KSA",
    "Logistics": "KSA", "Admin": "KSA", "Tap Gulf": "KSA",
}

# which measure columns belong to which region ("both" always shown)
COL_REGION = {
    "visa": "UAE",
    "iqama": "KSA",
    "gosi": "KSA",
    "mol_fee": "KSA",
    "royalty_fee": "KSA",
}


def execute(filters=None):
    filters = filters or {}
    region = filters.get("region")
    columns = get_columns(region)
    data = get_data(filters)
    chart = get_chart(data)
    report_summary = get_report_summary(data)
    return columns, data, None, chart, report_summary


def _visible(fieldname, region):
    """A region-specific column is hidden when the other region is filtered."""
    col_region = COL_REGION.get(fieldname)
    if not col_region:
        return True
    if not region:
        return True          # region = All -> show everything
    return col_region == region


def get_columns(region=None):
    base = [
        {"label": _("Region"), "fieldname": "region", "fieldtype": "Data", "width": 90},
        {"label": _("Budget Unit"), "fieldname": "budget_unit", "fieldtype": "Data", "width": 150},
        {"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 150},
        {"label": _("HC"), "fieldname": "hc", "fieldtype": "Int", "width": 60},
        {"label": _("Monthly Salary"), "fieldname": "pay", "fieldtype": "Float", "width": 120, "precision": 0},
        {"label": _("Accommodation"), "fieldname": "accommodation", "fieldtype": "Float", "width": 110, "precision": 0},
        {"label": _("Visa"), "fieldname": "visa", "fieldtype": "Float", "width": 90, "precision": 0},
        {"label": _("Iqama"), "fieldname": "iqama", "fieldtype": "Float", "width": 90, "precision": 0},
        {"label": _("Medical"), "fieldname": "medical", "fieldtype": "Float", "width": 90, "precision": 0},
        {"label": _("Ticket"), "fieldname": "ticket", "fieldtype": "Float", "width": 90, "precision": 0},
        {"label": _("GOSI"), "fieldname": "gosi", "fieldtype": "Float", "width": 90, "precision": 0},
        {"label": _("MOL Fee"), "fieldname": "mol_fee", "fieldtype": "Float", "width": 90, "precision": 0},
        {"label": _("Royalty Fee"), "fieldname": "royalty_fee", "fieldtype": "Float", "width": 100, "precision": 0},
        {"label": _("Monthly CTC"), "fieldname": "monthly_ctc", "fieldtype": "Float", "width": 130, "precision": 0},
        {"label": _("Annual CTC"), "fieldname": "annual_ctc", "fieldtype": "Float", "width": 140, "precision": 0},
        {"label": _("Gratuity Provision"), "fieldname": "gratuity", "fieldtype": "Float", "width": 140, "precision": 0},
    ]
    return [c for c in base if _visible(c["fieldname"], region)]


MEASURES = ["hc", "pay", "accommodation", "visa", "iqama", "medical", "ticket",
            "gosi", "mol_fee", "royalty_fee", "monthly_ctc", "annual_ctc", "gratuity"]


def get_data(filters):
    conditions = ["e.status = 'Active'", "e.custom_budget_unit IS NOT NULL", "e.custom_budget_unit != ''"]
    values = {}
    if filters.get("region"):
        region_units = [u for u, r in UNIT_REGION.items() if r == filters["region"]]
        if region_units:
            placeholders = ", ".join("%(ru{0})s".format(i) for i in range(len(region_units)))
            conditions.append("e.custom_budget_unit IN ({0})".format(placeholders))
            for i, u in enumerate(region_units):
                values["ru{0}".format(i)] = u
    if filters.get("budget_unit"):
        conditions.append("e.custom_budget_unit = %(budget_unit)s")
        values["budget_unit"] = filters["budget_unit"]
    where = " AND ".join(conditions)

    rows = frappe.db.sql(
        """
        SELECT
            COALESCE(e.custom_region, '(none)')          AS region,
            COALESCE(e.custom_budget_unit, '(none)')     AS budget_unit,
            COALESCE(NULLIF(e.custom_sub_department,''), 'Unassigned')  AS section,
            COUNT(e.name)                                AS hc,
            SUM(COALESCE(e.custom_total_salary,0))       AS pay,
            SUM(COALESCE(e.custom_accommodation,0))      AS accommodation,
            SUM(COALESCE(e.custom_visa,0))               AS visa,
            SUM(COALESCE(e.custom_iqama,0))              AS iqama,
            SUM(COALESCE(e.custom_medical_insurance,0))  AS medical,
            SUM(COALESCE(e.custom_ticket_allowance,0))   AS ticket,
            SUM(COALESCE(e.custom_gosi,0))               AS gosi,
            SUM(COALESCE(e.custom_mol_fee,0))            AS mol_fee,
            SUM(COALESCE(e.custom_royalty_fee,0))        AS royalty_fee,
            SUM(COALESCE(e.custom_monthly_ctc,0))        AS monthly_ctc,
            SUM(COALESCE(e.custom_annual_ctc,0))         AS annual_ctc,
            SUM(COALESCE(e.custom_gratuity_monthly,0))   AS gratuity
        FROM `tabEmployee` e
        WHERE {where}
        GROUP BY e.custom_region, e.custom_budget_unit, e.custom_sub_department
        """.format(where=where),
        values, as_dict=True,
    )

    tree = {}
    for r in rows:
        reg = UNIT_REGION.get(r["budget_unit"], r.get("region") or "(none)")
        tree.setdefault(reg, {}).setdefault(r["budget_unit"], []).append(r)

    data = []
    grand = {m: 0 for m in MEASURES}

    for region in sorted(tree, key=lambda x: REGION_ORDER.get(x, 9)):
        region_tot = {m: 0 for m in MEASURES}
        region_block = []
        for unit in sorted(tree[region], key=lambda u: UNIT_ORDER.get(u, 9)):
            unit_tot = {m: 0 for m in MEASURES}
            sec_rows = []
            for r in sorted(tree[region][unit], key=lambda x: -x["hc"]):
                row = {"region": "", "budget_unit": "", "section": r["section"]}
                for m in MEASURES:
                    row[m] = r[m]
                    unit_tot[m] += r[m]
                sec_rows.append(row)
            unit_row = {"region": "", "budget_unit": unit, "section": "", "_bold": 1}
            for m in MEASURES:
                unit_row[m] = unit_tot[m]
                region_tot[m] += unit_tot[m]
            region_block.append(unit_row)
            region_block.extend(sec_rows)
        region_row = {"region": region, "budget_unit": "", "section": "", "_region": 1}
        for m in MEASURES:
            region_row[m] = region_tot[m]
            grand[m] += region_tot[m]
        data.append(region_row)
        data.extend(region_block)

    grand_row = {"region": "GRAND TOTAL", "budget_unit": "", "section": "", "_grand": 1}
    for m in MEASURES:
        grand_row[m] = grand[m]
    data.append(grand_row)
    return data


def get_chart(data):
    labels, ctc_vals = [], []
    for row in data:
        if row.get("_bold"):
            labels.append(row["budget_unit"])
            ctc_vals.append(row.get("monthly_ctc", 0))
    return {
        "type": "bar",
        "data": {"labels": labels, "datasets": [{"name": "Monthly CTC", "values": ctc_vals}]},
        "colors": ["#378ADD"],
    }


def get_report_summary(data):
    grand = next((r for r in data if r.get("_grand")), {})
    return [
        {"value": grand.get("hc", 0), "label": _("Headcount"), "datatype": "Int", "indicator": "Blue"},
        {"value": grand.get("pay", 0), "label": _("Monthly Salary"), "datatype": "Float", "indicator": "Blue"},
        {"value": grand.get("monthly_ctc", 0), "label": _("Monthly CTC"), "datatype": "Float", "indicator": "Green"},
        {"value": grand.get("annual_ctc", 0), "label": _("Annual CTC"), "datatype": "Float", "indicator": "Green"},
        {"value": grand.get("gratuity", 0), "label": _("Gratuity Provision"), "datatype": "Float", "indicator": "Orange"},
    ]
