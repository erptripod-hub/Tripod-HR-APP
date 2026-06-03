"""
Tripod CTC — comprehensive one-shot installer.

Wired as after_migrate hook. Runs automatically on every `bench migrate`.
Idempotent — safe to re-run.

Steps:
  1. Import required doctypes (CTC Component Default, Employee Deployment History)
  2. Determine correct insert_after for the CTC tab (last attendance field)
  3. Install/update 31 custom fields on Employee + SSA
  4. Seed 9 CTC Component Default records
  5. Create 3 Report doctype records (HR Budget, HR Manpower, Monthly CTC Comparison)
  6. Create Dashboard + 4 Charts + 4 Number Cards
  7. Populate CTC fields on all active employees
  8. Clear cache
"""
import os
import json
import frappe
from frappe.utils import flt
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


BRANCH_DEFAULTS = [
    ("Fit Out UAE",        "Tripod Media",  "UAE", 0, 650, 180,  0,  58, 62.5, 22, 21, 30, 1),
    ("Dubai Production",   "Tripod Media",  "UAE", 0, 650, 180,  0,  58, 62.5, 22, 21, 30, 1),
    ("Dubai Office Staff", "Tripod Media",  "UAE", 0,   0, 180,  0, 200,  175,  0, 21, 30, 1),
    ("KSA Office Staff",   "Tripod Global", "KSA", 0,   0,   0, 87, 282,  182,  0, 15, 30, 2),
    ("KSA National",       "Tripod Global", "KSA", 1,   0,   0,  0,   0,    0,  0, 15, 30, 2),
    ("KSA Labour",         "Tripod Global", "KSA", 0, 800,   0, 96,  55,   22, 63, 15, 30, 2),
    ("KSA Fit Out",        "Tripod Global", "KSA", 0, 800,   0, 57,  54,   63, 22, 15, 30, 2),
    ("Luxxe Labour",       "Luxxe",         "UAE", 0, 650, 180,  0,  58, 62.5, 22, 21, 30, 1),
    ("Luxxe Office",       "Luxxe",         "UAE", 0,   0, 180,  0, 350,  142,  0, 21, 30, 1),
]


def execute():
    print("\n" + "="*70)
    print("CTC INSTALLER — running all steps")
    print("="*70)

    print("\n[1/8] Ensuring required doctypes exist...")
    print(f"      {_ensure_doctypes()}")

    print("\n[2/8] Finding correct insert_after for CTC tab...")
    last_attendance = _find_last_attendance_field()
    print(f"      Will insert CTC tab after field: {last_attendance}")

    print("\n[3/8] Installing custom fields on Employee + SSA...")
    print(f"      {_install_custom_fields(last_attendance)}")

    print("\n[4/8] Seeding CTC Component Defaults (9 branches)...")
    print(f"      {_seed_ctc_defaults()}")

    print("\n[5/8] Creating Report records...")
    print(f"      {_create_reports()}")

    print("\n[6/8] Creating Dashboard + Charts + Number Cards...")
    print(f"      {_create_dashboard()}")

    print("\n[7/8] Populating CTC fields on existing employees...")
    print(f"      {_populate_existing_employees()}")

    print("\n[8/8] Clearing cache...")
    frappe.clear_cache()
    print("      OK")

    print("\n" + "="*70)
    print("DONE. Hard-refresh browser (Ctrl+Shift+R).")
    print("Make sure your user has HR Manager role to see CTC tab.")
    print("="*70 + "\n")


def _ensure_doctypes():
    from frappe.modules.import_file import import_file_by_path
    base = os.path.dirname(__file__)
    targets = [
        ("CTC Component Default",
         os.path.join(base, "doctype", "ctc_component_default", "ctc_component_default.json")),
        ("Employee Deployment History",
         os.path.join(base, "doctype", "employee_deployment_history", "employee_deployment_history.json")),
    ]
    imported = existing = 0
    for name, path in targets:
        if frappe.db.exists("DocType", name):
            existing += 1
            continue
        if not os.path.exists(path):
            continue
        try:
            import_file_by_path(path, force=True, ignore_version=True)
            imported += 1
        except Exception as e:
            print(f"      WARN: import {name}: {e}")
    frappe.db.commit()
    return f"{imported} imported, {existing} already existed"


def _find_last_attendance_field():
    """Return the fieldname of the last field within the attendance tab."""
    res = frappe.db.sql("""
        SELECT fieldname FROM `tabDocField`
        WHERE parent = 'Employee'
          AND idx > (SELECT idx FROM `tabDocField`
                     WHERE parent='Employee' AND fieldname='attendance_and_leave_details' LIMIT 1)
          AND idx < COALESCE(
              (SELECT MIN(idx) FROM `tabDocField`
               WHERE parent='Employee' AND fieldtype='Tab Break'
                 AND idx > (SELECT idx FROM `tabDocField`
                            WHERE parent='Employee' AND fieldname='attendance_and_leave_details' LIMIT 1)),
              999999
          )
        ORDER BY idx DESC LIMIT 1
    """, as_dict=True)
    return res[0].fieldname if res else "attendance_and_leave_details"


