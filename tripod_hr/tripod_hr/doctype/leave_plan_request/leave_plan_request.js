frappe.ui.form.on('Leave Plan Request', {
	refresh: function (frm) {
		if (frm.is_new()) {
			return;
		}

		if (!frm.doc.leave_application && frm.doc.status !== 'Cancelled' && frm.doc.status !== 'Rejected') {
			frm.add_custom_button(__('Create Leave Application'), function () {
				frappe.model.open_mapped_doc({
					method: 'tripod_hr.tripod_hr.doctype.leave_plan_request.leave_plan_request.make_leave_application',
					frm: frm,
					freeze: true
				});
			}, __('Actions'));
		}

		if (frm.doc.leave_application) {
			frm.add_custom_button(__('View Leave Application'), function () {
				frappe.set_route('Form', 'Leave Application', frm.doc.leave_application);
			}, __('Actions'));
		}

		frm.add_custom_button(__('Open Leave Planner Board'), function () {
			frappe.set_route('leave-planner-board');
		}, __('Actions'));

		frm.set_intro('');
		if (frm.doc.status === 'Planned') {
			frm.set_intro(__('This is a leave plan only. No leave balance is deducted until a Leave Application is created.'), 'blue');
		}
	},

	employee: function (frm) {
		if (!frm.doc.employee) {
			return;
		}
		frm.set_value('section', '');
	},

	leave_type: function (frm) {
		set_total_days(frm);
	},

	from_date: function (frm) {
		set_total_days(frm);
	},

	to_date: function (frm) {
		set_total_days(frm);
	}
});

function set_total_days(frm) {
	if (!frm.doc.employee || !frm.doc.leave_type || !frm.doc.from_date || !frm.doc.to_date) {
		return;
	}

	if (frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) < 0) {
		return;
	}

	frappe.call({
		method: 'tripod_hr.tripod_hr.doctype.leave_plan_request.leave_plan_request.get_planned_days',
		args: {
			employee: frm.doc.employee,
			leave_type: frm.doc.leave_type,
			from_date: frm.doc.from_date,
			to_date: frm.doc.to_date
		},
		callback: function (r) {
			if (!r.message) {
				return;
			}

			frm.set_value('total_days', r.message.total_days);

			if (r.message.excluded) {
				frm.set_value('balance_note', __('{0} calendar days, {1} holidays / weekends excluded.', [r.message.calendar_days, r.message.excluded]));
			} else {
				frm.set_value('balance_note', '');
			}
		}
	});
}
