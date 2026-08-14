# Copyright (c) 2026, Tripod and contributors
"""Migration diff.

``before_migrate`` writes a full inventory snapshot; ``after_migrate`` takes a
second one and compares. Three-way triage decides what happens to each finding:

  new object in a custom app   -> registry record created (Needs Names)
  changed object we already own -> change log entry appended
  framework object              -> migration report only, never the register

Watchlist objects are pulled out of the framework bucket and raised as alerts,
because v15 patches are known to undo fixes such as the System Manager DocPerms
strip on HR and Payroll doctypes.
"""

import hashlib
import json
import os

import frappe
from frappe.utils import now_datetime

from tripod_hr.registry.core import (
	APP_SCOPED_DOCTYPES,
	WATCHLIST,
	app_for_module,
	is_custom_app,
	log_change,
	source_key,
	upsert_customization,
)

SNAPSHOT_FILE = "erp_registry_migration_snapshot.json"

INVENTORY_DOCTYPES = (
	"DocType", "Report", "Page", "Print Format", "Custom Field",
	"Property Setter", "Server Script", "Client Script", "Workflow",
	"Notification", "Dashboard Chart", "Web Form",
)


def _snapshot_path():
	folder = frappe.get_site_path("private", "files")
	if not os.path.exists(folder):
		os.makedirs(folder)
	return os.path.join(folder, SNAPSHOT_FILE)


def _fingerprint(dt, name):
	"""Hash of the object's definition, so a real change is distinguishable from
	a bumped modified stamp."""
	try:
		doc = frappe.get_doc(dt, name)
		payload = json.dumps(doc.as_dict(no_nulls=True), sort_keys=True, default=str)
	except Exception:
		return ""
	return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def build_inventory(with_fingerprint=False):
	"""Map of ``Type::name`` -> metadata for every object we care about."""
	inv = {}
	for dt in INVENTORY_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			continue
		fields = ["name", "modified"]
		meta_fields = [f.fieldname for f in frappe.get_meta(dt).fields]
		if "module" in meta_fields:
			fields.append("module")
		try:
			rows = frappe.get_all(dt, fields=fields)
		except Exception:
			continue
		for r in rows:
			key = source_key(dt, r.name)
			module = r.get("module")
			inv[key] = {
				"type": dt,
				"name": r.name,
				"module": module,
				"app": app_for_module(module),
				"modified": str(r.modified),
				"hash": _fingerprint(dt, r.name) if with_fingerprint else "",
			}
	return inv


@frappe.whitelist()
def take_snapshot():
	"""Called by ``before_migrate``. Writes the pre-migration inventory to disk."""
	try:
		inv = build_inventory(with_fingerprint=True)
		with open(_snapshot_path(), "w") as fh:
			json.dump({"at": str(now_datetime()), "inventory": inv}, fh)
		return {"objects": len(inv)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ERP registry: take_snapshot")
		return {"objects": 0}


def _load_snapshot():
	path = _snapshot_path()
	if not os.path.exists(path):
		return None
	try:
		with open(path) as fh:
			return json.load(fh)
	except Exception:
		return None


def _is_watchlisted(entry):
	for w in WATCHLIST:
		if entry.get("type") == w.get("doctype"):
			return w.get("note")
	return None


@frappe.whitelist()
def diff_after_migrate():
	"""Called by ``after_migrate``. Compares against the snapshot and triages."""
	try:
		snap = _load_snapshot()
		if not snap:
			return {"skipped": "no snapshot on disk"}

		before = snap.get("inventory") or {}
		after = build_inventory(with_fingerprint=True)

		added_ours, added_framework = [], []
		changed_ours, changed_framework = [], []
		removed = []
		alerts = []

		for key, entry in after.items():
			ours = is_custom_app(entry.get("app")) or entry["type"] in (
				"Custom Field", "Property Setter", "Print Format")
			if key not in before:
				if ours:
					added_ours.append(entry)
				else:
					added_framework.append(entry)
					note = _is_watchlisted(entry)
					if note:
						alerts.append({"entry": entry, "note": note, "kind": "added"})
			elif before[key].get("hash") and before[key]["hash"] != entry.get("hash"):
				if ours:
					changed_ours.append(entry)
				else:
					changed_framework.append(entry)
					note = _is_watchlisted(entry)
					if note:
						alerts.append({"entry": entry, "note": note, "kind": "changed"})

		for key, entry in before.items():
			if key not in after:
				removed.append(entry)

		# New objects in our apps become registry records needing the two names.
		for entry in added_ours:
			if entry["type"] in APP_SCOPED_DOCTYPES or entry["type"] in (
				"Custom Field", "Property Setter", "Print Format",
				"Server Script", "Client Script", "Workflow",
			):
				cust = upsert_customization(
					entry["type"], entry["name"], module=entry.get("module"),
					app=entry.get("app"), source="Migration",
				)
				log_change(cust, entry["type"], entry["name"],
				           "added by migration", source="Migration",
				           changed_by="Administrator")

		# Changed objects we already own append to their existing history.
		for entry in changed_ours:
			key = source_key(entry["type"], entry["name"])
			cust = frappe.db.get_value("ERP Customization", {"source_key": key}, "name")
			if not cust:
				cust = upsert_customization(
					entry["type"], entry["name"], module=entry.get("module"),
					app=entry.get("app"), source="Migration",
				)
			log_change(cust, entry["type"], entry["name"],
			           "definition changed during migration", source="Migration",
			           changed_by="Administrator")

		# Removed objects are marked inactive, never deleted.
		for entry in removed:
			key = source_key(entry["type"], entry["name"])
			cust = frappe.db.get_value("ERP Customization", {"source_key": key}, "name")
			if cust:
				frappe.db.set_value("ERP Customization", cust, "is_active", 0,
				                    update_modified=False)
				log_change(cust, entry["type"], entry["name"],
				           "no longer present after migration", source="Migration",
				           changed_by="Administrator")

		result = {
			"at": str(now_datetime()),
			"added_ours": len(added_ours),
			"changed_ours": len(changed_ours),
			"removed": len(removed),
			"framework_added": len(added_framework),
			"framework_changed": len(changed_framework),
			"alerts": alerts,
		}

		frappe.cache().set_value("erp_registry_last_migration_diff", result, expires_in_sec=60 * 60 * 24 * 30)
		frappe.db.commit()
		return result
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ERP registry: diff_after_migrate")
		return {"error": "see Error Log"}


@frappe.whitelist()
def last_migration_diff():
	"""The most recent diff result, for the register page."""
	return frappe.cache().get_value("erp_registry_last_migration_diff") or {}
