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
    "Tap Gulf": "KSA",
}

BOTH_REGION_UNITS = ["Logistics", "Admin"]

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
        {"label": _("Gratuity Provision Till Date"), "fieldname": "gratuity", "fieldtype": "Float", "width": 170, "precision": 0},
    ]
    return [c for c in base if _visible(c["fieldname"], region)]


MEASURES = ["hc", "pay", "accommodation", "visa", "iqama", "medical", "ticket",
            "gosi", "mol_fee", "royalty_fee", "monthly_ctc", "annual_ctc", "gratuity"]


def get_data(filters):
    conditions = ["e.status = 'Active'", "e.custom_budget_unit IS NOT NULL", "e.custom_budget_unit != ''"]
    values = {}
    if filters.get("region"):
        # units that belong to this region by name, PLUS the both-region units
        # (Logistics / Admin) which are resolved by the employee's own region.
        region_units = [u for u, r in UNIT_REGION.items() if r == filters["region"]]
        region_units += BOTH_REGION_UNITS
        placeholders = ", ".join("%(ru{0})s".format(i) for i in range(len(region_units)))
        conditions.append(
            "(e.custom_budget_unit IN ({0}) AND "
            " (e.custom_budget_unit NOT IN %(both)s OR e.custom_region = %(region)s))".format(placeholders)
        )
        for i, u in enumerate(region_units):
            values["ru{0}".format(i)] = u
        values["both"] = tuple(BOTH_REGION_UNITS)
        values["region"] = filters["region"]
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

    rows = _merge_split_deltas(rows, _get_split_deltas(filters))

    tree = {}
    for r in rows:
        reg = UNIT_REGION.get(r["budget_unit"]) or (r.get("region") or "(none)")
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


# ---------------------------------------------------------------- cost splits
# Two kinds of split, both COST ONLY (headcount always stays whole, on the
# employee's current unit):
#   1. Mid-month transfer  -> cost apportioned by days across the units held
#                             during the month (Employee Transfer Log).
#   2. Fixed % split       -> custom_cost_split_pct of MONTHLY SALARY moved to
#                             custom_cost_split_unit (e.g. CEO 50/50).
# The base SQL puts 100% of every employee on their CURRENT unit, so a split is
# expressed as a set of deltas that move value off the current unit.

SPLIT_MEASURES = ["pay", "accommodation", "visa", "iqama", "medical", "ticket",
                  "gosi", "mol_fee", "royalty_fee", "monthly_ctc", "annual_ctc", "gratuity"]


def _month_bounds(ref=None):
    from frappe.utils import getdate, get_first_day, get_last_day, nowdate
    ref = getdate(ref or nowdate())
    return get_first_day(ref), get_last_day(ref)


def _transfer_segments(emp_rows, first_day, last_day):
    """Return [(budget_unit, days), ...] for the month, from the transfer log."""
    from frappe.utils import getdate, date_diff
    rows = [r for r in emp_rows if r.get("transfer_date")]
    rows = [r for r in rows if first_day <= getdate(r["transfer_date"]) <= last_day]
    if not rows:
        return []
    rows.sort(key=lambda r: getdate(r["transfer_date"]))

    # The transfer DATE itself counts to the OLD unit: a transfer on the 10th
    # means days 1-10 sit with the old unit and day 11 onward with the new one.
    segments = []
    cursor = first_day
    for r in rows:
        tdate = getdate(r["transfer_date"])
        days = date_diff(tdate, cursor) + 1
        if days > 0 and r.get("from_budget_unit"):
            segments.append((r["from_budget_unit"], days))
        cursor = frappe.utils.add_days(tdate, 1)
    tail = date_diff(last_day, cursor) + 1
    if tail > 0 and rows[-1].get("to_budget_unit"):
        segments.append((rows[-1]["to_budget_unit"], tail))
    return segments


