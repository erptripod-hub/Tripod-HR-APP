"""
Install custom fields on Leave Application for tracking leave extensions
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install():
    """Create custom fields for Leave Application extension tracking"""
    
    custom_fields = {
        "Leave Application": [
            {
                "fieldname": "custom_extension_section",
                "label": "Extension Details",
                "fieldtype": "Section Break",
                "insert_after": "follow_via_email",
                "collapsible": 1,
                "depends_on": "eval:doc.custom_original_to_date"
            },
            {
                "fieldname": "custom_original_to_date",
                "label": "Original To Date",
                "fieldtype": "Date",
                "insert_after": "custom_extension_section",
                "read_only": 1,
                "description": "Original return date before extension"
            },
            {
                "fieldname": "custom_extension_reason",
                "label": "Extension Reason",
                "fieldtype": "Small Text",
                "insert_after": "custom_original_to_date",
                "read_only": 1
            },
            {
                "fieldname": "custom_cb_extension",
                "fieldtype": "Column Break",
                "insert_after": "custom_extension_reason"
            },
            {
                "fieldname": "custom_extended_on",
                "label": "Extended On",
                "fieldtype": "Datetime",
                "insert_after": "custom_cb_extension",
                "read_only": 1
            },
            {
                "fieldname": "custom_extended_by",
                "label": "Extended By",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "custom_extended_on",
                "read_only": 1
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    print("Leave Application extension fields installed successfully")
