import frappe

REGION_ORDER = {"UAE": 1, "KSA": 2, "": 9}
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
OWNERS = ["TM-EMP-0021", "TM-EMP-0022"]        # excluded from budget entirely
CEO = "TGK-EMP-0284"                            # cost split across two offices
CEO_DUBAI_SHARE = 0.40                          # 40% Dubai Office, 60% stays KSA Office

CEO_ALLOC_LABEL = "CEO cost allocation (40%)"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONTHS = ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]
MONTH_LBL = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@frappe.whitelist()
def get_budget_dashboard(company=None):
    company = company or None
    active = _active(company)
    plan = _plan(company)
    ramp = _ramp(company, active["current_salary"])
    designations = _designations(company)
    movement = _movement(company, active["current_ctc"])
    return {
        "active": active,
        "plan": plan,
        "ramp": ramp,
        "designations": designations,
        "movement": movement,
    }


def _cond(company, alias=""):
    p = (alias + ".") if alias else ""
    cond = f"{p}status = 'Active'"
    vals = {}
    if company:
        cond += f" AND {p}company = %(company)s"
        vals["company"] = company
    return cond, vals


def _active(company):
    cond, vals = _cond(company)
    rows = frappe.db.sql(
        f"""
        SELECT
            COALESCE(NULLIF(custom_budget_unit, ''), '(untagged)') AS unit,
            COALESCE(custom_region, '')                            AS region,
            COUNT(*)                                               AS hc,
            SUM(COALESCE(custom_total_salary, 0))                  AS salary,
            SUM(COALESCE(custom_monthly_ctc, 0))                   AS ctc,
            SUM(COALESCE(custom_annual_ctc, 0))                    AS ctc_yr
        FROM `tabEmployee`
        WHERE {cond}
          AND name NOT IN %(owners)s
        GROUP BY unit, region
        """,
        dict(vals, owners=tuple(OWNERS)), as_dict=True,
    )

    by_unit = {}
    untagged = {"hc": 0, "salary": 0, "ctc": 0, "ctc_yr": 0}
    for r in rows:
        if r["unit"] == "(untagged)":
            for k in untagged:
                untagged[k] += r[k] or 0
            continue
        u = by_unit.setdefault(r["unit"], {"hc": 0, "salary": 0, "ctc": 0, "ctc_yr": 0})
        for k in u:
            u[k] += r[k] or 0

    if not company:
        ceo = frappe.db.get_value(
            "Employee", CEO,
            ["custom_budget_unit", "custom_total_salary", "custom_monthly_ctc", "custom_annual_ctc"],
            as_dict=True,
        )
        if ceo and ceo.custom_budget_unit in by_unit:
            share = CEO_DUBAI_SHARE
            home = by_unit[ceo.custom_budget_unit]
            dubai = by_unit.setdefault("Dubai Office", {"hc": 0, "salary": 0, "ctc": 0, "ctc_yr": 0})
            for fld, key in [("custom_total_salary", "salary"),
                             ("custom_monthly_ctc", "ctc"),
                             ("custom_annual_ctc", "ctc_yr")]:
                amt = (ceo.get(fld) or 0) * share
                home[key] -= amt
                dubai[key] += amt
            # headcount stays in CEO's home unit; only cost is split

    regions = {}
    for unit, m in by_unit.items():
        reg = UNIT_REGION.get(unit, "")
        regions.setdefault(reg, []).append((unit, m))

    out = []
    grand = {"hc": 0, "salary": 0, "ctc": 0, "ctc_yr": 0}
    for reg in sorted(regions, key=lambda x: REGION_ORDER.get(x, 9)):
        sub = {"hc": 0, "salary": 0, "ctc": 0, "ctc_yr": 0}
        unit_rows = []
        for unit, m in sorted(regions[reg], key=lambda t: UNIT_ORDER.get(t[0], 9)):
            unit_rows.append(_row(reg, unit, m, "unit"))
            for k in sub:
                sub[k] += m[k]
        out.extend(unit_rows)
        out.append(_row(reg, reg + " subtotal", sub, "subtotal"))
        for k in grand:
            grand[k] += sub[k]

    if untagged["hc"]:
        out.append(_row("", "Untagged (to tag)", untagged, "untagged"))
        for k in grand:
            grand[k] += untagged[k]

    out.append(_row("", "TOTAL", grand, "grand"))
    return {"rows": out, "current_ctc": grand["ctc"], "current_salary": grand["salary"]}


