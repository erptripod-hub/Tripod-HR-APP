frappe.views.calendar['Leave Plan Request'] = {
	field_map: {
		start: 'from_date',
		end: 'to_date',
		id: 'name',
		title: 'title',
		allDay: 'allDay',
		status: 'status'
	},
	status_color: {
		Planned: 'blue',
		Approved: 'green',
		Converted: 'orange',
		Rejected: 'red',
		Cancelled: 'gray'
	},
	filters: [
		{
			fieldtype: 'Link',
			fieldname: 'company',
			options: 'Company',
			label: __('Company')
		},
		{
			fieldtype: 'Link',
			fieldname: 'employment_type',
			options: 'Employment Type',
			label: __('Employment Type')
		},
		{
			fieldtype: 'Link',
			fieldname: 'department',
			options: 'Department',
			label: __('Department')
		},
		{
			fieldtype: 'Data',
			fieldname: 'section',
			label: __('Section')
		},
		{
			fieldtype: 'Link',
			fieldname: 'leave_type',
			options: 'Leave Type',
			label: __('Leave Type')
		}
	],
	get_events_method: 'tripod_hr.tripod_hr.doctype.leave_plan_request.leave_plan_request.get_events'
};
