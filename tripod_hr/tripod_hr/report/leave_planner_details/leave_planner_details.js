frappe.query_reports['Leave Planner Details'] = {
	filters: [
		{
			fieldname: 'company',
			label: __('Company'),
			fieldtype: 'Link',
			options: 'Company'
		},
		{
			fieldname: 'employment_type',
			label: __('Employment Type'),
			fieldtype: 'Link',
			options: 'Employment Type'
		},
		{
			fieldname: 'department',
			label: __('Department'),
			fieldtype: 'Link',
			options: 'Department'
		},
		{
			fieldname: 'section',
			label: __('Section'),
			fieldtype: 'Data'
		},
		{
			fieldname: 'employee',
			label: __('Employee'),
			fieldtype: 'Link',
			options: 'Employee'
		},
		{
			fieldname: 'leave_type',
			label: __('Leave Type'),
			fieldtype: 'Link',
			options: 'Leave Type'
		},
		{
			fieldname: 'status',
			label: __('Status'),
			fieldtype: 'Select',
			options: '\nPlanned\nApproved\nRejected\nConverted\nCancelled'
		},
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.year_start()
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.year_end()
		}
	]
};
