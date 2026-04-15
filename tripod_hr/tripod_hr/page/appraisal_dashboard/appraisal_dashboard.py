import frappe

@frappe.whitelist()
def get_dashboard_data():
	"""Get all data for the appraisal dashboard"""
	
	try:
		# Get all appraisals - using only confirmed existing fields
		appraisals = frappe.get_all('Performance Appraisal Form',
			fields=['name', 'employee', 'employee_name', 'department', 
					'appraisal_cycle', 'workflow_state', 'docstatus', 'review_period'],
			order_by='modified desc'
		)
		
		# Fetch overall_rating separately to avoid field errors
		for appraisal in appraisals:
			doc = frappe.get_doc('Performance Appraisal Form', appraisal.name)
			appraisal.overall_rating = doc.get('overall_rating')
			
			# Fix null employee names by fetching from Employee master
			if not appraisal.employee_name and appraisal.employee:
				emp_data = frappe.db.get_value('Employee', appraisal.employee, 
					['employee_name', 'department'], as_dict=True)
				if emp_data:
					appraisal.employee_name = emp_data.employee_name
					if not appraisal.department:
						appraisal.department = emp_data.department
		
		# Calculate statistics based on workflow_state
		stats = {
			'total': len(appraisals),
			'pending': len([a for a in appraisals if a.workflow_state != 'Completed']),
			'completed': len([a for a in appraisals if a.workflow_state == 'Completed']),
			'avg_rating': 0
		}
		
		# Calculate average rating
		ratings = [float(a.overall_rating) for a in appraisals if a.overall_rating]
		if ratings:
			stats['avg_rating'] = sum(ratings) / len(ratings)
		
		# Group by department
		departments = {}
		for appraisal in appraisals:
			dept = appraisal.department or 'No Department'
			if dept not in departments:
				departments[dept] = {
					'name': dept,
					'employees': [],
					'total': 0,
					'completed': 0,
					'pending': 0,
					'ratings': []
				}
			
			departments[dept]['employees'].append(appraisal)
			departments[dept]['total'] += 1
			if appraisal.workflow_state == 'Completed':
				departments[dept]['completed'] += 1
			else:
				departments[dept]['pending'] += 1
			if appraisal.overall_rating:
				departments[dept]['ratings'].append(float(appraisal.overall_rating))
		
		# Calculate average rating per department
		for dept in departments.values():
			dept['avg_rating'] = sum(dept['ratings']) / len(dept['ratings']) if dept['ratings'] else 0
		
		return {
			'stats': stats,
			'departments': list(departments.values()),
			'employees': appraisals
		}
	
	except Exception as e:
		frappe.log_error(f"Dashboard Error: {str(e)}", "Appraisal Dashboard")
		return {
			'stats': {'total': 0, 'pending': 0, 'completed': 0, 'avg_rating': 0},
			'departments': [],
			'employees': []
		}
