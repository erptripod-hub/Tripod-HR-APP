import frappe

REGION_ORDER = {"UAE": 1, "KSA": 2, "": 9}
UNIT_ORDER = {
    "Fit Out UAE": 1, "Dubai Production": 2, "Dubai Office": 3,
    "KSA Office": 4, "KSA National": 5, "KSA Labour": 6, "KSA Fit Out": 7,
}
UNIT_REGION = {
    "Fit Out UAE": "UAE", "Dubai Production": "UAE", "Dubai Office": "UAE",
    "KSA Office": "KSA", "KSA National": "KSA", "KSA Labour": "KSA", "KSA Fit Out": "KSA",
}
MONTHS = ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]
MONTH_LBL = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@frappe.whitelist()
def get_budget_dashboard(company=None):
    company = company or None
    active = _active(company)
    plan = _plan(company)
    ramp = _ramp(company, active["current_salary"])
    return {"active": active, "plan": plan, "ramp": ramp}


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
        GROUP BY unit, region
        """,
        vals, as_dict=True,
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
