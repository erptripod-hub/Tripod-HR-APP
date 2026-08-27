from . import __version__ as app_version

app_name = "tripod_hr"
app_title = "Tripod HR"
app_publisher = "Tripod"
app_description = "Custom HR Management App for Tripod - Performance Appraisals, Reviews and HR Workflows"
app_email = "hr@tripod.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tripod_hr/css/tripod_hr.css"
# app_include_js = "/assets/tripod_hr/js/tripod_hr.js"

# include js, css files in header of web template
# web_include_css = "/assets/tripod_hr/css/tripod_hr.css"
# web_include_js = "/assets/tripod_hr/js/tripod_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tripod_hr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Employee": "public/js/employee.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "tripod_hr.utils.jinja_methods",
#	"filters": "tripod_hr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tripod_hr.install.before_install"
# after_install = "tripod_hr.install.after_install"

# After Migrate — install CTC custom fields on Employee + SSA
# -----------------------------------------------------------
before_migrate = [
    "tripod_hr.registry.migration.take_snapshot"
]

after_migrate = [
    "tripod_hr.tripod_hr.ctc_management.install_ctc_fields.install",
    "tripod_hr.tripod_hr.payroll_filter.install_employment_type_field.install",
    "tripod_hr.tripod_hr.ctc_management.install_budget_dashboard.after_migrate",
    "tripod_hr.tripod_hr.ctc_management.install_transfer_fields.install",
    "tripod_hr.registry.migration.diff_after_migrate"
]

# Uninstallation
# ------------

# before_uninstall = "tripod_hr.uninstall.before_uninstall"
# after_uninstall = "tripod_hr.uninstall.after_uninstall"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tripod_hr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Salary Slip": "tripod_hr.overrides.salary_slip.CustomSalarySlip",
	"Payroll Entry": "tripod_hr.overrides.payroll_entry.CustomPayrollEntry",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee": {
		"validate": "tripod_hr.tripod_hr.ctc_management.transfer_sync.apply_latest_transfer",
		"before_save": "tripod_hr.events.ctc_automation.employee_before_save"
	},
	"Salary Structure Assignment": {
		"on_submit": "tripod_hr.events.ctc_automation.ssa_on_submit",
		"on_cancel": "tripod_hr.events.ctc_automation.ssa_on_cancel"
	}
}

# ERP Customization Register — site-side capture
# ----------------------------------------------
# Every save of a tracked artefact appends to the change log; the first insert
# also creates the register record. Handlers never block the user's save.
_REGISTRY_TRACKED = (
	"Custom Field",
	"Property Setter",
	"Server Script",
	"Client Script",
	"Print Format",
	"Workflow",
	"Notification",
	"Dashboard Chart",
	"Web Form",
	"DocType",
	"Report",
	"Page",
)

for _dt in _REGISTRY_TRACKED:
	doc_events.setdefault(_dt, {})
	doc_events[_dt]["after_insert"] = "tripod_hr.registry.tracker.on_artefact_insert"
	doc_events[_dt]["on_update"] = "tripod_hr.registry.tracker.on_artefact_update"
	doc_events[_dt]["on_trash"] = "tripod_hr.registry.tracker.on_artefact_trash"

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"tripod_hr.tasks.all"
#	],
#	"daily": [
#		"tripod_hr.tasks.daily"
#	],
#	"hourly": [
#		"tripod_hr.tasks.hourly"
#	],
#	"weekly": [
#		"tripod_hr.tasks.weekly"
#	],
#	"monthly": [
#		"tripod_hr.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "tripod_hr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "tripod_hr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "tripod_hr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"tripod_hr.auth.validate"
# ]

scheduler_events = {
    "daily": [
        "tripod_hr.registry.tracker.nightly_sync"
    ],
    "monthly": [
        "tripod_hr.tripod_hr.ctc_management.gratuity_provision.update_all_gratuity_provisions",
        "tripod_hr.tripod_hr.ctc_management.budget_snapshot.monthly_capture"
    ]
}
