# Copyright (c) 2026, Tripod and contributors
"""Whitelisted methods behind the ERP Customization Register page."""

import frappe

from tripod_hr.registry.core import get_site_name


@frappe.whitelist()
def get_dashboard(site=None, module=None, status=None, search=None, limit=500):
	"""Everything the register page needs in one round trip."""
	limit = int(limit or 500)
	filters = {}
	if site and site != "all":
		filters["site_name"] = site
	if module:
		filters["module"] = module
	if status in ("Registered", "Needs Names"):
		filters["registration_status"] = status

	or_filters = None
	if search:
		like = "%{0}%".format(search)
		or_filters = [
			["customization_name", "like", like],
			["app_name", "like", like],
			["module", "like", like],
		]

	rows = frappe.get_all(
		"ERP Customization",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "customization_name", "module", "app_name", "artefact_type",
			"site_name", "registration_status", "requested_by", "approved_by",
			"approved_on", "change_count", "last_changed_on", "last_changed_by",
			"last_change_source", "is_active",
		],
		order_by="registration_status asc, last_changed_on desc",
		limit_page_length=limit,
	)

	scope = {}
	if site and site != "all":
		scope["site_name"] = site
	total = frappe.db.count("ERP Customization", scope)
	needs = frappe.db.count(
		"ERP Customization", dict(scope, registration_status="Needs Names"))

	feed_filters = dict(scope)
	feed = frappe.get_all(
		"ERP Change Log",
		filters=feed_filters,
		fields=["name", "customization", "change_source", "changed_by", "change_time",
		        "artefact_type", "artefact_name", "reference", "change_detail", "site_name"],
		order_by="change_time desc",
		limit_page_length=40,
	)

	cust_names = {}
	for f in feed:
		if f.customization and f.customization not in cust_names:
			cust_names[f.customization] = frappe.db.get_value(
				"ERP Customization", f.customization, "customization_name") or f.customization
	for f in feed:
		f["customization_title"] = cust_names.get(f.customization, f.artefact_name)

	coverage = {}
	for r in frappe.get_all(
		"ERP Customization", filters=scope,
		fields=["module", "registration_status"], limit_page_length=0
	):
		mod = r.module or "(unassigned)"
		coverage.setdefault(mod, {"total": 0, "registered": 0})
		coverage[mod]["total"] += 1
		if r.registration_status == "Registered":
			coverage[mod]["registered"] += 1

	return {
		"rows": rows,
		"feed": feed,
		"coverage": coverage,
		"kpi": {
			"total": total,
			"registered": total - needs,
			"needs_names": needs,
			"changes_week": _changes_since(7, scope),
			"changes_today": _changes_since(1, scope),
		},
		"sites": sorted({r for r in frappe.get_all(
			"ERP Customization", pluck="site_name", limit_page_length=0) if r}),
		"current_site": get_site_name(),
	}


def _changes_since(days, scope):
	filters = dict(scope)
	filters["change_time"] = [">=", frappe.utils.add_days(frappe.utils.nowdate(), -days)]
	return frappe.db.count("ERP Change Log", filters)


@frappe.whitelist()
def get_customization(name):
	"""Full detail for the drawer: approval, artefacts, change history."""
	doc = frappe.get_doc("ERP Customization", name)
	history = frappe.get_all(
		"ERP Change Log",
		filters={"customization": name},
		fields=["name", "change_source", "changed_by", "change_time",
		        "artefact_type", "artefact_name", "reference", "change_detail"],
		order_by="change_time desc",
		limit_page_length=100,
	)
	return {
		"doc": doc.as_dict(),
		"history": history,
		"users": frappe.get_all(
			"User", filters={"enabled": 1, "user_type": "System User"},
			fields=["name", "full_name"], limit_page_length=0),
	}
