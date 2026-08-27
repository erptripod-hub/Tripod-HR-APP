# Copyright (c) 2026, Tripod Mena
# Budget Movement Detail — the names behind the Budget Comparison numbers.
# Lists every New Hire, Removed and Pay Change between two snapshot months.

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    fm, tm = filters.get("from_month"), filters.get("to_month")
    if not fm or not tm:
        return get_columns(), [], _("Select both From Month and To Month."), None, None
    return get_columns(), get_data(fm, tm, filters)


def get_columns():
    return [
        {"label": _("Movement"), "fieldname": "movement", "fieldtype": "Data", "width": 110},
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
        {"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 190},
        {"label": _("Budget Unit"), "fieldname": "budget_unit", "fieldtype": "Data", "width": 150},
        {"label": _("From Unit"), "fieldname": "from_unit", "fieldtype": "Data", "width": 150},
        {"label": _("CTC (From)"), "fieldname": "ctc_from", "fieldtype": "Float", "width": 115, "precision": 0},
        {"label": _("CTC (To)"), "fieldname": "ctc_to", "fieldtype": "Float", "width": 115, "precision": 0},
        {"label": _("Impact"), "fieldname": "impact", "fieldtype": "Float", "width": 115, "precision": 0},
    ]


def _load(month):
    rows = frappe.db.sql(
        """SELECT employee, employee_name, budget_unit, monthly_ctc
           FROM `tabHR Budget Snapshot` WHERE snapshot_month=%s""",
        month, as_dict=True)
    return {r.employee: r for r in rows}


def get_data(from_month, to_month, filters):
    a, b = _load(from_month), _load(to_month)
    unit_filter = filters.get("budget_unit")
    show = filters.get("movement")
    out = []

    for emp, r in b.items():
        prev = a.get(emp)
        if not prev:
            out.append({"movement": _("New Hire"), "employee": emp, "employee_name": r.employee_name,
                        "budget_unit": r.budget_unit, "from_unit": "",
                        "ctc_from": 0, "ctc_to": r.monthly_ctc or 0, "impact": r.monthly_ctc or 0})
        elif prev.budget_unit != r.budget_unit:
            out.append({"movement": _("Moved In"), "employee": emp, "employee_name": r.employee_name,
                        "budget_unit": r.budget_unit, "from_unit": prev.budget_unit,
                        "ctc_from": 0, "ctc_to": r.monthly_ctc or 0, "impact": r.monthly_ctc or 0})
            out.append({"movement": _("Moved Out"), "employee": emp, "employee_name": prev.employee_name,
                        "budget_unit": prev.budget_unit, "from_unit": "",
                        "ctc_from": prev.monthly_ctc or 0, "ctc_to": 0, "impact": -(prev.monthly_ctc or 0)})
        else:
            diff = (r.monthly_ctc or 0) - (prev.monthly_ctc or 0)
            if abs(diff) > 0.5:
                out.append({"movement": _("Pay Change"), "employee": emp, "employee_name": r.employee_name,
                            "budget_unit": r.budget_unit, "from_unit": "",
                            "ctc_from": prev.monthly_ctc or 0, "ctc_to": r.monthly_ctc or 0, "impact": diff})

    for emp, r in a.items():
        if emp not in b:
            out.append({"movement": _("Removed"), "employee": emp, "employee_name": r.employee_name,
                        "budget_unit": r.budget_unit, "from_unit": "",
                        "ctc_from": r.monthly_ctc or 0, "ctc_to": 0, "impact": -(r.monthly_ctc or 0)})

    if unit_filter:
        out = [r for r in out if r["budget_unit"] == unit_filter]
    if show:
        out = [r for r in out if r["movement"] == show]

    order = {_("New Hire"): 1, _("Moved In"): 2, _("Moved Out"): 3, _("Removed"): 4, _("Pay Change"): 5}
    out.sort(key=lambda r: (r["budget_unit"] or "", order.get(r["movement"], 9), -abs(r["impact"])))
    return out
