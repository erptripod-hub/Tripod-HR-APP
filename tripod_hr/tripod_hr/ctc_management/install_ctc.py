"""
Tripod CTC — one-shot installer.

Does EVERYTHING needed to make the CTC tab and calculations work:
  1. Creates 31 custom fields on Employee + Salary Structure Assignment
  2. Seeds 9 CTC Component Default records (one per branch)
  3. Populates CTC values on all existing active employees
  4. Clears Frappe's cache

Idempotent — safe to run any number of times. Re-running with everything
already in place takes ~1 second (no-op for already-installed pieces).

Usage:
    bench --site tripod.k.frappe.cloud execute tripod_hr.tripod_hr.ctc_management.install_ctc.execute

Or just `bench --site SITE migrate` — this is wired as an after_migrate hook,
so it runs automatically every time you migrate.
"""
import os
import json
import frappe
from frappe.utils import flt
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


BRANCH_DEFAULTS = [
    # (branch, company, country, is_ksa_national,
    #  accom, visa, iqama, medical, ticket, transport,
    #  grat_1to5, grat_5plus, probation_yrs)
    ("Fit Out UAE", "Tripod Media", "UAE", 0, 650, 180, 0, 58, 62.5, 22, 21, 30, 1),
    ("Dubai Production", "Tripod Media", "UAE", 0, 650, 180, 0, 58, 62.5, 22, 21, 30, 1),
    ("Dubai Office Staff", "Tripod Media", "UAE", 0, 0, 180, 0, 200, 175, 0, 21, 30, 1),
    ("KSA Office Staff", "Tripod Global", "KSA", 0, 0, 0, 87, 282, 182, 0, 15, 30, 2),
    ("KSA National", "Tripod Global", "KSA", 1, 0, 0, 0, 0, 0, 0, 15, 30, 2),
    ("KSA Labour", "Tripod Global", "KSA", 0, 800, 0, 96, 55, 22, 63, 15, 30, 2),
    ("KSA Fit Out", "Tripod Global", "KSA", 0, 800, 0, 57, 54, 63, 22, 15, 30, 2),
    ("Luxxe Labour", "Luxxe", "UAE", 0, 650, 180, 0, 58, 62.5, 22, 21, 30, 1),
    ("Luxxe Office", "Luxxe", "UAE", 0, 0, 180, 0, 350, 142, 0, 21, 30, 1),
]


def execute():
    """Main entry point. Runs all 4 steps with progress output."""
    print("\n" + "="*70)
    print("CTC INSTALLER — running all steps")
    print("="*70)

    print("\n[1/4] Creating custom fields on Employee + SSA...")
    created = _install_custom_fields()
    print(f"      OK — {created['created']} created, {created['updated']} updated")

    print("\n[2/4] Seeding CTC Component Defaults (9 branches)...")
    seeded = _seed_ctc_defaults()
    print(f"      OK — {seeded} branches configured")

    print("\n[3/4] Populating CTC fields on existing employees...")
    populated = _populate_existing_employees()
    print(f"      OK — {populated['processed']} processed, "
          f"{populated['errors']} errors")

    print("\n[4/4] Clearing cache...")
    frappe.clear_cache()
    print("      OK")

    print("\n" + "="*70)
    print("DONE.")
    print("Now hard-refresh your browser (Ctrl+Shift+R) on the Employee form.")
    print("Make sure HR Manager role has Permission Level 1 on Employee + SSA.")
    print("="*70 + "\n")


def _install_custom_fields():
    """Step 1: install all 31 custom fields from fixture JSONs."""
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

    all_fields = []
    for fname in ("custom_field_employee.json", "custom_field_ssa.json"):
        with open(os.path.join(fixtures_dir, fname)) as fp:
            all_fields.extend(json.load(fp))

    grouped = {}
    created = 0
    updated = 0
    for f in all_fields:
        dt = f["dt"]
        clean = {k: v for k, v in f.items() if k not in ("doctype", "dt")}
        grouped.setdefault(dt, []).append(clean)

        existing = frappe.db.exists("Custom Field",
            {"dt": dt, "fieldname": clean["fieldname"]})
        if existing:
            updated += 1
        else:
            created += 1

    create_custom_fields(grouped, ignore_validate=True, update=True)
    frappe.db.commit()

    return {"created": created, "updated": updated}


