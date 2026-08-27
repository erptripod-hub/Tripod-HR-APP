# Copyright (c) 2026, Tripod Mena
# Adds the Transfer & Cost Split section on Employee:
#   - custom_transfer_log   (Table -> Employee Transfer Log)
#   - custom_cost_split_pct (Percent) + custom_cost_split_unit (Select)
# Idempotent: safe on every migrate.

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

UNIT_OPTIONS = (
    "\nFit Out UAE\nDubai Production\nDubai Office\nKSA Office\nKSA National"
    "\nKSA Production\nKSA Fit Out\nLogistics\nAdmin\nTap Gulf"
)


def install():
    fields = {
        "Employee": [
            {
                "fieldname": "custom_transfer_section",
                "label": "Transfer & Cost Split",
                "fieldtype": "Section Break",
                "insert_after": "custom_gratuity_monthly",
                "collapsible": 1,
            },
            {
                "fieldname": "custom_transfer_log",
                "label": "Transfer Log",
                "fieldtype": "Table",
                "options": "Employee Transfer Log",
                "insert_after": "custom_transfer_section",
                "description": "Add a row when the employee moves. On save the current Location, Region and Budget Unit are set from the latest transfer.",
            },
            {
                "fieldname": "custom_cost_split_cb",
                "fieldtype": "Column Break",
                "insert_after": "custom_transfer_log",
            },
            {
                "fieldname": "custom_cost_split_pct",
                "label": "Cost Split %",
                "fieldtype": "Percent",
                "insert_after": "custom_cost_split_cb",
                "description": "Share of MONTHLY SALARY moved to the split budget unit (e.g. 50 for a 50/50 split). Leave blank for no split.",
            },
            {
                "fieldname": "custom_cost_split_unit",
                "label": "Cost Split Budget Unit",
                "fieldtype": "Select",
                "options": UNIT_OPTIONS,
                "insert_after": "custom_cost_split_pct",
                "description": "The other budget unit that carries the split share of monthly salary.",
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)
    frappe.db.commit()
    frappe.logger().info("[install_transfer_fields] transfer + cost split fields installed")