def _install_custom_fields(last_attendance_field):
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    all_fields = []
    for fname in ("custom_field_employee.json", "custom_field_ssa.json"):
        with open(os.path.join(fixtures_dir, fname)) as fp:
            all_fields.extend(json.load(fp))

    grouped = {}
    for f in all_fields:
        if f.get("fieldname") == "custom_ctc_tab":
            f["insert_after"] = last_attendance_field
        clean = {k: v for k, v in f.items() if k not in ("doctype", "dt")}
        grouped.setdefault(f["dt"], []).append(clean)

    create_custom_fields(grouped, ignore_validate=True, update=True)
    frappe.db.commit()

    emp_n = frappe.db.count("Custom Field", {"dt": "Employee", "fieldname": ["like", "custom_%"]})
    ssa_n = frappe.db.count("Custom Field",
        {"dt": "Salary Structure Assignment", "fieldname": ["like", "custom_%"]})
    return f"Employee: {emp_n} fields, SSA: {ssa_n} fields"


def _seed_ctc_defaults():
    count = 0
    for row in BRANCH_DEFAULTS:
        (branch, company, country, is_ksa_nat,
         accom, visa, iqama, medical, ticket, transport,
         g15, g5p, probation) = row

        if not frappe.db.exists("Company", company):
            continue

        if not frappe.db.exists("Branch", branch):
            try:
                b = frappe.new_doc("Branch")
                b.branch = branch
                b.insert(ignore_permissions=True)
            except Exception:
                continue

        if frappe.db.exists("CTC Component Default", branch):
            doc = frappe.get_doc("CTC Component Default", branch)
        else:
            doc = frappe.new_doc("CTC Component Default")
            doc.branch = branch

        doc.company = company
        doc.country = country
        doc.is_ksa_national_branch = is_ksa_nat
        doc.default_accommodation = accom
        doc.default_visa = visa
        doc.default_iqama = iqama
        doc.default_medical_insurance = medical
        doc.default_ticket_allowance = ticket
        doc.default_transport = transport
        doc.gratuity_days_year1to5 = g15
        doc.gratuity_days_year5plus = g5p
        doc.probation_years_no_gratuity = probation
        doc.save(ignore_permissions=True)
        count += 1
    frappe.db.commit()
    return f"{count} branches configured"


def _create_reports():
    reports = [
        ("HR Budget Summary", "Employee", "Script Report",
         ["HR Manager", "System Manager", "Accounts Manager"]),
        ("HR Manpower Summary", "Employee", "Script Report",
         ["HR Manager", "HR User", "System Manager"]),
        ("Monthly CTC Comparison", "Employee", "Script Report",
         ["HR Manager", "System Manager", "Accounts Manager"]),
    ]
    created = updated = 0
    for name, ref_dt, rtype, roles in reports:
        if frappe.db.exists("Report", name):
            doc = frappe.get_doc("Report", name)
            doc.ref_doctype = ref_dt
            doc.report_type = rtype
            doc.module = "Tripod HR"
            doc.is_standard = "Yes"
            doc.disabled = 0
            doc.roles = []
            for r in roles:
                doc.append("roles", {"role": r})
            doc.save(ignore_permissions=True)
            updated += 1
        else:
            doc = frappe.new_doc("Report")
            doc.report_name = name
            doc.ref_doctype = ref_dt
            doc.report_type = rtype
            doc.module = "Tripod HR"
            doc.is_standard = "Yes"
            doc.disabled = 0
            for r in roles:
                doc.append("roles", {"role": r})
            doc.insert(ignore_permissions=True)
            created += 1
    frappe.db.commit()
    return f"{created} created, {updated} updated"


