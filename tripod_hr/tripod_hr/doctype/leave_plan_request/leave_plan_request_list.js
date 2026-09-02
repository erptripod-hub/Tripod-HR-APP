frappe.listview_settings['Leave Plan Request'] = {
	add_fields: ['status', 'from_date', 'to_date', 'total_days', 'department', 'section'],

	get_indicator: function (doc) {
		var colors = {
			Planned: 'blue',
			Approved: 'green',
			Converted: 'orange',
			Rejected: 'red',
			Cancelled: 'gray'
		};

		return [__(doc.status), colors[doc.status] || 'gray', 'status,=,' + doc.status];
	},

	onload: function (listview) {
		listview.page.add_inner_button(__('Planner Board'), function () {
			frappe.set_route('leave-planner-board');
		});
	}
};