def _row(region, unit, m, kind):
    return {
        "region": region, "unit": unit, "kind": kind,
        "hc": int(m["hc"]),
        "salary": round(m["salary"]),
        "salary_yr": round(m["salary"] * 12),
        "ctc": round(m["ctc"]),
        "ctc_yr": round(m.get("ctc_yr", m["ctc"] * 12)),
    }


def _plan(company):
    cond = "status = 'Open'"
    vals = {}
    if company:
        cond += " AND company = %(company)s"
        vals["company"] = company
    rows = frappe.db.sql(
        f"""
        SELECT budget_unit AS unit,
               COUNT(*) AS hc,
               SUM(COALESCE(monthly_salary, 0)) AS salary,
               SUM(COALESCE(total_ctc, 0))      AS ctc
        FROM `tabHiring Plan`
        WHERE {cond}
        GROUP BY budget_unit
        """,
        vals, as_dict=True,
    )
    by_unit = {r["unit"]: r for r in rows}
    regions = {}
    for unit, r in by_unit.items():
        regions.setdefault(UNIT_REGION.get(unit, ""), []).append((unit, r))

    out = []
    grand = {"hc": 0, "salary": 0, "ctc": 0}
    for reg in sorted(regions, key=lambda x: REGION_ORDER.get(x, 9)):
        sub = {"hc": 0, "salary": 0, "ctc": 0}
        urows = []
        for unit, r in sorted(regions[reg], key=lambda t: UNIT_ORDER.get(t[0], 9)):
            urows.append({"region": reg, "unit": unit, "kind": "unit",
                          "hc": int(r["hc"]), "salary": round(r["salary"] or 0), "ctc": round(r["ctc"] or 0)})
            sub["hc"] += r["hc"] or 0
            sub["salary"] += r["salary"] or 0
            sub["ctc"] += r["ctc"] or 0
        out.extend(urows)
        out.append({"region": reg, "unit": reg + " subtotal", "kind": "subtotal",
                    "hc": int(sub["hc"]), "salary": round(sub["salary"]), "ctc": round(sub["ctc"])})
        for k in grand:
            grand[k] += sub[k]
    out.append({"region": "", "unit": "TOTAL", "kind": "grand",
                "hc": int(grand["hc"]), "salary": round(grand["salary"]), "ctc": round(grand["ctc"])})
    return {"rows": out, "total_ctc": round(grand["ctc"]), "total_salary": round(grand["salary"])}


def _ramp(company, base_salary):
    cond = "status = 'Open'"
    vals = {}
    if company:
        cond += " AND company = %(company)s"
        vals["company"] = company
    rows = frappe.db.sql(
        f"""
        SELECT budget_unit AS unit, planned_month AS m,
               SUM(COALESCE(monthly_salary, 0)) AS sal
        FROM `tabHiring Plan`
        WHERE {cond}
        GROUP BY budget_unit, planned_month
        """,
        vals, as_dict=True,
    )
    add = {}
    for r in rows:
        if r["m"] in MONTHS:
            add.setdefault(r["unit"], {})[r["m"]] = r["sal"] or 0

    unit_series = []
    for unit in sorted(add, key=lambda u: UNIT_ORDER.get(u, 9)):
        cum, vals_out = 0, []
        for mo in MONTHS:
            cum += add[unit].get(mo, 0)
            vals_out.append(round(cum))
        unit_series.append({"unit": unit, "vals": vals_out})

    total, pct = [], []
    for i in range(6):
        added = sum(u["vals"][i] for u in unit_series)
        total.append(round(base_salary + added))
        pct.append(round((added / base_salary * 100), 1) if base_salary else 0)

    return {"months": MONTH_LBL, "current": [round(base_salary)] * 6,
            "units": unit_series, "total": total, "pct": pct}