def _create_dashboard():
    cards = [
        ("Total Active Headcount", "Count", None, "#7575FF",
         [["Employee", "status", "=", "Active"]]),
        ("Total Monthly CTC", "Sum", "custom_monthly_ctc", "#39E4A5",
         [["Employee", "status", "=", "Active"]]),
        ("Total Annual CTC", "Sum", "custom_annual_ctc", "#2490EF",
         [["Employee", "status", "=", "Active"]]),
        ("Hires Last 30 Days", "Count", None, "#FFA00A",
         [["Employee", "date_of_joining", ">", "2026-05-04"]]),
    ]
    cards_created = 0
    for label, func, agg_field, color, filters in cards:
        if frappe.db.exists("Number Card", label):
            doc = frappe.get_doc("Number Card", label)
        else:
            doc = frappe.new_doc("Number Card")
            doc.name = label
        doc.label = label
        doc.type = "Document Type"
        doc.document_type = "Employee"
        doc.function = func
        if agg_field:
            doc.aggregate_function_based_on = agg_field
        doc.filters_json = json.dumps(filters)
        doc.color = color
        doc.is_public = 1
        doc.module = "Tripod HR"
        doc.save(ignore_permissions=True)
        cards_created += 1

    charts = [
        ("Headcount by Company",     "Group By", "company", "Count", None, "Pie"),
        ("Headcount by Branch",      "Group By", "branch",  "Count", None, "Bar"),
        ("Monthly CTC by Company",   "Group By", "company", "Sum",   "custom_monthly_ctc", "Donut"),
        ("Monthly CTC by Branch",    "Group By", "branch",  "Sum",   "custom_monthly_ctc", "Bar"),
    ]
    charts_created = 0
    for name, ctype, group_by, group_type, agg_field, vis in charts:
        if frappe.db.exists("Dashboard Chart", name):
            doc = frappe.get_doc("Dashboard Chart", name)
        else:
            doc = frappe.new_doc("Dashboard Chart")
            doc.name = name
        doc.chart_name = name
        doc.chart_type = ctype
        doc.document_type = "Employee"
        doc.group_by_based_on = group_by
        doc.group_by_type = group_type
        if agg_field:
            doc.aggregate_function_based_on = agg_field
        doc.type = vis
        doc.filters_json = json.dumps([["Employee", "status", "=", "Active"]])
        doc.is_public = 1
        doc.module = "Tripod HR"
        doc.timespan = "Last Year"
        doc.time_interval = "Yearly"
        doc.save(ignore_permissions=True)
        charts_created += 1

    dash_name = "HR Manpower & Budget"
    if frappe.db.exists("Dashboard", dash_name):
        doc = frappe.get_doc("Dashboard", dash_name)
        doc.charts = []
        doc.cards = []
    else:
        doc = frappe.new_doc("Dashboard")
        doc.dashboard_name = dash_name
    doc.module = "Tripod HR"
    doc.is_default = 0
    doc.is_standard = 1
    for name, *_ in charts:
        doc.append("charts", {"chart": name})
    for label, *_ in cards:
        doc.append("cards", {"card": label})
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return f"{cards_created} cards, {charts_created} charts, 1 dashboard"


def _populate_existing_employees():
    required = ["custom_accommodation", "custom_visa", "custom_iqama",
                "custom_medical_insurance", "custom_ticket_allowance",
                "custom_transport", "custom_total_salary", "custom_gratuity_monthly",
                "custom_monthly_ctc", "custom_annual_ctc"]
    missing = [c for c in required if not frappe.db.has_column("Employee", c)]
    if missing:
        return f"SKIP — missing columns: {missing}"

    try:
        from tripod_hr.tripod_hr.ctc_management.ctc_engine import (
            calculate_employee_ctc, sync_employee_fields,
            sync_ssa_fields, get_ctc_defaults,
        )
    except Exception as e:
        return f"SKIP — engine import failed: {e}"

    employees = frappe.db.sql("""
        SELECT name, branch, company, date_of_joining,
               COALESCE(custom_accommodation, 0) AS custom_accommodation,
               COALESCE(custom_visa, 0) AS custom_visa,
               COALESCE(custom_iqama, 0) AS custom_iqama,
               COALESCE(custom_medical_insurance, 0) AS custom_medical_insurance,
               COALESCE(custom_ticket_allowance, 0) AS custom_ticket_allowance,
               COALESCE(custom_transport, 0) AS custom_transport
        FROM `tabEmployee` WHERE status = 'Active'
    """, as_dict=True)
    total = len(employees)
    processed = 0
    errors = []

    for i, emp in enumerate(employees, 1):
        try:
            if not emp.branch:
                continue
            defaults = get_ctc_defaults(emp.branch)
            if not defaults:
                errors.append(f"{emp.name}: no default for branch {emp.branch}")
                continue
            update = {}
            if defaults.is_ksa_national_branch:
                update = {f"custom_{k}": 0 for k in
                          ["accommodation", "visa", "iqama",
                           "medical_insurance", "ticket_allowance", "transport"]}
            else:
                if not flt(emp.custom_accommodation):
                    update["custom_accommodation"] = flt(defaults.default_accommodation)
                if not flt(emp.custom_visa) and defaults.country == "UAE":
                    update["custom_visa"] = flt(defaults.default_visa)
                if not flt(emp.custom_iqama) and defaults.country == "KSA":
                    update["custom_iqama"] = flt(defaults.default_iqama)
                if not flt(emp.custom_medical_insurance):
                    update["custom_medical_insurance"] = flt(defaults.default_medical_insurance)
                if not flt(emp.custom_ticket_allowance):
                    update["custom_ticket_allowance"] = flt(defaults.default_ticket_allowance)
                if not flt(emp.custom_transport):
                    update["custom_transport"] = flt(defaults.default_transport)
            if update:
                frappe.db.set_value("Employee", emp.name, update, update_modified=False)
            ctc = calculate_employee_ctc(emp.name)
            sync_employee_fields(emp.name, ctc)
            if ctc.get("ssa_name"):
                sync_ssa_fields(ctc["ssa_name"], ctc, emp.name)
            processed += 1
            if i % 100 == 0:
                frappe.db.commit()
        except Exception as e:
            errors.append(f"{emp.name}: {str(e)[:120]}")
    frappe.db.commit()
    if errors:
        frappe.log_error("CTC populate errors:\n" + "\n".join(errors[:100]),
                          "CTC Installer")
    return f"{processed}/{total} processed, {len(errors)} errors"