def _seed_ctc_defaults():
    """Step 2: ensure 9 CTC Component Default records exist."""
    count = 0
    for row in BRANCH_DEFAULTS:
        (branch_name, company, country, is_ksa_nat,
         accom, visa, iqama, medical, ticket, transport,
         g15, g5p, probation) = row

        if not frappe.db.exists("Company", company):
            print(f"      WARN: Company '{company}' not found, skipping {branch_name}")
            continue

        if not frappe.db.exists("Branch", branch_name):
            try:
                b = frappe.new_doc("Branch")
                b.branch = branch_name
                b.insert(ignore_permissions=True)
            except Exception as e:
                print(f"      WARN: could not create branch {branch_name}: {e}")
                continue

        if frappe.db.exists("CTC Component Default", branch_name):
            doc = frappe.get_doc("CTC Component Default", branch_name)
        else:
            doc = frappe.new_doc("CTC Component Default")
            doc.branch = branch_name

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
    return count


def _populate_existing_employees():
    """Step 3: populate CTC fields on every active employee."""
    required_cols = [
        "custom_accommodation", "custom_visa", "custom_iqama",
        "custom_medical_insurance", "custom_ticket_allowance",
        "custom_transport", "custom_total_salary", "custom_gratuity_monthly",
        "custom_monthly_ctc", "custom_annual_ctc",
    ]
    missing = [c for c in required_cols if not frappe.db.has_column("Employee", c)]
    if missing:
        print(f"      WARN: required columns missing: {missing} — skipping populate")
        return {"processed": 0, "errors": 0}

    try:
        from tripod_hr.tripod_hr.ctc_management.ctc_engine import (
            calculate_employee_ctc, sync_employee_fields,
            sync_ssa_fields, get_ctc_defaults,
        )
    except Exception as e:
        print(f"      WARN: cannot import ctc_engine: {e}")
        return {"processed": 0, "errors": 0}

    employees = frappe.db.sql("""
        SELECT name, branch, company, date_of_joining,
               COALESCE(custom_accommodation, 0) AS custom_accommodation,
               COALESCE(custom_visa, 0) AS custom_visa,
               COALESCE(custom_iqama, 0) AS custom_iqama,
               COALESCE(custom_medical_insurance, 0) AS custom_medical_insurance,
               COALESCE(custom_ticket_allowance, 0) AS custom_ticket_allowance,
               COALESCE(custom_transport, 0) AS custom_transport
        FROM `tabEmployee`
        WHERE status = 'Active'
    """, as_dict=True)

    total = len(employees)
    print(f"      Found {total} active employees")
    processed = 0
    errors = []

    for i, emp in enumerate(employees, 1):
        try:
            if not emp.branch:
                continue
            defaults = get_ctc_defaults(emp.branch)
            if not defaults:
                errors.append(f"{emp.name}: no CTC default for branch {emp.branch}")
                continue

            update = {}
            if defaults.is_ksa_national_branch:
                update = {
                    "custom_accommodation": 0, "custom_visa": 0,
                    "custom_iqama": 0, "custom_medical_insurance": 0,
                    "custom_ticket_allowance": 0, "custom_transport": 0,
                }
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
                frappe.db.set_value("Employee", emp.name, update,
                                    update_modified=False)

            ctc = calculate_employee_ctc(emp.name)
            sync_employee_fields(emp.name, ctc)
            if ctc.get("ssa_name"):
                sync_ssa_fields(ctc["ssa_name"], ctc, emp.name)

            processed += 1

            if i % 100 == 0:
                frappe.db.commit()
                print(f"      ... {i}/{total} done")

        except Exception as e:
            errors.append(f"{emp.name}: {str(e)[:120]}")

    frappe.db.commit()

    if errors:
        frappe.log_error("CTC populate errors:\n" + "\n".join(errors[:100]),
                          "CTC Installer")
        print(f"      First 3 errors:")
        for err in errors[:3]:
            print(f"        - {err}")

    return {"processed": processed, "errors": len(errors)}
