# Hiring Plan Summary — Section -> Designation, with head count,
# monthly salary, monthly CTC and annual CTC. Lets management filter by
# designation (or any other filter) and see how many people and what it costs.

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    data = get_data(filters)
    return get_columns(), data, None, None, get_summary(data)


def get_columns():
    return [
        {"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 180},
        {"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 220},
        {"label": _("Head Count"), "fieldname": "hc", "fieldtype": "Int", "width": 110},
        {"label": _("Monthly Salary"), "fieldname": "salary", "fieldtype": "Float", "width": 150, "precision": 0},
        {"label": _("Monthly CTC"), "fieldname": "ctc", "fieldtype": "Float", "width": 150, "precision": 0},
        {"label": _("Annual CTC"), "fieldname": "annual_ctc", "fieldtype": "Float", "width": 150, "precision": 0},
    ]


def get_data(filters):
    conds = []
    vals = {}

    for key, field in [
        ("company", "company"),
        ("budget_unit", "budget_unit"),
        ("region", "region"),
        ("section", "section"),
        ("designation", "designation"),
        ("planned_month", "planned_month"),
        ("status", "status"),
        ("hire_type", "hire_type"),
    ]:
        if filters.get(key):
            conds.append("`tabHiring Plan`.{0} = %({1})s".format(field, key))
            vals[key] = filters.get(key)

    where = (" WHERE " + " AND ".join(conds)) if conds else ""

    rows = frappe.db.sql(
        """
        SELECT
            COALESCE(NULLIF(`tabHiring Plan`.section, ''), '(none)')     AS section,
            COALESCE(NULLIF(`tabHiring Plan`.designation, ''), '(none)') AS designation,
            COUNT(*)                                                    AS hc,
            SUM(COALESCE(`tabHiring Plan`.monthly_salary, 0))           AS salary,
            SUM(COALESCE(`tabHiring Plan`.total_ctc, 0))                AS ctc
        FROM `tabHiring Plan`
        {where}
        GROUP BY section, designation
        ORDER BY section, designation
        """.format(where=where),
        vals,
        as_dict=True,
    )

    # group by section, add section subtotal rows, then a grand total
    tree = {}
    for r in rows:
        tree.setdefault(r["section"], []).append(r)

    data = []
    g_hc = g_sal = g_ctc = 0

    for section in sorted(tree):
        s_hc = s_sal = s_ctc = 0
        child_rows = []
        for r in tree[section]:
            child_rows.append({
                "section": "",
                "designation": r["designation"],
                "hc": int(r["hc"] or 0),
                "salary": round(r["salary"] or 0),
                "ctc": round(r["ctc"] or 0),
                "annual_ctc": round((r["ctc"] or 0) * 12),
                "indent": 1,
            })
            s_hc += r["hc"] or 0
            s_sal += r["salary"] or 0
            s_ctc += r["ctc"] or 0

        data.append({
            "section": section,
            "designation": "",
            "hc": int(s_hc),
            "salary": round(s_sal),
            "ctc": round(s_ctc),
            "annual_ctc": round(s_ctc * 12),
            "indent": 0,
            "is_group": 1,
        })
        data.extend(child_rows)

        g_hc += s_hc
        g_sal += s_sal
        g_ctc += s_ctc

    if data:
        data.append({
            "section": _("TOTAL"),
            "designation": "",
            "hc": int(g_hc),
            "salary": round(g_sal),
            "ctc": round(g_ctc),
            "annual_ctc": round(g_ctc * 12),
            "indent": 0,
            "is_group": 1,
        })

    return data


def get_summary(data):
    if not data:
        return []
    total = data[-1]
    return [
        {"value": total.get("hc", 0), "label": _("Planned Head Count"), "datatype": "Int", "indicator": "Blue"},
        {"value": total.get("salary", 0), "label": _("Monthly Salary"), "datatype": "Float", "indicator": "Blue"},
        {"value": total.get("ctc", 0), "label": _("Monthly CTC"), "datatype": "Float", "indicator": "Green"},
        {"value": total.get("annual_ctc", 0), "label": _("Annual CTC"), "datatype": "Float", "indicator": "Green"},
    ]
