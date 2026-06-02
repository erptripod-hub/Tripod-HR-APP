"""
Programmatic installer for CTC custom fields on Employee and SSA.

Reads the fixture JSON files in this folder and calls Frappe's
create_custom_fields() which is idempotent (skips existing fields).

Usage:
    bench --site tripod.k.frappe.cloud execute tripod_hr.tripod_hr.ctc_management.install_custom_fields.execute
"""
import os
import json
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _load_fixture(filename):
    """Load a fixture JSON file from the fixtures/ folder next to this file."""
    base = os.path.dirname(__file__)
    path = os.path.join(base, "fixtures", filename)
    with open(path) as f:
        return json.load(f)


def _group_by_doctype(field_list):
    """Convert flat list of Custom Field dicts to {doctype: [field_dicts]}."""
    grouped = {}
    for f in field_list:
        dt = f.get("dt")
        if not dt:
            continue
        clean = {k: v for k, v in f.items() if k not in ("doctype", "dt")}
        grouped.setdefault(dt, []).append(clean)
    return grouped


def execute():
    print("\n[CTC] Installing custom fields on Employee and SSA...")

    emp_fields = _load_fixture("custom_field_employee.json")
    ssa_fields = _load_fixture("custom_field_ssa.json")

    emp_grouped = _group_by_doctype(emp_fields)
    ssa_grouped = _group_by_doctype(ssa_fields)

    all_grouped = {}
    for dt, fields in emp_grouped.items():
        all_grouped.setdefault(dt, []).extend(fields)
    for dt, fields in ssa_grouped.items():
        all_grouped.setdefault(dt, []).extend(fields)

    for doctype, fields in all_grouped.items():
        print(f"  - {doctype}: {len(fields)} field(s)")

    create_custom_fields(all_grouped, ignore_validate=True, update=True)

    frappe.db.commit()
    frappe.clear_cache()

    employee_count = frappe.db.count("Custom Field",
        {"dt": "Employee", "fieldname": ["like", "custom_%"]})
    ssa_count = frappe.db.count("Custom Field",
        {"dt": "Salary Structure Assignment", "fieldname": ["like", "custom_%"]})

    print(f"\n[CTC] DONE")
    print(f"  Employee custom fields:                    {employee_count}")
    print(f"  Salary Structure Assignment custom fields: {ssa_count}")
    print(f"\nNow do a HARD REFRESH (Ctrl+Shift+R) on the Employee form.")
    print(f"Make sure HR Manager role has Permission Level 1 granted.")
