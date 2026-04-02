import frappe

@frappe.whitelist()
def get_dashboard_data():
	"""Get all data for the appraisal dashboard"""
	
	# Get all appraisals
	appraisals = frappe.get_all('Performance Appraisal Form',
		fields=['name', 'employee', 'employee_name', 'employee_number', 'department', 
				'appraisal_cycle', 'overall_rating', 'docstatus', 'review_period'],
		order_by='modified desc'
	)
	
	# Calculate statistics
	stats = {
		'total': len(appraisals),
		'pending': len([a for a in appraisals if a.docstatus == 0]),
		'completed': len([a for a in appraisals if a.docstatus == 1]),
		'avg_rating': sum([a.overall_rating or 0 for a in appraisals]) / len(appraisals) if appraisals else 0
	}
	
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
		if appraisal.docstatus == 1:
			departments[dept]['completed'] += 1
		else:
			departments[dept]['pending'] += 1
		if appraisal.overall_rating:
			departments[dept]['ratings'].append(appraisal.overall_rating)
	
	# Calculate average rating per department
	for dept in departments.values():
		dept['avg_rating'] = sum(dept['ratings']) / len(dept['ratings']) if dept['ratings'] else 0
	
	# Get unique departments and cycles for filters
	filters = {
		'departments': list(set([a.department for a in appraisals if a.department])),
		'cycles': list(set([a.appraisal_cycle for a in appraisals if a.appraisal_cycle]))
	}
	
	return {
		'stats': stats,
		'departments': list(departments.values()),
		'employees': appraisals,
		'filters': filters
	}
