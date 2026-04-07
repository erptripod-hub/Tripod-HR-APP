import frappe


@frappe.whitelist()
def get_guidelines():
	"""Return all Appointment Guideline records for the current user."""
	try:
		records = frappe.get_all(
			"Appointment Guideline",
			fields=["name", "title", "department", "effective_date", "status", "guideline_file"],
			filters={"status": ["!=", "Archived"]},
			order_by="effective_date desc",
		)
		return records
	except Exception as e:
		frappe.log_error(f"ESS Guidelines Error: {str(e)}", "ESS Guidelines Page")
		return []


@frappe.whitelist()
def get_policies():
	"""Return all Company Policy records grouped by department."""
	try:
		records = frappe.get_all(
			"Company Policy",
			fields=[
				"name",
				"policy_name",
				"department",
				"version",
				"status",
				"last_reviewed",
				"next_review_date",
				"applicable_roles",
				"summary",
				"policy_document",
			],
			filters={"status": ["!=", "Archived"]},
			order_by="department asc, policy_name asc",
		)
		return records
	except Exception as e:
		frappe.log_error(f"ESS Policies Error: {str(e)}", "ESS Guidelines Page")
		return []


@frappe.whitelist()
def get_file_content(file_url):
	"""
	Serve a private file for in-browser viewing only.
	Blocks direct download by returning the URL only if the user has read access.
	"""
	try:
		if not file_url:
			frappe.throw("No file URL provided")

		# Check user has at least Employee or ESS role
		allowed_roles = ["Employee", "Employee Self Service", "HR Manager", "HR User", "System Manager"]
		if not any(frappe.utils.has_common(allowed_roles, frappe.get_roles())):
			frappe.throw("Not permitted", frappe.PermissionError)

		# Find the file record
		file_doc = frappe.get_value(
			"File",
			{"file_url": file_url},
			["name", "file_url", "file_name", "is_private"],
			as_dict=True,
		)

		if not file_doc:
			frappe.throw("File not found")

		# Return a time-limited view URL (use Frappe's built-in file URL)
		return {
			"file_name": file_doc.file_name,
			"file_url": file_doc.file_url,
			"viewable": True,
		}

	except frappe.PermissionError:
		frappe.throw("You do not have permission to view this file")
	except Exception as e:
		frappe.log_error(f"ESS File View Error: {str(e)}", "ESS Guidelines Page")
		frappe.throw("Could not load file")