def _get_split_deltas(filters):
    """Build {(region, unit, section): {measure: delta}} for all split employees."""
    from frappe.utils import date_diff
    first_day, last_day = _month_bounds()
    total_days = date_diff(last_day, first_day) + 1

    emps = frappe.db.sql(
        """
        SELECT e.name, e.custom_region AS region,
               e.custom_budget_unit AS unit,
               COALESCE(NULLIF(e.custom_sub_department,''),'Unassigned') AS section,
               COALESCE(e.custom_total_salary,0)      AS pay,
               COALESCE(e.custom_accommodation,0)     AS accommodation,
               COALESCE(e.custom_visa,0)              AS visa,
               COALESCE(e.custom_iqama,0)             AS iqama,
               COALESCE(e.custom_medical_insurance,0) AS medical,
               COALESCE(e.custom_ticket_allowance,0)  AS ticket,
               COALESCE(e.custom_gosi,0)              AS gosi,
               COALESCE(e.custom_mol_fee,0)           AS mol_fee,
               COALESCE(e.custom_royalty_fee,0)       AS royalty_fee,
               COALESCE(e.custom_monthly_ctc,0)       AS monthly_ctc,
               COALESCE(e.custom_annual_ctc,0)        AS annual_ctc,
               COALESCE(e.custom_gratuity_monthly,0)  AS gratuity,
               COALESCE(e.custom_cost_split_pct,0)    AS split_pct,
               e.custom_cost_split_unit               AS split_unit
        FROM `tabEmployee` e
        WHERE e.status='Active'
          AND e.custom_budget_unit IS NOT NULL AND e.custom_budget_unit != ''
          AND (
                COALESCE(e.custom_cost_split_pct,0) > 0
                OR EXISTS (SELECT 1 FROM `tabEmployee Transfer Log` t
                           WHERE t.parent = e.name
                             AND t.transfer_date BETWEEN %(fd)s AND %(ld)s)
              )
        """,
        {"fd": first_day, "ld": last_day}, as_dict=True,
    )
    if not emps:
        return {}

    logs = {}
    for t in frappe.db.sql(
        """SELECT parent, from_budget_unit, to_budget_unit, transfer_date
           FROM `tabEmployee Transfer Log` WHERE parent IN %(names)s""",
        {"names": tuple(e["name"] for e in emps)}, as_dict=True):
        logs.setdefault(t["parent"], []).append(t)

    deltas = {}

    def add(region, unit, section, measure, amount):
        if not unit or not amount:
            return
        key = (region or "(none)", unit, section)
        deltas.setdefault(key, {})
        deltas[key][measure] = deltas[key].get(measure, 0) + amount

    for e in emps:
        cur_unit, region, section = e["unit"], e["region"], e["section"]

        # 1. mid-month transfer -> apportion EVERY measure by days
        segments = _transfer_segments(logs.get(e["name"], []), first_day, last_day)
        if segments and total_days:
            for seg_unit, days in segments:
                if seg_unit == cur_unit:
                    continue
                w = float(days) / float(total_days)
                for m in SPLIT_MEASURES:
                    amt = round((e.get(m) or 0) * w, 2)
                    if amt:
                        add(region, seg_unit, section, m, amt)      # to the held unit
                        add(region, cur_unit, section, m, -amt)     # off the current unit

        # 2. fixed % split -> MONTHLY SALARY only (also shifts the CTC it sits in)
        pct = float(e.get("split_pct") or 0)
        if pct > 0 and e.get("split_unit") and e["split_unit"] != cur_unit:
            share = pct / 100.0
            salary_share = round((e.get("pay") or 0) * share, 2)
            if salary_share:
                add(region, e["split_unit"], section, "pay", salary_share)
                add(region, cur_unit, section, "pay", -salary_share)
                add(region, e["split_unit"], section, "monthly_ctc", salary_share)
                add(region, cur_unit, section, "monthly_ctc", -salary_share)
                add(region, e["split_unit"], section, "annual_ctc", round(salary_share * 12, 2))
                add(region, cur_unit, section, "annual_ctc", round(-salary_share * 12, 2))

    return deltas


def _merge_split_deltas(rows, deltas):
    """Apply deltas onto the aggregated rows, creating rows for new units."""
    if not deltas:
        return rows
    index = {(r.get("region"), r["budget_unit"], r["section"]): r for r in rows}
    for (region, unit, section), measures in deltas.items():
        target = index.get((region, unit, section))
        if not target:
            target = {"region": region, "budget_unit": unit, "section": section, "hc": 0}
            for m in MEASURES:
                target.setdefault(m, 0)
            rows.append(target)
            index[(region, unit, section)] = target
        for m, amt in measures.items():
            target[m] = (target.get(m) or 0) + amt
    return rows


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
        {"value": grand.get("gratuity", 0), "label": _("Gratuity Provision Till Date"), "datatype": "Float", "indicator": "Orange"},
    ]
