# Copyright (c) 2026, Tripod Mena
# Adds a read-only "Application Link" field on Job Opening that a client
# script auto-fills on save, so HR can copy it straight to LinkedIn.
# Idempotent: safe on every migrate.

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install():
    fields = {
        "Job Opening": [
            {
                "fieldname": "custom_application_link",
                "label": "Application Link",
                "fieldtype": "Small Text",
                "insert_after": "job_application_route",
                "read_only": 1,
                "description": "Auto-generated public application link. Copy and paste on LinkedIn or share directly.",
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)
    frappe.db.commit()
