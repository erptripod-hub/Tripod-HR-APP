# Copyright (c) 2026, Tripod and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

RATING_FIELDS = [
	"rate_quality_of_work",
	"rate_communication",
	"rate_takes_initiative",
	"rate_collaboration",
	"rate_problem_solving",
	"rate_client_relations",
]


class ProjectTeamAppraisal(Document):
	def validate(self):
		self.calculate_total_score()

	def calculate_total_score(self):
		total = 0
		for field in RATING_FIELDS:
			value = self.get(field)
			if value:
				# value looks like "4 - Exceeds Expectations" -> take leading number
				try:
					total += int(str(value).split("-")[0].strip())
				except (ValueError, IndexError):
					pass
		self.total_score = total
