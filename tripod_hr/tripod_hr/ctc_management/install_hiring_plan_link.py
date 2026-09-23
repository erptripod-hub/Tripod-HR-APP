# Copyright (c) 2026, Tripod Mena
# Links Job Opening back to Hiring Plan so a plan row can spawn an opening
# (Connections + button) and the plan status can follow the opening.
# Idempotent: safe on every migrate.

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install():
    fields = {
        "Job Opening": [
            {
                "fieldname": "custom_hiring_plan",
                "label": "Hiring Plan",
                "fieldtype": "Link",
                "options": "Hiring Plan",
                "insert_after": "custom_application_link",
                "read_only": 1,
                "description": "The Hiring Plan position this opening was created from.",
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)
    frappe.db.commit()
