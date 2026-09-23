# Copyright (c) 2026, Tripod Mena
# Job Applicant additions:
#   - custom fields: Years of Experience, Notice Period, Expected Salary
#   - adds "Shortlisted" to the status options
# Idempotent: safe on every migrate.

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install():
    fields = {
        "Job Applicant": [
            {
                "fieldname": "custom_experience_section",
                "label": "Experience & Availability",
                "fieldtype": "Section Break",
                "insert_after": "phone_number",
                "collapsible": 0,
            },
            {
                "fieldname": "custom_years_experience",
                "label": "Years of Experience (same field)",
                "fieldtype": "Int",
                "insert_after": "custom_experience_section",
            },
            {
                "fieldname": "custom_notice_period",
                "label": "Notice Period",
                "fieldtype": "Data",
                "insert_after": "custom_years_experience",
            },
            {
                "fieldname": "custom_expected_salary",
                "label": "Expected Salary (Monthly)",
                "fieldtype": "Currency",
                "insert_after": "custom_notice_period",
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)

    # add "Shortlisted" to the status Select options via property setter
    meta = frappe.get_meta("Job Applicant")
    status_field = meta.get_field("status")
    if status_field:
        options = [o.strip() for o in (status_field.options or "").split("\n")]
        if "Shortlisted" not in options:
            options.append("Shortlisted")
            frappe.make_property_setter({
                "doctype": "Job Applicant",
                "fieldname": "status",
                "property": "options",
                "value": "\n".join(options),
                "property_type": "Text",
            }, is_system_generated=False)

    frappe.db.commit()
