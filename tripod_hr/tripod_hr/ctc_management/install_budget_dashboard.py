# Copyright (c) 2026, Tripod Mena
# Installs the HR Budget Dashboard: Number Cards + Dashboard Charts + Dashboard.
# Idempotent — safe to run on every migrate.

import frappe

DOCTYPE = "Employee"
ACTIVE_FILTER = '[["Employee","status","=","Active"],["Employee","custom_budget_unit","is","set"]]'


def _number_card(name, label, func, agg_field=None, filters=None, color=None):
    if frappe.db.exists("Number Card", name):
        return
    doc = frappe.get_doc({
        "doctype": "Number Card",
        "name": name,
        "label": label,
        "document_type": DOCTYPE,
        "function": func,
        "aggregate_function_based_on": agg_field,
        "filters_json": filters or ACTIVE_FILTER,
        "is_public": 1,
        "show_percentage_stats": 0,
        "type": "Document Type",
    })
    if color:
        doc.color = color
    doc.insert(ignore_permissions=True)


def _chart(name, label, chart_type, group_by=None, agg_func="Count", agg_field=None, filters=None):
    if frappe.db.exists("Dashboard Chart", name):
        return
    doc = frappe.get_doc({
        "doctype": "Dashboard Chart",
        "name": name,
        "chart_name": label,
        "chart_type": "Group By",
        "document_type": DOCTYPE,
        "group_by_type": "Count" if agg_func == "Count" else "Sum",
        "group_by_based_on": group_by,
        "aggregate_function_based_on": agg_field,
        "type": chart_type,
        "filters_json": filters or ACTIVE_FILTER,
        "is_public": 1,
        "timeseries": 0,
        "number_of_groups": 10,
    })
    doc.insert(ignore_permissions=True)


def install_budget_dashboard():
    # --- Number Cards ---
    _number_card("HR Total Headcount", "Total Headcount", "Count", color="#185FA5")
    _number_card("HR Total Actual Pay", "Actual Pay / mo", "Sum", "custom_total_salary", color="#185FA5")
    _number_card("HR Total Monthly CTC", "Monthly CTC", "Sum", "custom_monthly_ctc", color="#0F6E56")
    _number_card("HR Total Annual CTC", "Annual CTC", "Sum", "custom_annual_ctc", color="#0F6E56")
    _number_card("HR Gratuity Provision", "Gratuity Provision", "Sum", "custom_gratuity_monthly", color="#9A6A2F")

    # --- Charts ---
    _chart("HR Monthly CTC by Budget Unit", "Monthly CTC by Budget Unit", "Bar",
           group_by="custom_budget_unit", agg_func="Sum", agg_field="custom_monthly_ctc")
    _chart("HR Headcount by Budget Unit", "Headcount by Budget Unit", "Bar",
           group_by="custom_budget_unit", agg_func="Count")
    _chart("HR Headcount by Region", "Headcount by Region", "Percentage",
           group_by="custom_region", agg_func="Count")
    _chart("HR CTC by Sub-Department", "CTC by Sub-Department", "Bar",
           group_by="custom_sub_department", agg_func="Sum", agg_field="custom_monthly_ctc")

    # --- Dashboard ---
    if not frappe.db.exists("Dashboard", "HR Budget Dashboard"):
        dash = frappe.get_doc({
            "doctype": "Dashboard",
            "dashboard_name": "HR Budget Dashboard",
            "is_default": 0,
            "is_standard": 0,
            "cards": [
                {"card": "HR Total Headcount"},
                {"card": "HR Total Actual Pay"},
                {"card": "HR Total Monthly CTC"},
                {"card": "HR Total Annual CTC"},
                {"card": "HR Gratuity Provision"},
            ],
            "charts": [
                {"chart": "HR Monthly CTC by Budget Unit", "width": "Full"},
                {"chart": "HR Headcount by Budget Unit", "width": "Half"},
                {"chart": "HR Headcount by Region", "width": "Half"},
                {"chart": "HR CTC by Sub-Department", "width": "Full"},
            ],
        })
        dash.insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.logger().info("[install_budget_dashboard] HR Budget Dashboard installed")


def after_migrate():
    try:
        install_budget_dashboard()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "install_budget_dashboard failed")
