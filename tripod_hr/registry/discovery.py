# Copyright (c) 2026, Tripod and contributors
"""Discovery scan.

Walks the live site, finds every artefact belonging to a custom app plus every
non-standard print format / custom field / property setter, and makes sure each
has a registry record. Records it creates land in ``Needs Names``.

Safe to run repeatedly — existing records are matched on ``source_key`` and left
alone. Run read-only first with ``preview()``.
"""

import frappe
from frappe.utils import now_datetime

from tripod_hr.registry.core import (
	APP_SCOPED_DOCTYPES,
	app_for_module,
	get_custom_apps,
	is_custom_app,
	log_change,
	source_key,
	upsert_customization,
)


def _collect():
	"""Return a list of dicts describing every artefact that belongs in the register."""
	found = []
	custom_apps = set(get_custom_apps())

	# Modules owned by our apps, resolved once.
	module_app = {}
	for row in frappe.get_all("Module Def", fields=["name", "app_name"]):
		module_app[row.name] = row.app_name
	our_modules = [m for m, a in module_app.items() if a in custom_apps]

	# 1. App-scoped artefacts: DocType, Report, Page
	for dt in APP_SCOPED_DOCTYPES:
		if not our_modules:
			break
		fields = ["name", "module", "modified", "owner"]
		if dt == "Report":
			fields.append("ref_doctype")
		try:
			rows = frappe.get_all(dt, filters={"module": ["in", our_modules]}, fields=fields)
		except Exception:
			continue
		for r in rows:
			found.append({
				"artefact_type": dt,
				"artefact_name": r.name,
				"module": r.module,
				"app": module_app.get(r.module),
				"target_doctype": r.get("ref_doctype"),
				"owner": r.owner,
				"modified": r.modified,
			})

	# 2. Custom Field and Property Setter — customizations by definition
	for dt, target_field in (("Custom Field", "dt"), ("Property Setter", "doc_type")):
		try:
			rows = frappe.get_all(dt, fields=["name", "module", target_field, "modified", "owner"])
		except Exception:
			continue
		for r in rows:
			found.append({
				"artefact_type": dt,
				"artefact_name": r.name,
				"module": r.module,
				"app": app_for_module(r.module),
				"target_doctype": r.get(target_field),
				"owner": r.owner,
				"modified": r.modified,
			})

	# 3. Scripts, workflows, notifications, web forms, dashboard charts
	for dt in ("Server Script", "Client Script", "Workflow", "Notification",
	           "Dashboard Chart", "Web Form"):
		if not frappe.db.exists("DocType", dt):
			continue
		try:
			rows = frappe.get_all(dt, fields=["name", "module", "modified", "owner"])
		except Exception:
			continue
		for r in rows:
			found.append({
				"artefact_type": dt,
				"artefact_name": r.name,
				"module": r.module,
				"app": app_for_module(r.module),
				"target_doctype": None,
				"owner": r.owner,
				"modified": r.modified,
			})

	# 4. Print formats — non-standard ones live only in the DB, so the register
	#    is their sole version history.
	try:
		rows = frappe.get_all(
			"Print Format",
			fields=["name", "module", "doc_type", "standard", "modified", "owner"],
		)
	except Exception:
		rows = []
	for r in rows:
		app = app_for_module(r.module)
		if r.standard == "Yes" and not is_custom_app(app):
			continue
		found.append({
			"artefact_type": "Print Format",
			"artefact_name": r.name,
			"module": r.module,
			"app": app,
			"target_doctype": r.doc_type,
			"owner": r.owner,
			"modified": r.modified,
		})

	return found


@frappe.whitelist()
def preview():
	"""Read-only. Counts what a scan would create, grouped by app and type."""
	found = _collect()
	existing = set(
		frappe.get_all("ERP Customization", pluck="source_key")
	)
	by_app = {}
	by_type = {}
	new_count = 0
	for f in found:
		key = source_key(f["artefact_type"], f["artefact_name"])
		is_new = key not in existing
		if is_new:
			new_count += 1
		app = f.get("app") or "(no app)"
		by_app.setdefault(app, {"total": 0, "new": 0})
		by_app[app]["total"] += 1
		by_app[app]["new"] += 1 if is_new else 0
		by_type.setdefault(f["artefact_type"], {"total": 0, "new": 0})
		by_type[f["artefact_type"]]["total"] += 1
		by_type[f["artefact_type"]]["new"] += 1 if is_new else 0

	return {
		"total_found": len(found),
		"already_registered": len(found) - new_count,
		"would_create": new_count,
		"by_app": by_app,
		"by_type": by_type,
	}


@frappe.whitelist()
def run_discovery(log_new=False):
	"""Create registry records for anything not already present."""
	found = _collect()
	created = 0
	for f in found:
		key = source_key(f["artefact_type"], f["artefact_name"])
		if frappe.db.get_value("ERP Customization", {"source_key": key}, "name"):
			continue
		cust = upsert_customization(
			f["artefact_type"], f["artefact_name"],
			module=f.get("module"), app=f.get("app"),
			target_doctype=f.get("target_doctype"),
			created_by=f.get("owner"), source="Discovery",
		)
		created += 1
		if log_new:
			log_change(cust, f["artefact_type"], f["artefact_name"],
			           "found by discovery scan", source="Discovery",
			           changed_by=f.get("owner") or "Administrator")
		if created % 100 == 0:
			frappe.db.commit()

	frappe.db.commit()
	return {"scanned": len(found), "created": created, "at": str(now_datetime())}


@frappe.whitelist()
def bulk_set_approval(names, requested_by, approved_by, approval_reference=None):
	"""Assign the two names to many records at once — for clearing the initial backlog."""
	if isinstance(names, str):
		names = frappe.parse_json(names)

	frappe.flags.erp_registry_bulk = True
	done = 0
	for n in names:
		status = frappe.db.get_value("ERP Customization", n, "registration_status")
		if status == "Registered":
			continue
		doc = frappe.get_doc("ERP Customization", n)
		doc.requested_by = requested_by
		doc.approved_by = approved_by
		if approval_reference:
			doc.approval_reference = approval_reference
		doc.save(ignore_permissions=True)
		done += 1
		if done % 50 == 0:
			frappe.db.commit()

	frappe.db.commit()
	return {"updated": done, "skipped": len(names) - done}
