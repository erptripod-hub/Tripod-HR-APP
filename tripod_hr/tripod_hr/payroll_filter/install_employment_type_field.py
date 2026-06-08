"""
Payroll Filter — install employment_type custom field on Payroll Entry.

Adds a single Link field `employment_type` (linked to Employment Type doctype),
positioned next to the existing Branch / Department filters.

Wired to after_migrate hook. Idempotent — safe to re-run.

Manual trigger (if hook fails):
    bench --site SITE execute tripod_hr.tripod_hr.payroll_filter.install_employment_type_field.install
"""
import frappe


FIELDNAME = "employment_type"
DOCTYPE = "Payroll Entry"


def install():
    """Entry point. Wrapped in try/except so migrate never breaks if this fails."""
    try:
        print("\n" + "=" * 60)
        print("PAYROLL FILTER — employment_type field installer")
        print("=" * 60)

        # Determine where to insert (after Department field on Payroll Entry)
        insert_after = _find_insert_after()
        print(f"\n[1/1] Inserting {FIELDNAME} after: {insert_after}")

        _install_field(insert_after)
        frappe.clear_cache(doctype=DOCTYPE)
        print(f"\n✓ employment_type custom field ready on {DOCTYPE}")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n✗ Payroll filter installer failed: {e}")
        frappe.log_error(frappe.get_traceback(), "Payroll Filter installer")


def _find_insert_after():
    """Place the field next to Department if it exists, else after Branch, else after Company."""
    preferred_order = ["department", "branch", "company"]
    meta = frappe.get_meta(DOCTYPE)
    field_names = {f.fieldname for f in meta.fields}
    for fn in preferred_order:
        if fn in field_names:
            return fn
    # Fallback
    return "company"


def _install_field(insert_after):
    """Create or update the employment_type Custom Field."""
    existing = frappe.db.get_value(
        "Custom Field",
        {"dt": DOCTYPE, "fieldname": FIELDNAME},
        "name",
    )
    if existing:
        # Update position only — don't touch user choices
        doc = frappe.get_doc("Custom Field", existing)
        if doc.insert_after != insert_after:
            doc.insert_after = insert_after
            doc.save(ignore_permissions=True)
            print(f"  Updated existing field (re-positioned after {insert_after})")
        else:
            print(f"  Custom field already exists — skipping")
        return

    doc = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": DOCTYPE,
        "fieldname": FIELDNAME,
        "label": "Employment Type",
        "fieldtype": "Link",
        "options": "Employment Type",
        "insert_after": insert_after,
        "description": (
            "If set, the 'Get Employees' button will only include employees "
            "with this Employment Type (e.g. Labour vs Full-time)."
        ),
        "no_copy": 0,
        "allow_on_submit": 0,
        "in_list_view": 0,
        "translatable": 0,
    })
    doc.insert(ignore_permissions=True)
    print(f"  Created field: {DOCTYPE}.{FIELDNAME}")