def _designations(company):
    """Head count and cost per designation inside each budget unit."""
    cond, vals = _cond(company)
    rows = frappe.db.sql(
        f"""
        SELECT COALESCE(NULLIF(custom_budget_unit, ''), '(untagged)') AS unit,
               COALESCE(NULLIF(designation, ''), '(none)')            AS designation,
               COUNT(*)                                               AS hc,
               SUM(COALESCE(custom_total_salary, 0))                  AS salary,
               SUM(COALESCE(custom_monthly_ctc, 0))                   AS ctc
        FROM `tabEmployee`
        WHERE {cond}
          AND name NOT IN %(owners)s
        GROUP BY unit, designation
        ORDER BY unit, hc DESC
        """,
        dict(vals, owners=tuple(OWNERS)), as_dict=True,
    )

    out = {}
    for r in rows:
        out.setdefault(r["unit"], []).append({
            "designation": r["designation"],
            "hc": int(r["hc"] or 0),
            "salary": round(r["salary"] or 0),
            "ctc": round(r["ctc"] or 0),
        })

    # mirror the CEO split so designation rows still add up to the unit row
    if not company:
        ceo = frappe.db.get_value(
            "Employee", CEO,
            ["custom_budget_unit", "designation", "custom_total_salary", "custom_monthly_ctc"],
            as_dict=True,
        )
        if ceo and ceo.custom_budget_unit in out:
            share_sal = (ceo.custom_total_salary or 0) * CEO_DUBAI_SHARE
            share_ctc = (ceo.custom_monthly_ctc or 0) * CEO_DUBAI_SHARE
            label = ceo.designation or "(none)"
            for row in out[ceo.custom_budget_unit]:
                if row["designation"] == label:
                    row["salary"] = round(row["salary"] - share_sal)
                    row["ctc"] = round(row["ctc"] - share_ctc)
                    break
            out.setdefault("Dubai Office", []).append({
                "designation": CEO_ALLOC_LABEL,
                "hc": 0,
                "salary": round(share_sal),
                "ctc": round(share_ctc),
            })

    return out


def _months_back(n=6):
    """Last n months, oldest first, as (year, month)."""
    from datetime import date

    today = date.today()
    out = []
    for i in range(n - 1, -1, -1):
        mm, yy = today.month - i, today.year
        while mm <= 0:
            mm += 12
            yy -= 1
        out.append((yy, mm))
    return out


def _movement(company, current_ctc):
    """Joiners and leavers over the last 6 months and the effect on monthly CTC."""
    months = _months_back(6)
    start = "{0}-{1:02d}-01".format(months[0][0], months[0][1])

    vals = {"start": start, "owners": tuple(OWNERS)}
    ccond = ""
    if company:
        ccond = " AND company = %(company)s"
        vals["company"] = company

    joiners = frappe.db.sql(
        f"""
        SELECT DATE_FORMAT(date_of_joining, '%%Y-%%m') AS m,
               COUNT(*)                             AS hc,
               SUM(COALESCE(custom_monthly_ctc, 0)) AS ctc
        FROM `tabEmployee`
        WHERE date_of_joining IS NOT NULL
          AND date_of_joining >= %(start)s
          AND name NOT IN %(owners)s
          {ccond}
        GROUP BY m
        """,
        vals, as_dict=True,
    )

    leavers = frappe.db.sql(
        f"""
        SELECT DATE_FORMAT(relieving_date, '%%Y-%%m') AS m,
               COUNT(*)                             AS hc,
               SUM(COALESCE(custom_monthly_ctc, 0)) AS ctc
        FROM `tabEmployee`
        WHERE relieving_date IS NOT NULL
          AND relieving_date >= %(start)s
          AND name NOT IN %(owners)s
          {ccond}
        GROUP BY m
        """,
        vals, as_dict=True,
    )

    jmap = {r["m"]: r for r in joiners}
    lmap = {r["m"]: r for r in leavers}

    keys = ["{0}-{1:02d}".format(y, m) for y, m in months]
    labels = [MONTH_NAMES[m - 1] for _, m in months]

    total_added = sum(float((jmap.get(k) or {}).get("ctc") or 0) for k in keys)
    total_removed = sum(float((lmap.get(k) or {}).get("ctc") or 0) for k in keys)

    running = (current_ctc or 0) - total_added + total_removed

    rows = []
    n_joined = n_left = 0
    for key, label in zip(keys, labels):
        j = jmap.get(key) or {}
        l = lmap.get(key) or {}
        added = float(j.get("ctc") or 0)
        removed = float(l.get("ctc") or 0)
        closing = running + added - removed
        rows.append({
            "month": label,
            "key": key,
            "opening": round(running),
            "joined": int(j.get("hc") or 0),
            "added": round(added),
            "left": int(l.get("hc") or 0),
            "removed": round(removed),
            "closing": round(closing),
        })
        n_joined += int(j.get("hc") or 0)
        n_left += int(l.get("hc") or 0)
        running = closing

    ucond = ""
    uvals = {}
    if company:
        ucond = " AND company = %(company)s"
        uvals["company"] = company

    undated = frappe.db.sql(
        f"""
        SELECT COUNT(*) FROM `tabEmployee`
        WHERE status = 'Left'
          AND (relieving_date IS NULL OR relieving_date = '')
          {ucond}
        """,
        uvals,
    )
    undated_count = int(undated[0][0]) if undated else 0

    return {
        "rows": rows,
        "net_joined": n_joined,
        "net_added": round(total_added),
        "net_left": n_left,
        "net_removed": round(total_removed),
        "closing": round(running),
        "undated_leavers": undated_count,
    }
