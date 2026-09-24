# Copyright (c) 2026, Tripod Mena
# Attendance Grid — employees as rows, days of the selected range as columns,
# each cell a short colored status code, plus per-employee summary totals.
# Reads standard Attendance records.

import frappe
from frappe import _
from frappe.utils import getdate, add_days, date_diff

# status code shown in each day cell (kept short so the grid stays compact)
CODE = {
    "Present": "P",
    "Absent": "A",
    "On Leave": "L",         # refined below by leave_type
    "Half Day": "\u00bd",    # ½
    "Work From Home": "P",
    "Holiday": "H",
}

# leave_type -> code (Annual / Sick get their own; anything else -> L)
LEAVE_CODE = {
    "Annual Leave": "AL",
    "Sick Leave": "SL",
}


def execute(filters=None):
    filters = filters or {}
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please set both From Date and To Date."))

    from_date = getdate(filters["from_date"])
    to_date = getdate(filters["to_date"])
    if date_diff(to_date, from_date) < 0:
        frappe.throw(_("To Date must be after From Date."))
    if date_diff(to_date, from_date) > 62:
        frappe.throw(_("Please keep the range within about two months for the day grid."))

    days = []
    d = from_date
    while d <= to_date:
        days.append(d)
        d = add_days(d, 1)

    rows = _fetch(filters, from_date, to_date)

    # employee -> {date_str: code}, plus name
    emp = {}
    for r in rows:
        e = emp.setdefault(r["employee"], {"name": r["employee_name"], "days": {}})
        e["days"][str(r["attendance_date"])] = _code(r)

    columns = _columns(days)
    data = _rows(emp, days)
    return columns, data


def _fetch(filters, from_date, to_date):
    conds = ["a.docstatus < 2", "a.attendance_date BETWEEN %(from_date)s AND %(to_date)s"]
    vals = {"from_date": from_date, "to_date": to_date}
    if filters.get("company"):
        conds.append("a.company = %(company)s")
        vals["company"] = filters["company"]
    if filters.get("employment_type"):
        conds.append("e.employment_type = %(employment_type)s")
        vals["employment_type"] = filters["employment_type"]
    if filters.get("employee"):
        conds.append("a.employee = %(employee)s")
        vals["employee"] = filters["employee"]
    where = " AND ".join(conds)

    return frappe.db.sql(
        """
        SELECT a.employee, a.employee_name, a.attendance_date, a.status, a.leave_type
        FROM `tabAttendance` a
        LEFT JOIN `tabEmployee` e ON e.name = a.employee
        WHERE {where}
        ORDER BY a.employee_name, a.attendance_date
        """.format(where=where),
        vals, as_dict=True,
    )


def _code(r):
    status = r.get("status")
    if status == "On Leave" or (status == "Half Day" and r.get("leave_type")):
        lt = r.get("leave_type")
        base = LEAVE_CODE.get(lt, "L")
        return "\u00bd" if status == "Half Day" else base
    return CODE.get(status, status or "")


def _columns(days):
    cols = [
        {"label": _("Employee"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
    ]
    for d in days:
        cols.append({
            "label": d.strftime("%d %a"),
            "fieldname": "d_" + d.strftime("%Y%m%d"),
            "fieldtype": "Data",
            "width": 62,
            "align": "center",
        })
    for key, label in [("t_present", "P"), ("t_absent", "A"),
                       ("t_al", "AL"), ("t_sl", "SL"),
                       ("t_worked", "Worked")]:
        cols.append({"label": _(label), "fieldname": key, "fieldtype": "Int", "width": 70})
    return cols


def _rows(emp, days):
    out = []
    for e_id in sorted(emp, key=lambda x: emp[x]["name"] or ""):
        info = emp[e_id]
        row = {"employee_name": info["name"]}
        p = a = al = sl = 0
        for d in days:
            code = info["days"].get(str(d), "")
            row["d_" + d.strftime("%Y%m%d")] = code
            if code == "P":
                p += 1
            elif code == "A":
                a += 1
            elif code == "AL":
                al += 1
            elif code == "SL":
                sl += 1
            elif code == "\u00bd":
                p += 0  # half day counted separately if needed
        row["t_present"] = p
        row["t_absent"] = a
        row["t_al"] = al
        row["t_sl"] = sl
        row["t_worked"] = p
        out.append(row)
    return out
