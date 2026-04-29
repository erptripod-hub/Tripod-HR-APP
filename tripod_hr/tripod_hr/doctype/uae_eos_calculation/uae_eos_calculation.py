# Copyright (c) 2026, Custom HR Module
# For license information, please see license.txt
#
# UAE End of Service Benefit Calculation
# As per UAE Federal Decree-Law No. 33 of 2021 on Regulation of Labour Relations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, cint, getdate


class UAEEOSCalculation(Document):
	def validate(self):
		self.validate_dates()
		self.set_leave_basis_from_exit_status()
		self.calculate_gross_pay()
		self.calculate_service_period()
		self.calculate_gratuity()
		self.calculate_leave_salary()
		self.calculate_overtime()
		self.calculate_pending_salary()
		self.calculate_recovery()
		self.calculate_summary()
		self.set_default_status()

	def before_submit(self):
		"""Block submit unless status is Cleared."""
		if self.status != "Cleared":
			frappe.throw(
				_("Cannot submit. Please click <b>Mark as Cleared</b> first to confirm all calculations are reviewed and final.")
			)

	def on_submit(self):
		"""When submitted, mark as Completed."""
		self.db_set("status", "Completed")

	def on_cancel(self):
		"""When cancelled, mark as Cancelled."""
		self.db_set("status", "Cancelled")

	# ------------------------------------------------------------------
	# Default status
	# ------------------------------------------------------------------
	def set_default_status(self):
		"""New records start as In Process. Don't override Cleared/Completed/Cancelled."""
		if self.is_new() and not self.status:
			self.status = "In Process"
		# If reopened/edited after Cleared but before submit, allow status to stay Cleared
		# Only auto-reset to In Process on first save

	# ------------------------------------------------------------------
	# Validations
	# ------------------------------------------------------------------
	def validate_dates(self):
		if self.date_of_joining and self.date_of_settlement:
			if getdate(self.date_of_settlement) < getdate(self.date_of_joining):
				frappe.throw(_("Date of Settlement cannot be earlier than Date of Joining"))

	# ------------------------------------------------------------------
	# Auto-set leave basis from exit status
	# ------------------------------------------------------------------
	def set_leave_basis_from_exit_status(self):
		"""Auto-set leave calculation basis from exit status if not already set."""
		if not self.exit_status:
			return
		if self.exit_status == "End of Contract":
			self.leave_calculation_basis = "Full Month Salary (End of Contract)"
		else:
			# Resignation, Termination, etc. = Basic only
			self.leave_calculation_basis = "Basic Salary Only (Resignation/Termination)"

	# ------------------------------------------------------------------
	# Gross pay
	# ------------------------------------------------------------------
	def calculate_gross_pay(self):
		self.gross_pay_per_month = (
			flt(self.basic_salary)
			+ flt(self.housing_allowance)
			+ flt(self.transportation_allowance)
			+ flt(self.other_allowance)
		)

	# ------------------------------------------------------------------
	# Service period (years and days)
	# ------------------------------------------------------------------
	def calculate_service_period(self):
		if self.date_of_joining and self.date_of_settlement:
			days = date_diff(self.date_of_settlement, self.date_of_joining)
			self.total_service_days = days
			# Use 365.25 to match the sample's calculation precision
			self.employment_years = flt(days / 365.25, 4)
		else:
			self.total_service_days = 0
			self.employment_years = 0

	# ------------------------------------------------------------------
	# Gratuity (UAE Federal Decree-Law 33/2021)
	# ------------------------------------------------------------------
	def calculate_gratuity(self):
		# Determine base
		base_type = self.gratuity_base_type or "Basic Only"
		if base_type == "Basic Only":
			base = flt(self.basic_salary)
		elif base_type == "Basic + Housing":
			base = flt(self.basic_salary) + flt(self.housing_allowance)
		else:  # Basic + All Allowances
			base = flt(self.gross_pay_per_month)

		self.gratuity_base_amount = base
		self.daily_basic_wage = flt(base / 30, 2) if base else 0

		# Skip auto-calc if user has overridden
		if self.override_gratuity or self.calculation_mode == "Manual":
			# Still set the days_per_year display field for reference
			years = flt(self.employment_years)
			if years < 1:
				self.gratuity_days_per_year = 0
			elif years <= 5:
				self.gratuity_days_per_year = 21
			else:
				self.gratuity_days_per_year = 30
			return

		days = cint(self.total_service_days)
		years = flt(self.employment_years)
		daily = flt(self.daily_basic_wage)

		# UAE Gratuity Rules
		if years < 1:
			# No gratuity entitlement under 1 year of continuous service
			self.gratuity_days_per_year = 0
			gratuity = 0
		elif years <= 5:
			# 21 days basic per year for first 5 years (pro-rata by exact days)
			self.gratuity_days_per_year = 21
			gratuity = daily * 21 * (days / 365.25)
		else:
			# First 5 years at 21 days, remaining at 30 days
			self.gratuity_days_per_year = 30
			first_five_days = 5 * 365.25
			remaining_days = days - first_five_days
			gratuity = (daily * 21 * 5) + (daily * 30 * (remaining_days / 365.25))

		# Apply reduction percent if any (legacy/edge cases)
		if flt(self.gratuity_reduction_percent):
			gratuity = gratuity * (1 - flt(self.gratuity_reduction_percent) / 100)

		# UAE law cap: maximum 2 years total wage
		cap = base * 24
		if cap and gratuity > cap:
			gratuity = cap

		self.gratuity_payable = flt(gratuity, 2)

	# ------------------------------------------------------------------
	# Leave Salary
	# ------------------------------------------------------------------
	def calculate_leave_salary(self):
		# Compute daily rate based on basis
		if self.leave_calculation_basis == "Full Month Salary (End of Contract)":
			daily = flt(self.gross_pay_per_month) / 30 if self.gross_pay_per_month else 0
		else:
			# Basic Salary Only or unset → default Basic
			daily = flt(self.basic_salary) / 30 if self.basic_salary else 0

		self.leave_daily_rate = flt(daily, 2)

		# Auto leave balance if not given
		if self.leaves_accrued and self.leaves_utilized and not self.leaves_balance:
			self.leaves_balance = flt(self.leaves_accrued) - flt(self.leaves_utilized)

		# Skip auto-calc if overridden
		if self.override_leave or self.calculation_mode == "Manual":
			return

		balance = flt(self.leaves_balance)
		gross_leave = daily * balance

		# Subtract any already-paid amount and held visa-change amount
		net_leave = gross_leave - flt(self.leave_salary_paid) - flt(self.leave_salary_held_visa_change)
		if net_leave < 0:
			net_leave = 0

		self.leave_salary_payable = flt(net_leave, 2)

	# ------------------------------------------------------------------
	# Overtime
	# ------------------------------------------------------------------
	def calculate_overtime(self):
		if self.override_overtime or self.calculation_mode == "Manual":
			return

		hours = flt(self.pending_overtime_hours)
		rate = flt(self.overtime_rate_per_hour)
		self.overtime_payable = flt(hours * rate, 2)

	# ------------------------------------------------------------------
	# Pending Salary
	# ------------------------------------------------------------------
	def calculate_pending_salary(self):
		# Calculate pending salary from days worked
		gross = flt(self.gross_pay_per_month)
		days = cint(self.days_worked_pending)
		unpaid_leaves = flt(self.unpaid_leaves_taken)

		net_days = days - unpaid_leaves
		if net_days < 0:
			net_days = 0

		if gross:
			self.pending_salary_last_month = flt((gross / 30) * net_days, 2)
		else:
			self.pending_salary_last_month = 0

		# Total Salary Payable section = pending salary + air ticket
		if self.override_salary_payable or self.calculation_mode == "Manual":
			return

		self.salary_payable = flt(
			flt(self.pending_salary_last_month) + flt(self.air_ticket_allowance), 2
		)

	# ------------------------------------------------------------------
	# Recovery
	# ------------------------------------------------------------------
	def calculate_recovery(self):
		self.total_recovery = flt(
			flt(self.visa_labour_card_expense)
			+ flt(self.loan_advance_recovery)
			+ flt(self.notice_period_shortfall)
			+ flt(self.other_recovery),
			2,
		)

	# ------------------------------------------------------------------
	# Final Summary
	# ------------------------------------------------------------------
	def calculate_summary(self):
		self.total_gratuity = flt(self.gratuity_payable)
		self.total_leave_salary = flt(self.leave_salary_payable)
		self.total_overtime = flt(self.overtime_payable)
		self.total_salary_payable = flt(self.salary_payable)

		self.gross_total = flt(
			self.total_gratuity
			+ self.total_leave_salary
			+ self.total_overtime
			+ self.total_salary_payable,
			2,
		)
		self.total_deductions = flt(self.total_recovery)
		self.net_payable = flt(self.gross_total - self.total_deductions, 2)


