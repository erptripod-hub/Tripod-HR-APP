"""
v1_1_migrate_existing_employees

POST-MODEL-SYNC patch: runs AFTER custom field fixtures are loaded.

Populates Employee CTC fields for all existing active employees from their
branch defaults + active SSA, then syncs to SSA.

Idempotent: safe to re-run.
"""
import frappe
from frappe.utils import flt


REQUIRED_COLUMNS = [
    "custom_accommodation",
    "custom_visa",
    "custom_iqama",
    "custom_medical_insurance",
    "custom_ticket_allowance",
    "custom_transport",
    "custom_total_salary",
    "custom_gratuity_monthly",
    "custom_monthly_ctc",
    "custom_annual_ctc",
]


def execute():
    missing = [c for c in REQUIRED_COLUMNS if not frappe.db.has_column("Employee", c)]
    if missing:
        msg = (
            "CTC custom fields not yet synced on Employee. Missing columns: {missing}.\n"
            "This patch must run AFTER fixture sync. Ensure patches.txt has "
            "'[post_model_sync]' header before this patch entry, then re-run "
            "`bench migrate`."
        ).format(missing=", ".join(missing))
        frappe.log_error(msg, "CTC Migration v1_1 - skipped")
        print(f"\n[CTC Migration v1_1] SKIPPED: {msg}")
        return

    from tripod_hr.tripod_hr.ctc_management.ctc_engine import (
        calculate_employee_ctc,
        sync_employee_fields,
        sync_ssa_fields,
        get_ctc_defaults,
    )

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
    print(f"\n[CTC Migration v1_1] Processing {total} active employees...")

    populated = 0
    calculated = 0
    skipped = 0
    errors = []

    for i, emp in enumerate(employees, 1):
        try:
            if not emp.branch:
                skipped += 1
                continue

            defaults = get_ctc_defaults(emp.branch)
            if not defaults:
                skipped += 1
                errors.append(f"{emp.name}: no CTC defaults for branch {emp.branch}")
                continue

            update_fields = {}

            if defaults.is_ksa_national_branch:
                update_fields = {
                    "custom_accommodation": 0,
                    "custom_visa": 0,
                    "custom_iqama": 0,
                    "custom_medical_insurance": 0,
                    "custom_ticket_allowance": 0,
                    "custom_transport": 0,
                }
            else:
                if not flt(emp.custom_accommodation):
                    update_fields["custom_accommodation"] = flt(defaults.default_accommodation)
                if not flt(emp.custom_visa) and defaults.country == "UAE":
                    update_fields["custom_visa"] = flt(defaults.default_visa)
                if not flt(emp.custom_iqama) and defaults.country == "KSA":
                    update_fields["custom_iqama"] = flt(defaults.default_iqama)
                if not flt(emp.custom_medical_insurance):
                    update_fields["custom_medical_insurance"] = flt(defaults.default_medical_insurance)
                if not flt(emp.custom_ticket_allowance):
                    update_fields["custom_ticket_allowance"] = flt(defaults.default_ticket_allowance)
                if not flt(emp.custom_transport):
                    update_fields["custom_transport"] = flt(defaults.default_transport)

            if update_fields:
                frappe.db.set_value("Employee", emp.name, update_fields, update_modified=False)
                populated += 1

            ctc = calculate_employee_ctc(emp.name)

            sync_employee_fields(emp.name, ctc)

            if ctc.get("ssa_name"):
                sync_ssa_fields(ctc["ssa_name"], ctc, emp.name)

            calculated += 1

            if i % 50 == 0:
                frappe.db.commit()
                print(f"  [{i}/{total}] processed...")

        except Exception as e:
            errors.append(f"{emp.name}: {str(e)}")

    frappe.db.commit()

    print(f"\n[CTC Migration v1_1] DONE")
    print(f"  Total employees:       {total}")
    print(f"  Defaults populated:    {populated}")
    print(f"  CTC calculated/synced: {calculated}")
    print(f"  Skipped (no branch):   {skipped}")
    print(f"  Errors:                {len(errors)}")

    if errors:
        frappe.log_error(
            "CTC Migration errors:\n" + "\n".join(errors[:100]),
            "CTC Migration v1_1"
        )
        print(f"\n  First 5 errors:")
        for err in errors[:5]:
            print(f"    - {err}")
