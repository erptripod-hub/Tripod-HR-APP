import json

import frappe
from frappe.model.document import Document


class HiringPlan(Document):
    pass


@frappe.whitelist()
def get_list_totals(filters=None):
    """Totals for whatever the user has filtered in the Hiring Plan list view.

    Used by hiring_plan_list.js to show head count / monthly salary / monthly CTC
    directly above the list, so management can filter (e.g. Designation = Driver)
    and immediately see how many people and what it costs.
    """
    if isinstance(filters, str):
        filters = json.loads(filters or "[]")

    rows = frappe.get_all(
        "Hiring Plan",
        filters=filters or [],
        fields=["monthly_salary", "total_ctc"],
        limit_page_length=0,
    )

    salary = sum(float(r.get("monthly_salary") or 0) for r in rows)
    ctc = sum(float(r.get("total_ctc") or 0) for r in rows)

    return {
        "count": len(rows),
        "salary": salary,
        "ctc": ctc,
        "annual_ctc": ctc * 12,
    }
