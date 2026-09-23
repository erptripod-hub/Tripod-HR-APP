# Copyright (c) 2026, Tripod Mena
# Keeps a Hiring Plan row's status in sync with the Job Opening created from it:
#   - Job Opening created (with custom_hiring_plan set) -> plan "In Progress"
#   - Job Opening status set to a filled/closed state    -> plan "Filled"
# Only moves the plan forward; never overrides Cancelled.

import frappe

FILLED_STATES = {"Filled", "Closed"}


def _set_plan_status(hiring_plan, new_status):
    if not hiring_plan:
        return
    current = frappe.db.get_value("Hiring Plan", hiring_plan, "status")
    if not current or current == "Cancelled":
        return
    if current == new_status:
        return
    # do not downgrade a Filled plan back to In Progress
    if current == "Filled" and new_status == "In Progress":
        return
    frappe.db.set_value("Hiring Plan", hiring_plan, "status", new_status)


def job_opening_after_insert(doc, method=None):
    hp = doc.get("custom_hiring_plan")
    if hp:
        _set_plan_status(hp, "In Progress")


def job_opening_on_update(doc, method=None):
    hp = doc.get("custom_hiring_plan")
    if not hp:
        return
    if (doc.get("status") or "") in FILLED_STATES:
        _set_plan_status(hp, "Filled")
