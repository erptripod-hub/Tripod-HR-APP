# Copyright (c) 2026, Tripod and contributors
"""Site-side capture.

Wired through ``doc_events`` in hooks.py. Any save of a tracked artefact writes
a change log entry; any first insert also creates the registry record.

Every handler is defensive: a failure here must never block the user's save.
"""

import frappe
from frappe.utils import now_datetime

from tripod_hr.registry.core import describe, log_change, upsert_customization


def _skip():
	"""Hooks must stay out of the way during migrate, install and patches.

	Migration changes are captured by the snapshot diff instead, which is both
	faster and able to tell our changes apart from framework churn.
	"""
	flags = frappe.flags
	return bool(
		flags.get("in_migrate")
		or flags.get("in_install")
		or flags.get("in_install_app")
		or flags.get("in_patch")
		or flags.get("in_import")
		or flags.get("in_test")
		or flags.get("erp_registry_bulk")
	)


def _summarise(doc):
	"""Short human-readable line describing what changed on this save."""
	dt = doc.doctype

	if dt == "Custom Field":
		bits = []
		for f in ("fieldtype", "reqd", "hidden", "read_only", "depends_on", "fetch_from", "options"):
			val = doc.get(f)
			if val not in (None, "", 0):
				bits.append("{0}={1}".format(f, str(val)[:40]))
		return "{0} on {1} · {2}".format(doc.get("fieldname"), doc.get("dt"), ", ".join(bits[:4]) or "saved")

	if dt == "Property Setter":
		return "{0}.{1} → {2}".format(doc.get("doc_type"), doc.get("property"), str(doc.get("value"))[:60])

	if dt in ("Server Script", "Client Script"):
		body = doc.get("script") or ""
		return "{0} · {1} lines".format(doc.get("script_type") or dt, len(body.splitlines()))

	if dt == "Print Format":
		body = doc.get("html") or ""
		return "html body saved, {0} lines".format(len(body.splitlines()))

	if dt == "Workflow":
		return "{0} states, {1} transitions".format(
			len(doc.get("states") or []), len(doc.get("transitions") or []))

	if dt == "DocType":
		return "{0} fields, {1} permissions".format(
			len(doc.get("fields") or []), len(doc.get("permissions") or []))

	return "saved"


def _last_version_name(doc):
	"""Name of the Version row ERPNext just wrote, when there is one."""
	try:
		rows = frappe.get_all(
			"Version",
			filters={"ref_doctype": doc.doctype, "docname": doc.name},
			fields=["name"], order_by="creation desc", limit=1,
		)
		return rows[0].name if rows else None
	except Exception:
		return None


def _body_of(doc):
	"""The field worth snapshotting for rollback, when the artefact has one."""
	if doc.doctype in ("Server Script", "Client Script"):
		return doc.get("script")
	if doc.doctype == "Print Format":
		return doc.get("html")
	return None


def on_artefact_update(doc, method=None):
	"""Log a change against the registry record for this artefact."""
	if _skip():
		return
	try:
		info = describe(doc)
		if not info:
			return
		artefact_type, artefact_name, module, app, target = info

		cust = upsert_customization(
			artefact_type, artefact_name, module=module, app=app,
			target_doctype=target, created_by=doc.get("owner"), source="Site",
		)
		log_change(
			cust, artefact_type, artefact_name, _summarise(doc),
			source="Site",
			reference=_last_version_name(doc),
			changed_by=frappe.session.user,
			target_doctype=target,
			new_value=_body_of(doc),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ERP registry: on_artefact_update")


def on_artefact_insert(doc, method=None):
	"""Create the registry record the moment a new customization appears."""
	if _skip():
		return
	try:
		info = describe(doc)
		if not info:
			return
		artefact_type, artefact_name, module, app, target = info

		cust = upsert_customization(
			artefact_type, artefact_name, module=module, app=app,
			target_doctype=target, created_by=frappe.session.user, source="Site",
		)
		log_change(
			cust, artefact_type, artefact_name, "created on site",
			source="Site", changed_by=frappe.session.user, target_doctype=target,
			new_value=_body_of(doc),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ERP registry: on_artefact_insert")


def on_artefact_trash(doc, method=None):
	"""Mark the registry record inactive rather than deleting history."""
	if _skip():
		return
	try:
		info = describe(doc)
		if not info:
			return
		artefact_type, artefact_name = info[0], info[1]
		key = "{0}::{1}".format(artefact_type, artefact_name)
		cust = frappe.db.get_value("ERP Customization", {"source_key": key}, "name")
		if not cust:
			return
		frappe.db.set_value("ERP Customization", cust, "is_active", 0, update_modified=False)
		log_change(cust, artefact_type, artefact_name, "deleted from site",
		           source="Site", changed_by=frappe.session.user)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ERP registry: on_artefact_trash")


def nightly_sync():
	"""Safety net for anything the hooks missed — bench-deployed code, direct SQL,
	or a save that errored before the hook ran. Compares Version rows written since
	the last run against the registry."""
	try:
		from tripod_hr.registry.discovery import run_discovery
		run_discovery(log_new=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ERP registry: nightly_sync")
