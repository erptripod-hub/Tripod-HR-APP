# Copyright (c) 2026, Tripod Mena
# One-time update of the site-specific print formats "EOS UAE" / "EOS KSA":
#   1. Signature footer: Employee (scan), HR Executive (creator), CPO, Finance - all above the line
#   2. Compensatory Leave Balance / Amount rows after Leave Salary Payable (only printed when there is a balance)
# Each change is applied only when the exact expected markup is found, otherwise that format is left untouched.

import frappe

SIG_START = "{# ---- Signatures ---- #}"
SIG_END = '<div class="footer-meta">'

SIGNATURE_BLOCK = """{# ---- Signatures ---- #}
    {% set hr_name = frappe.db.get_value("User", doc.owner, "full_name") or doc.owner %}
    {% set hr_sig = frappe.db.get_value("User", doc.owner, "custom_signature") %}
    {% set emp_sig = doc.get("custom_employee_signature") %}
    {% set cpo_user = doc.get("custom_cpo_approved_by") %}
    {% set fin_user = doc.get("custom_finance_approved_by") %}
    {% set cpo_sig = frappe.db.get_value("User", cpo_user, "custom_signature") if cpo_user else None %}
    {% set fin_sig = frappe.db.get_value("User", fin_user, "custom_signature") if fin_user else None %}
    {% set sig_style = "position: absolute; left: 0; right: 0; bottom: 100%; margin: 0 auto 2px auto; height: 40px; max-width: 150px;" %}
    <table class="signatures">
        <tr>
            <td style="position: relative;">
                {% if emp_sig %}<img src="{{ frappe.utils.get_url(emp_sig) }}" style="{{ sig_style }}">{% endif %}
                <span class="sig-name">{{ doc.employee_name or "" }}</span>
                <span class="sig-role">Employee</span>
            </td>
            <td style="position: relative;">
                {% if hr_sig %}<img src="{{ frappe.utils.get_url(hr_sig) }}" style="{{ sig_style }}">{% endif %}
                <span class="sig-name">{{ hr_name }}</span>
                <span class="sig-role">HR Executive</span>
            </td>
            <td style="position: relative;">
                {% if cpo_sig %}<img src="{{ frappe.utils.get_url(cpo_sig) }}" style="{{ sig_style }}">{% endif %}
                <span class="sig-name">{% if cpo_user %}{{ frappe.db.get_value("User", cpo_user, "full_name") }}{% else %}&nbsp;{% endif %}</span>
                <span class="sig-role">Chief People Officer</span>
                {% if doc.get("custom_cpo_approved_on") %}<span class="sig-role">{{ frappe.utils.formatdate(doc.custom_cpo_approved_on) }}</span>{% endif %}
            </td>
            <td style="position: relative;">
                {% if fin_sig %}<img src="{{ frappe.utils.get_url(fin_sig) }}" style="{{ sig_style }}">{% endif %}
                <span class="sig-name">{% if fin_user %}{{ frappe.db.get_value("User", fin_user, "full_name") }}{% else %}&nbsp;{% endif %}</span>
                <span class="sig-role">Head of Finance</span>
                {% if doc.get("custom_finance_approved_on") %}<span class="sig-role">{{ frappe.utils.formatdate(doc.custom_finance_approved_on) }}</span>{% endif %}
            </td>
        </tr>
    </table>

    """

LEAVE_ROW = {
	"EOS UAE": '<tr class="highlight-row"><td class="label">Leave Salary Payable</td><td class="value">{{ "{:,.2f}".format(doc.leave_salary_payable or 0) }}</td></tr>',
	"EOS KSA": '<tr class="highlight-row"><td class="label">Leave Salary Payable</td><td class="value">{{ "{:,.2f}".format(doc.leave_salary_payable or 0) }} SAR</td></tr>',
}
CURRENCY_SUFFIX = {"EOS UAE": "", "EOS KSA": " SAR"}


def comp_rows(suffix):
	return (
		' {% if doc.get("compensatory_leave_balance") %}'
		' <tr><td class="label">Compensatory Leave Balance</td>'
		'<td class="value">{{ "{:.2f}".format(doc.compensatory_leave_balance or 0) }}</td></tr>'
		' <tr class="highlight-row"><td class="label">Compensatory Leave Amount</td>'
		'<td class="value">{{ "{:,.2f}".format(doc.compensatory_leave_amount or 0) }}' + suffix + "</td></tr>"
		" {% endif %}"
	)


def update_html(name, html):
	changed = []
	# 1. signature footer
	s, e = html.find(SIG_START), html.find(SIG_END)
	if s != -1 and e > s and "emp_sig" not in html:
		html = html[:s] + SIGNATURE_BLOCK + html[e:]
		changed.append("signatures")
	# 2. compensatory leave rows
	row = LEAVE_ROW[name]
	if html.count(row) == 1 and "compensatory_leave_balance" not in html:
		html = html.replace(row, row + comp_rows(CURRENCY_SUFFIX[name]))
		changed.append("compensatory leave")
	return html, changed


def execute():
	for name in ("EOS UAE", "EOS KSA"):
		if not frappe.db.exists("Print Format", name):
			continue
		pf = frappe.get_doc("Print Format", name)
		html, changed = update_html(name, pf.html or "")
		if changed:
			pf.html = html
			pf.flags.ignore_permissions = True
			pf.save()
			print(f"{name}: updated {', '.join(changed)}")
		else:
			print(f"{name}: no change (markup not found or already updated)")
