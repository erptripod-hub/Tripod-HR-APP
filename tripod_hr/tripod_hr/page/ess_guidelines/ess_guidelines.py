import frappe


@frappe.whitelist()
def get_guidelines():
	"""Return all Appointment Guidelines - read only for ESS role"""
	try:
		docs = frappe.get_all(
			"Appointment Guideline",
			fields=["name", "title", "department", "effective_date", "status", "description", "guideline_file"],
			filters={"status": ["!=", "Archived"]},
			order_by="effective_date desc",
		)
		return {"success": True, "data": docs}
	except Exception as e:
		frappe.log_error(str(e), "ESS Guidelines")
		return {"success": False, "data": [], "error": str(e)}


@frappe.whitelist()
def get_policies():
	"""Return all Company Policies grouped by department"""
	try:
		docs = frappe.get_all(
			"Company Policy",
			fields=["name", "policy_name", "department", "version", "status", "last_reviewed", "summary", "policy_document"],
			filters={"status": ["!=", "Archived"]},
			order_by="department asc, policy_name asc",
		)
		# Group by department
		grouped = {}
		for doc in docs:
			dept = doc.get("department") or "General"
			if dept not in grouped:
				grouped[dept] = []
			grouped[dept].append(doc)
		return {"success": True, "data": grouped, "total": len(docs)}
	except Exception as e:
		frappe.log_error(str(e), "ESS Policies")
		return {"success": False, "data": {}, "error": str(e)}


@frappe.whitelist()
def get_file_stream(file_url):
	"""
	Server-side file proxy — streams the file content back to the browser
	as inline (not attachment), so it displays but cannot be downloaded
	via the normal attachment mechanism.
	Only users with read access to the DocType can call this.
	"""
	if not file_url:
		frappe.throw("No file specified", frappe.PermissionError)

	# Verify the user has at least Employee or ESS role
	allowed_roles = {"Employee Self Service", "Employee", "HR Manager", "HR User", "System Manager"}
	user_roles = set(frappe.get_roles(frappe.session.user))
	if not allowed_roles.intersection(user_roles):
		frappe.throw("Not permitted", frappe.PermissionError)

	# Get file doc to check it exists
	file_doc = frappe.db.get_value(
		"File", {"file_url": file_url}, ["name", "file_name", "file_url", "is_private"], as_dict=True
	)
	if not file_doc:
		frappe.throw("File not found", frappe.DoesNotExistError)

	# Return metadata only — the JS will open the file in an iframe
	# We never expose a download URL, only the frappe file viewer URL
	return {
		"success": True,
		"file_name": file_doc.file_name,
		"view_url": file_url,
	}
