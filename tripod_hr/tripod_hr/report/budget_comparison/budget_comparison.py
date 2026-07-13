# Copyright (c) 2026, Tripod Mena
# Budget Comparison — month over month. Shows per Budget Unit:
# headcount change, CTC change, plus joiners / leavers between two snapshot months.

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    from_month = filters.get("from_month")
    to_month = filters.get("to_month")
    if not from_month or not to_month:
        return get_columns(), [], _("Select both From Month and To Month (snapshots must exist)."), None, None

    columns = get_columns()
    data = get_data(from_month, to_month)
    return columns, data


def get_columns():
    return [
        {"label": _("Budget Unit"), "fieldname": "budget_unit", "fieldtype": "Data", "width": 160},
        {"label": _("HC (From)"), "fieldname": "hc_from", "fieldtype": "Int", "width": 90},
        {"label": _("HC (To)"), "fieldname": "hc_to", "fieldtype": "Int", "width": 90},
        {"label": _("HC Δ"), "fieldname": "hc_delta", "fieldtype": "Int", "width": 70},
        {"label": _("Joiners"), "fieldname": "joiners", "fieldtype": "Int", "width": 80},
        {"label": _("Leavers"), "fieldname": "leavers", "fieldtype": "Int", "width": 80},
        {"label": _("CTC (From)"), "fieldname": "ctc_from", "fieldtype": "Float", "width": 120, "precision": 0},
        {"label": _("CTC (To)"), "fieldname": "ctc_to", "fieldtype": "Float", "width": 120, "precision": 0},
        {"label": _("CTC Δ"), "fieldname": "ctc_delta", "fieldtype": "Float", "width": 120, "precision": 0},
        {"label": _("CTC Δ %"), "fieldname": "ctc_pct", "fieldtype": "Percent", "width": 90},
    ]


def _load(month):
    rows = frappe.db.sql(
        """SELECT employee, budget_unit, monthly_ctc
           FROM `tabHR Budget Snapshot` WHERE snapshot_month=%s""",
        month, as_dict=True)
    by_emp = {r.employee: r for r in rows}
    return by_emp


def get_data(from_month, to_month):
    a = _load(from_month)   # from
    b = _load(to_month)     # to
    units = {}

    def unit(rec):
        return rec.budget_unit or "(none)"

    # From side
    for emp, r in a.items():
        u = unit(r)
        d = units.setdefault(u, dict(hc_from=0, hc_to=0, joiners=0, leavers=0, ctc_from=0, ctc_to=0))
        d["hc_from"] += 1
        d["ctc_from"] += r.monthly_ctc or 0
    # To side
    for emp, r in b.items():
        u = unit(r)
        d = units.setdefault(u, dict(hc_from=0, hc_to=0, joiners=0, leavers=0, ctc_from=0, ctc_to=0))
        d["hc_to"] += 1
        d["ctc_to"] += r.monthly_ctc or 0
    # Joiners (in b not a) / Leavers (in a not b)
    for emp, r in b.items():
        if emp not in a:
            units[unit(r)]["joiners"] += 1
    for emp, r in a.items():
        if emp not in b:
            units[unit(r)]["leavers"] += 1

    data = []
    tot = dict(hc_from=0, hc_to=0, joiners=0, leavers=0, ctc_from=0, ctc_to=0)
    for u in sorted(units):
        d = units[u]
        hc_delta = d["hc_to"] - d["hc_from"]
        ctc_delta = d["ctc_to"] - d["ctc_from"]
        pct = (ctc_delta / d["ctc_from"] * 100) if d["ctc_from"] else 0
        data.append({
            "budget_unit": u, "hc_from": d["hc_from"], "hc_to": d["hc_to"], "hc_delta": hc_delta,
            "joiners": d["joiners"], "leavers": d["leavers"],
            "ctc_from": d["ctc_from"], "ctc_to": d["ctc_to"], "ctc_delta": ctc_delta, "ctc_pct": pct,
        })
        for k in tot:
            tot[k] += d[k]

    grand_delta = tot["ctc_to"] - tot["ctc_from"]
    grand_pct = (grand_delta / tot["ctc_from"] * 100) if tot["ctc_from"] else 0
    data.append({
        "budget_unit": "GRAND TOTAL", "hc_from": tot["hc_from"], "hc_to": tot["hc_to"],
        "hc_delta": tot["hc_to"] - tot["hc_from"], "joiners": tot["joiners"], "leavers": tot["leavers"],
        "ctc_from": tot["ctc_from"], "ctc_to": tot["ctc_to"], "ctc_delta": grand_delta, "ctc_pct": grand_pct,
        "_grand": 1,
    })
    return data
