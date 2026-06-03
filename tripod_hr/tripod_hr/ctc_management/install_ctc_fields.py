"""
Tripod CTC — Deploy 1: install custom fields only.

This script:
  1. Finds the correct insert_after for the CTC tab (last field in attendance tab)
  2. Creates 15 custom fields on Employee + 10 on Salary Structure Assignment

Wired to after_migrate hook. Idempotent — safe to re-run.

Manual trigger (if hook fails):
    bench --site SITE execute tripod_hr.tripod_hr.ctc_management.install_ctc_fields.install
"""
import os
import json
import frappe


def install():
    """Entry point. Wrapped in try/except so migrate never breaks if this fails."""
    try:
        print("\n" + "=" * 60)
        print("CTC FIELDS INSTALLER")
        print("=" * 60)

        # Step 1: find correct position
        last_attendance = _find_last_attendance_field()
        print(f"\n[1/2] CTC tab will be inserted after: {last_attendance}")

        # Step 2: install fields
        result = _install_fields(last_attendance)
        print(f"\n[2/2] {result}")

        frappe.clear_cache()
        print("\nCache cleared. Hard-refresh browser to see CTC tab.")
        print("=" * 60 + "\n")

    except Exception as e:
        # Log but do NOT raise — keeps migrate from breaking
        msg = f"CTC FIELDS INSTALLER FAILED: {e}"
        print("\n" + "!" * 60)
        print(msg)
        print("!" * 60 + "\n")
        try:
            frappe.log_error(msg, "CTC Fields Install")
        except Exception:
            pass


def _find_last_attendance_field():
    """Return fieldname of the last field within the attendance tab."""
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


def _install_fields(last_attendance):
    """Install custom fields from the fixture JSON files."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

    grouped = {}
    for fname in ("custom_field_employee.json", "custom_field_ssa.json"):
        with open(os.path.join(fixtures_dir, fname)) as fp:
            for field in json.load(fp):
                if field.get("fieldname") == "custom_ctc_tab":
                    field["insert_after"] = last_attendance
                dt = field["dt"]
                clean = {k: v for k, v in field.items() if k != "dt"}
                grouped.setdefault(dt, []).append(clean)

    create_custom_fields(grouped, ignore_validate=True, update=True)
    frappe.db.commit()

    emp = frappe.db.count("Custom Field",
        {"dt": "Employee", "fieldname": ["like", "custom_ctc%"]})
    emp_all = frappe.db.count("Custom Field",
        {"dt": "Employee",
         "fieldname": ["in", ["custom_accommodation", "custom_visa", "custom_iqama",
                              "custom_medical_insurance", "custom_ticket_allowance",
                              "custom_transport", "custom_total_salary",
                              "custom_gratuity_monthly", "custom_monthly_ctc",
                              "custom_annual_ctc"]]})
    ssa = frappe.db.count("Custom Field",
        {"dt": "Salary Structure Assignment",
         "fieldname": ["like", "custom_ctc%"]})

    return f"Employee CTC fields: {emp + emp_all}, SSA CTC fields: {ssa}"