# ----------------------------------------------------------------------
# Whitelisted methods callable from client script
# ----------------------------------------------------------------------
@frappe.whitelist()
def mark_as_cleared(docname):
	"""Mark the EOS record as Cleared. Called from the form button."""
	doc = frappe.get_doc("UAE EOS Calculation", docname)

	if doc.docstatus == 1:
		frappe.throw(_("Document is already submitted."))

	if doc.status == "Cleared":
		frappe.throw(_("Document is already marked as Cleared."))

	if doc.status not in ("In Process", None, ""):
		frappe.throw(_("Document status must be 'In Process' to mark as Cleared."))

	# Optional: ensure required calculations are non-zero before clearing
	if not doc.net_payable or doc.net_payable <= 0:
		frappe.throw(_("Cannot mark as Cleared. Net Payable amount is zero or invalid. Please complete all calculations."))

	doc.db_set("status", "Cleared")
	doc.db_set("cleared_by", frappe.session.user)
	doc.db_set("cleared_on", frappe.utils.now())

	frappe.msgprint(
		_("Marked as Cleared. You can now Submit the document."),
		alert=True,
		indicator="green"
	)
	return doc


@frappe.whitelist()
def get_employee_details(employee):
	"""Fetch employee details + latest salary structure assignment + leave balance."""
	if not employee:
		return {}

	emp = frappe.get_doc("Employee", employee)

	data = {
		"employee_name": emp.employee_name,
		"designation": emp.designation,
		"department": emp.department,
		"branch": emp.branch,
		"company": emp.company,
		"date_of_joining": emp.date_of_joining,
		"nationality": getattr(emp, "nationality", None),
		"emirates_id": getattr(emp, "iqama_no", None) or getattr(emp, "emirates_id", None),
		"passport_number": emp.passport_number,
		"bank_account": getattr(emp, "bank_ac_no", None),
		"iban": getattr(emp, "iban", None),
	}

	# Get latest salary structure assignment to fetch components
	ssa = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee, "docstatus": 1},
		["name", "base", "salary_structure"],
		order_by="from_date desc",
	)

	if ssa:
		ssa_name, base, structure = ssa
		data["base_salary"] = flt(base)

		# Pull earnings from the Salary Structure
		earnings = frappe.get_all(
			"Salary Detail",
			filters={"parent": structure, "parentfield": "earnings"},
			fields=["salary_component", "amount", "amount_based_on_formula", "formula"],
		)

		basic = housing = transport = other = 0
		for row in earnings:
			comp_lower = (row.salary_component or "").lower()
			amt = flt(row.amount)
			if "basic" in comp_lower:
				basic += amt
			elif "housing" in comp_lower or "house" in comp_lower or "accommodation" in comp_lower:
				housing += amt
			elif "transport" in comp_lower or "conveyance" in comp_lower:
				transport += amt
			else:
				other += amt

		# If components were not picked individually, dump base into basic
		if base and not basic:
			basic = base

		data["basic_salary"] = basic
		data["housing_allowance"] = housing
		data["transportation_allowance"] = transport
		data["other_allowance"] = other

	# Get leave balance for paid leave types
	leave_balance = 0
	leaves = frappe.db.sql("""
		SELECT SUM(la.total_leaves_allocated)
		FROM `tabLeave Allocation` la
		WHERE la.employee = %s
		AND la.docstatus = 1
		AND la.from_date <= CURDATE()
		AND la.to_date >= CURDATE()
	""", employee)
	if leaves and leaves[0][0]:
		leave_balance = flt(leaves[0][0])

	leaves_taken = frappe.db.sql("""
		SELECT SUM(la.total_leave_days)
		FROM `tabLeave Application` la
		WHERE la.employee = %s
		AND la.docstatus = 1
		AND la.status = 'Approved'
	""", employee)
	if leaves_taken and leaves_taken[0][0]:
		leave_balance -= flt(leaves_taken[0][0])

	data["leaves_balance"] = leave_balance if leave_balance > 0 else 0

	# Active loan recovery
	active_loan = frappe.db.sql("""
		SELECT SUM(l.outstanding_amount)
		FROM `tabLoan` l
		WHERE l.applicant = %s
		AND l.docstatus = 1
		AND l.status NOT IN ('Closed', 'Settled')
	""", employee)
	if active_loan and active_loan[0][0]:
		data["loan_advance_recovery"] = flt(active_loan[0][0])

	return data
