# Copyright (c) 2026, Tripod and contributors
"""GitHub push receiver.

Endpoint: ``/api/method/tripod_hr.registry.git_hook.receive``

Set the same secret in the GitHub webhook config and in site_config.json as
``erp_registry_webhook_secret``. Payload file paths are mapped back to registry
records so a push shows up without anyone typing anything.

The snapshot diff in ``migration.py`` remains the source of truth for site
state; this feed exists to give changes an author and a commit reference.
"""

import hashlib
import hmac
import json
import re

import frappe

from tripod_hr.registry.core import (
	app_for_module,
	log_change,
	source_key,
	upsert_customization,
)

# app/app/doctype/some_doctype/some_doctype.py  ->  DocType: Some Doctype
PATH_PATTERNS = (
	(re.compile(r"/doctype/([^/]+)/"), "DocType"),
	(re.compile(r"/report/([^/]+)/"), "Report"),
	(re.compile(r"/page/([^/]+)/"), "Page"),
	(re.compile(r"/print_format/([^/]+)/"), "Print Format"),
	(re.compile(r"/workflow/([^/]+)/"), "Workflow"),
	(re.compile(r"/dashboard_chart/([^/]+)/"), "Dashboard Chart"),
	(re.compile(r"/notification/([^/]+)/"), "Notification"),
	(re.compile(r"/web_form/([^/]+)/"), "Web Form"),
)


def _verify(raw_body, signature):
	secret = frappe.conf.get("erp_registry_webhook_secret")
	if not secret:
		return False
	if not signature or not signature.startswith("sha256="):
		return False
	digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
	return hmac.compare_digest("sha256=" + digest, signature)


def _titleise(slug):
	return " ".join(w.capitalize() for w in slug.replace("-", "_").split("_") if w)


def map_path(path):
	"""Resolve a changed file path to (artefact_type, artefact_name) or None."""
	normalised = "/" + path.strip("/")
	for pattern, artefact_type in PATH_PATTERNS:
		match = pattern.search(normalised)
		if match:
			slug = match.group(1)
			guess = _titleise(slug)
			# Prefer the real record name when it exists on this site.
			if frappe.db.exists(artefact_type, guess):
				return artefact_type, guess
			rows = frappe.get_all(
				artefact_type,
				filters={"name": ["like", "%{0}%".format(guess)]},
				pluck="name", limit=1,
			)
			return artefact_type, (rows[0] if rows else guess)
	return None


@frappe.whitelist(allow_guest=True)
def receive():
	"""GitHub push webhook."""
	try:
		raw = frappe.request.get_data() if frappe.request else b""
		signature = frappe.get_request_header("X-Hub-Signature-256")
		if not _verify(raw, signature):
			frappe.local.response["http_status_code"] = 401
			return {"error": "invalid signature"}

		payload = json.loads(raw.decode("utf-8") or "{}")
		if not payload.get("commits"):
			return {"ok": True, "logged": 0}

		repo = (payload.get("repository") or {}).get("name") or ""
		logged = 0

		for commit in payload.get("commits", []):
			author = (commit.get("author") or {}).get("name") or "git"
			short = (commit.get("id") or "")[:7]
			message = (commit.get("message") or "").splitlines()[0][:140]
			touched = set()
			touched.update(commit.get("added") or [])
			touched.update(commit.get("modified") or [])
			touched.update(commit.get("removed") or [])

			seen = set()
			for path in touched:
				mapped = map_path(path)
				if not mapped:
					continue
				artefact_type, artefact_name = mapped
				key = source_key(artefact_type, artefact_name)
				if key in seen:
					continue
				seen.add(key)

				module = frappe.db.get_value(artefact_type, artefact_name, "module") \
					if frappe.db.exists(artefact_type, artefact_name) else None
				cust = upsert_customization(
					artefact_type, artefact_name, module=module,
					app=app_for_module(module) or repo, source="Git",
				)
				log_change(
					cust, artefact_type, artefact_name,
					message or "pushed",
					source="Git", reference="commit " + short, changed_by=author,
				)
				logged += 1

		frappe.db.commit()
		return {"ok": True, "logged": logged}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ERP registry: git webhook")
		frappe.local.response["http_status_code"] = 500
		return {"error": "see Error Log"}
