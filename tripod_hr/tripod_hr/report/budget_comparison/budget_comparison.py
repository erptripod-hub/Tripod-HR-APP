# Copyright (c) 2026, Tripod Mena
# Budget Comparison — month over month, per Budget Unit.
# The CTC movement is broken into its three real causes so the number is
# explainable rather than a single lump:
#     Cost In      = CTC of people present in TO month but not in FROM month
#     Cost Out     = CTC of people present in FROM month but not in TO month
#     Existing Δ   = salary/CTC change of people present in BOTH months
#     Net Δ        = Cost In - Cost Out + Existing Δ   (== CTC To - CTC From)
# A unit change counts as a leaver from the old unit and a joiner to the new one.

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    from_month = filters.get("from_month")
    to_month = filters.get("to_month")
    if not from_month or not to_month:
        return get_columns(), [], _("Select both From Month and To Month (snapshots must exist)."), None, None

    data = get_data(from_month, to_month)
    return get_columns(), data, None, None, get_report_summary(data)


def get_columns():
    return [
        {"label": _("Budget Unit"), "fieldname": "budget_unit", "fieldtype": "Data", "width": 150},
        {"label": _("HC (From)"), "fieldname": "hc_from", "fieldtype": "Int", "width": 85},
        {"label": _("HC (To)"), "fieldname": "hc_to", "fieldtype": "Int", "width": 80},
        {"label": _("HC \u0394"), "fieldname": "hc_delta", "fieldtype": "Int", "width": 65},
        {"label": _("New Hire"), "fieldname": "joiners", "fieldtype": "Int", "width": 85},
        {"label": _("Cost In"), "fieldname": "cost_in", "fieldtype": "Float", "width": 110, "precision": 0},
        {"label": _("Removed"), "fieldname": "leavers", "fieldtype": "Int", "width": 85},
        {"label": _("Cost Out"), "fieldname": "cost_out", "fieldtype": "Float", "width": 110, "precision": 0},
        {"label": _("Existing \u0394"), "fieldname": "existing_delta", "fieldtype": "Float", "width": 110, "precision": 0},
        {"label": _("CTC (From)"), "fieldname": "ctc_from", "fieldtype": "Float", "width": 115, "precision": 0},
        {"label": _("CTC (To)"), "fieldname": "ctc_to", "fieldtype": "Float", "width": 115, "precision": 0},
        {"label": _("Net \u0394"), "fieldname": "ctc_delta", "fieldtype": "Float", "width": 110, "precision": 0},
        {"label": _("Net \u0394 %"), "fieldname": "ctc_pct", "fieldtype": "Percent", "width": 85},
        {"label": _("Effect"), "fieldname": "effect", "fieldtype": "Data", "width": 100},
    ]


def _effect_label(delta):
    """Budget reading: spending less than the previous month is a SAVING."""
    if delta < 0:
        return _("Saved")
    if delta > 0:
        return _("Extra cost")
    return _("No change")


def _load(month):
    rows = frappe.db.sql(
        """SELECT employee, budget_unit, monthly_ctc
           FROM `tabHR Budget Snapshot` WHERE snapshot_month=%s""",
        month, as_dict=True)
    return {r.employee: r for r in rows}


def _blank():
    return dict(hc_from=0, hc_to=0, joiners=0, leavers=0,
                cost_in=0.0, cost_out=0.0, existing_delta=0.0,
                ctc_from=0.0, ctc_to=0.0)


def get_data(from_month, to_month):
    a = _load(from_month)
    b = _load(to_month)
    units = {}

    def bucket(unit):
        return units.setdefault(unit or "(none)", _blank())

    # FROM side — headcount and cost as they stood
    for emp, r in a.items():
        d = bucket(r.budget_unit)
        d["hc_from"] += 1
        d["ctc_from"] += r.monthly_ctc or 0

    # TO side — headcount and cost as they stand now
    for emp, r in b.items():
        d = bucket(r.budget_unit)
        d["hc_to"] += 1
        d["ctc_to"] += r.monthly_ctc or 0

    # Attribute the movement
    for emp, r in b.items():
        if emp not in a:                                   # new hire into this unit
            d = bucket(r.budget_unit)
            d["joiners"] += 1
            d["cost_in"] += r.monthly_ctc or 0
        elif a[emp].budget_unit != r.budget_unit:          # moved between units
            d_new = bucket(r.budget_unit)
            d_new["joiners"] += 1
            d_new["cost_in"] += r.monthly_ctc or 0
            d_old = bucket(a[emp].budget_unit)
            d_old["leavers"] += 1
            d_old["cost_out"] += a[emp].monthly_ctc or 0
        else:                                              # stayed put — pay change only
            d = bucket(r.budget_unit)
            d["existing_delta"] += (r.monthly_ctc or 0) - (a[emp].monthly_ctc or 0)

    for emp, r in a.items():
        if emp not in b:                                   # left the company
            d = bucket(r.budget_unit)
            d["leavers"] += 1
            d["cost_out"] += r.monthly_ctc or 0

    data = []
    tot = _blank()
    for unit in sorted(units):
        d = units[unit]
        delta = d["ctc_to"] - d["ctc_from"]
        pct = (delta / d["ctc_from"] * 100) if d["ctc_from"] else 0
        row = {"budget_unit": unit, "hc_delta": d["hc_to"] - d["hc_from"],
               "ctc_delta": delta, "ctc_pct": pct, "effect": _effect_label(delta)}
        row.update({k: d[k] for k in d})
        data.append(row)
        for k in tot:
            tot[k] += d[k]

    grand_delta = tot["ctc_to"] - tot["ctc_from"]
    grand_pct = (grand_delta / tot["ctc_from"] * 100) if tot["ctc_from"] else 0
    grand = {"budget_unit": _("GRAND TOTAL"), "hc_delta": tot["hc_to"] - tot["hc_from"],
             "ctc_delta": grand_delta, "ctc_pct": grand_pct,
             "effect": _effect_label(grand_delta), "_grand": 1}
    grand.update({k: tot[k] for k in tot})
    data.append(grand)
    return data


def get_report_summary(data):
    g = next((r for r in data if r.get("_grand")), {})
    delta = g.get("ctc_delta", 0)
    return [
        {"value": g.get("hc_delta", 0), "label": _("Headcount \u0394"), "datatype": "Int", "indicator": "Blue"},
        {"value": g.get("joiners", 0), "label": _("New Hires"), "datatype": "Int", "indicator": "Green"},
        {"value": g.get("leavers", 0), "label": _("Removed"), "datatype": "Int", "indicator": "Orange"},
        {"value": abs(delta), "label": _("Saved") if delta < 0 else _("Extra Cost"),
         "datatype": "Float", "indicator": "Green" if delta < 0 else "Red"},
    ]
