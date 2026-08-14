# Copyright (c) 2026, Tripod and contributors
"""Core helpers for the ERP customization registry.

Identity: every tracked artefact resolves to a stable ``source_key`` of the form
``<Artefact Type>::<name>``. That key is what ties a live site object to its
registry record, and it is what lets the same code run on both sites.
"""

import frappe
from frappe.utils import now_datetime

# Apps that ship with the platform. Everything else is ours.
FRAMEWORK_APPS = {"frappe", "erpnext", "hrms", "payments", "webshop", "insights", "lms"}

# DocTypes whose records ARE customizations by definition.
TRACKED_DOCTYPES = (
	"Custom Field",
	"Property Setter",
	"Server Script",
	"Client Script",
	"Print Format",
	"Workflow",
	"Notification",
	"Dashboard Chart",
	"Web Form",
)

# DocTypes that are customizations only when they belong to a custom app.
APP_SCOPED_DOCTYPES = ("DocType", "Report", "Page")

# Objects we never want silently overwritten by a migration. Surfaced as alerts.
WATCHLIST = [
	{"doctype": "Custom DocPerm", "note": "System Manager DocPerms on HR/Payroll doctypes"},
	{"doctype": "Property Setter", "note": "Employee Advance account type"},
]


def get_custom_apps():
	"""Installed apps that are not framework apps."""
	try:
		installed = frappe.get_installed_apps()
	except Exception:
		installed = []
	return [a for a in installed if a not in FRAMEWORK_APPS]


def get_site_name():
	return frappe.local.site or frappe.conf.get("site_name") or "unknown"


def app_for_module(module):
	"""Resolve a Module Def to its owning app. Returns None when unknown."""
	if not module:
		return None
	try:
		return frappe.db.get_value("Module Def", module, "app_name")
	except Exception:
		return None


def is_custom_app(app):
	return bool(app) and app not in FRAMEWORK_APPS


def source_key(artefact_type, artefact_name):
	return "{0}::{1}".format(artefact_type, artefact_name)


def describe(doc):
	"""Return (artefact_type, artefact_name, module, app, target_doctype) for a
	tracked document, or None when the document is not a customization."""
	dt = doc.doctype

	if dt == "Custom Field":
		target = doc.get("dt")
		return ("Custom Field", doc.name, doc.get("module"), app_for_module(doc.get("module")), target)

	if dt == "Property Setter":
		target = doc.get("doc_type")
		return ("Property Setter", doc.name, doc.get("module"), app_for_module(doc.get("module")), target)

	if dt == "Server Script":
		return ("Server Script", doc.name, doc.get("module"), app_for_module(doc.get("module")), doc.get("reference_doctype"))

	if dt == "Client Script":
		return ("Client Script", doc.name, doc.get("module"), app_for_module(doc.get("module")), doc.get("dt"))

	if dt == "Print Format":
		# Standard=No print formats are always ours; they live in the DB, not git.
		if doc.get("standard") == "Yes":
			app = app_for_module(doc.get("module"))
			if not is_custom_app(app):
				return None
		return ("Print Format", doc.name, doc.get("module"), app_for_module(doc.get("module")), doc.get("doc_type"))

	if dt in ("Workflow", "Notification", "Dashboard Chart", "Web Form"):
		return (dt, doc.name, doc.get("module"), app_for_module(doc.get("module")), doc.get("document_type") or doc.get("doc_type"))

	if dt in APP_SCOPED_DOCTYPES:
		module = doc.get("module")
		app = app_for_module(module)
		if not is_custom_app(app):
			return None
		target = doc.get("ref_doctype") if dt == "Report" else None
		return (dt, doc.name, module, app, target)

	return None


def upsert_customization(artefact_type, artefact_name, module=None, app=None,
                         target_doctype=None, created_by=None, source="Site"):
	"""Find the registry record for an artefact, creating it if absent.

	New records are always created in ``Needs Names``. The two names are never
	asked for again once set.
	"""
	key = source_key(artefact_type, artefact_name)
	existing = frappe.db.get_value("ERP Customization", {"source_key": key}, "name")
	if existing:
		return existing

	doc = frappe.new_doc("ERP Customization")
	doc.customization_name = artefact_name
	doc.artefact_type = artefact_type
	doc.module = module or ""
	doc.app_name = app or ""
	doc.site_name = get_site_name()
	doc.source_key = key
	doc.auto_created = 1
	doc.is_active = 1
	doc.discovered_on = now_datetime()
	doc.last_change_source = source
	if created_by and frappe.db.exists("User", created_by):
		doc.requested_by = created_by
	doc.append("artefacts", {
		"artefact_type": artefact_type,
		"artefact_name": artefact_name,
		"app_name": app or "",
		"module": module or "",
		"target_doctype": target_doctype or "",
		"in_git": 1 if is_custom_app(app) else 0,
		"last_modified": now_datetime(),
		"last_modified_by": created_by or frappe.session.user,
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return doc.name


def log_change(customization, artefact_type, artefact_name, detail,
               source="Site", reference=None, changed_by=None,
               target_doctype=None, old_value=None, new_value=None):
	"""Append one entry to the change log and stamp the parent record."""
	entry = frappe.new_doc("ERP Change Log")
	entry.customization = customization
	entry.change_source = source
	entry.changed_by = changed_by or frappe.session.user
	entry.change_time = now_datetime()
	entry.site_name = get_site_name()
	entry.artefact_type = artefact_type
	entry.artefact_name = artefact_name
	entry.target_doctype = target_doctype or ""
	entry.reference = reference or ""
	entry.change_detail = detail
	entry.old_value = old_value
	entry.new_value = new_value
	entry.flags.ignore_permissions = True
	entry.insert(ignore_permissions=True)

	if customization:
		frappe.db.set_value("ERP Customization", customization, {
			"last_changed_on": entry.change_time,
			"last_changed_by": entry.changed_by,
			"last_change_source": source,
			"change_count": frappe.db.count("ERP Change Log", {"customization": customization}),
		}, update_modified=False)

	return entry.name
