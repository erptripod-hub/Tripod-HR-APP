import frappe
from frappe.model.document import Document

class PerformanceAppraisalForm(Document):
	def before_save(self):
		self.calculate_overall_rating()
	
	def calculate_overall_rating(self):
		"""Calculate overall rating from all objectives"""
		ratings = []
		
		# Collect all objective ratings
		for i in range(1, 7):
			rating_field = f"objective_{i}_rating"
			rating = self.get(rating_field)
			if rating:
				try:
					ratings.append(int(rating))
				except:
					pass
		
		# Calculate average
		if ratings:
			self.overall_rating = sum(ratings) / len(ratings)
		else:
			self.overall_rating = 0
