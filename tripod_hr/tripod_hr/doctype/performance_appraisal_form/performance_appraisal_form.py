# Copyright (c) 2026, Tripod and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PerformanceAppraisalForm(Document):
	def validate(self):
		"""Validate the Performance Appraisal Form"""
		self.validate_objectives()
		self.calculate_overall_rating()
	
	def validate_objectives(self):
		"""Ensure at least one objective exists"""
		if not self.objectives:
			frappe.throw("Please add at least one objective")
	
	def calculate_overall_rating(self):
		"""Calculate overall rating as average of objective ratings"""
		if not self.objectives:
			return
		
		total_rating = 0
		rated_objectives = 0
		
		for obj in self.objectives:
			if obj.rating:
				total_rating += int(obj.rating)
				rated_objectives += 1
		
		if rated_objectives > 0:
			avg_rating = total_rating / rated_objectives
			# Round to nearest integer
			self.overall_rating = str(round(avg_rating))
	
	def on_submit(self):
		"""Actions to perform when appraisal is submitted"""
		self.send_notification_to_employee()
	
	def send_notification_to_employee(self):
		"""Send email notification to employee when appraisal is completed"""
		if self.employee:
			employee_email = frappe.db.get_value("Employee", self.employee, "user_id")
			if employee_email:
				frappe.sendmail(
					recipients=[employee_email],
					subject=f"Performance Appraisal Completed - {self.review_period}",
					message=f"""
						<p>Dear {self.employee_name},</p>
						<p>Your performance appraisal for <strong>{self.review_period}</strong> has been completed.</p>
						<p><strong>Overall Rating:</strong> {self.overall_rating}/5</p>
						<p>Please log in to the system to view your detailed appraisal.</p>
						<p>Link: <a href="{frappe.utils.get_url()}/app/performance-appraisal-form/{self.name}">View Appraisal</a></p>
						<br>
						<p>Best regards,<br>HR Team</p>
					""",
					reference_doctype=self.doctype,
					reference_name=self.name
				)
