# Copyright (c) 2026, Tripod Group and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, formatdate


class LeaveBlackout(Document):
    def validate(self):
        self.validate_dates()
        self.validate_duplicate_employees()

    def validate_dates(self):
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_("From Date cannot be after To Date"))

    def validate_duplicate_employees(self):
        seen = set()
        for row in self.allowed_employees:
            if row.employee in seen:
                frappe.throw(
                    _("Employee {0} is listed more than once in Allowed Employees").format(
                        frappe.bold(row.employee)
                    )
                )
            seen.add(row.employee)


def validate_leave_blackout(doc, method=None):
    """Called from Leave Application validate hook.

    Blocks a NEW leave application when its dates overlap an active blackout
    for the same company and leave type. Employees listed in the blackout's
    Allowed Employees table are exempt. Already-submitted leave applications
    are never affected, since this only runs when a document is being saved
    or submitted.
    """
    if not doc.get("leave_type") or not doc.get("from_date") or not doc.get("to_date"):
        return

    company = doc.get("company")
    if not company:
        company = frappe.db.get_value("Employee", doc.employee, "company")
    if not company:
        return

    blackouts = frappe.get_all(
        "Leave Blackout",
        filters={
            "docstatus": 1,
            "company": company,
            "leave_type": doc.leave_type,
            "from_date": ["<=", doc.to_date],
            "to_date": [">=", doc.from_date],
        },
        fields=["name", "from_date", "to_date", "reason"],
    )

    if not blackouts:
        return

    for blackout in blackouts:
        allowed = frappe.get_all(
            "Leave Blackout Allowed Employee",
            filters={"parent": blackout.name, "employee": doc.employee},
            limit=1,
        )
        if allowed:
            continue

        message = _("{0} cannot be applied between {1} and {2}.").format(
            frappe.bold(doc.leave_type),
            frappe.bold(formatdate(blackout.from_date)),
            frappe.bold(formatdate(blackout.to_date)),
        )

        if blackout.reason:
            message += "<br>" + _("Reason: {0}").format(blackout.reason)

        message += "<br><br>" + _(
            "Adjust your dates to fall outside this period, or contact HR."
        )

        frappe.throw(message, title=_("Leave Blackout"))
