# Copyright (c) 2026, Tripod Mena
# On Employee save: apply the LATEST transfer row (by transfer_date) to the
# employee's current Location, Region and Budget Unit.
# Cost apportioning for mid-month transfers is done in the CTC Budget Summary
# report — this only keeps the CURRENT position in sync.

import frappe
from frappe.utils import getdate

# Which region a budget unit belongs to. Logistics/Admin exist in BOTH regions,
# so they are deliberately absent here: those keep the employee's own region.
UNIT_REGION = {
    "Fit Out UAE": "UAE",
    "Dubai Production": "UAE",
    "Dubai Office": "UAE",
    "KSA Office": "KSA",
    "KSA National": "KSA",
    "KSA Production": "KSA",
    "KSA Fit Out": "KSA",
    "Tap Gulf": "KSA",
}


def latest_transfer(doc):
    """Return the transfer row with the newest transfer_date, or None."""
    rows = [r for r in (doc.get("custom_transfer_log") or []) if r.get("transfer_date")]
    if not rows:
        return None
    return sorted(rows, key=lambda r: getdate(r.transfer_date))[-1]


def apply_latest_transfer(doc, method=None):
    row = latest_transfer(doc)
    if not row:
        return

    if row.get("to_location"):
        doc.location = row.to_location

    if row.get("to_budget_unit"):
        doc.custom_budget_unit = row.to_budget_unit
        region = UNIT_REGION.get(row.to_budget_unit)
        if region:
            doc.custom_region = region
