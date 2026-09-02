frappe.pages['leave-planner-board'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Leave Planner Board'),
		single_column: true
	});

	var board = new LeavePlannerBoard(wrapper, page);
	board.init();
};

var LPB_METHOD = 'tripod_hr.tripod_hr.doctype.leave_plan_request.leave_plan_request.';

var LPB_MONTH_NAMES = [
	'January', 'February', 'March', 'April', 'May', 'June',
	'July', 'August', 'September', 'October', 'November', 'December'
];

var LPB_STATUS_COLOR = {
	Planned: '#AFA9EC',
	Approved: '#5DCAA5',
	Converted: '#85B7EB'
};

var LPB_STATUS_TEXT = {
	Planned: '#26215C',
	Approved: '#04342C',
	Converted: '#042C53'
};

var LeavePlannerBoard = class LeavePlannerBoard {
	constructor(wrapper, page) {
		this.wrapper = wrapper;
		this.page = page;
		this.options = {};

		var today = frappe.datetime.now_date();
		this.year = parseInt(today.split('-')[0], 10);
		this.month = parseInt(today.split('-')[1], 10);

		this.filters = {
			company: '',
			employment_type: '',
			department: '',
			section: ''
		};

		this.min_staff_gap = 3;
	}

	init() {
		var me = this;

		this.page.set_primary_action(__('New Plan'), function () {
			frappe.new_doc('Leave Plan Request');
		}, 'add');

		this.page.add_menu_item(__('Plan List'), function () {
			frappe.set_route('List', 'Leave Plan Request');
		});

		this.page.add_menu_item(__('Calendar View'), function () {
			frappe.set_route('List', 'Leave Plan Request', 'Calendar');
		});

		frappe.call({
			method: LPB_METHOD + 'get_filter_options',
			callback: function (r) {
				me.options = r.message || {};
				me.render_shell();
				me.refresh();
			}
		});
	}

	render_shell() {
		var html = '';

		html += '<div class="lpb-root" style="margin-top:-15px;">';
		html += '<div class="lpb-controls" style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;padding-top:24px;margin-bottom:12px;"></div>';
		html += '<div class="lpb-legend" style="margin-bottom:10px;font-size:12px;color:#6c7680;"></div>';
		html += '<div class="lpb-grid" style="overflow-x:auto;border:1px solid #e2e6e9;border-radius:8px;padding:10px;background:#fff;"></div>';
		html += '<div class="lpb-summary" style="display:flex;gap:12px;margin-top:12px;flex-wrap:wrap;"></div>';
		html += '</div>';

		$(this.wrapper).find('.page-content').html(html);

		this.render_controls();
		this.render_legend();
		this.bind_events();
	}

	render_controls() {
		var html = '';

		html += this.select_html('company', __('Company'), this.options.companies || []);
		html += this.select_html('employment_type', __('Employment Type'), this.options.employment_types || []);
		html += this.select_html('department', __('Department'), this.options.departments || []);
		html += this.select_html('section', __('Section'), this.options.sections || []);

		html += '<div style="min-width:150px;">';
		html += '<label style="display:block;font-size:11px;color:#8d99a6;margin-bottom:2px;">' + __('Month') + '</label>';
		html += '<div style="display:flex;gap:4px;align-items:center;">';
		html += '<button class="btn btn-default btn-xs lpb-prev">&lt;</button>';
		html += '<span class="lpb-month-label" style="min-width:110px;text-align:center;font-weight:500;"></span>';
		html += '<button class="btn btn-default btn-xs lpb-next">&gt;</button>';
		html += '</div></div>';

		html += '<div style="min-width:130px;">';
		html += '<label style="display:block;font-size:11px;color:#8d99a6;margin-bottom:2px;">' + __('Flag when out >=') + '</label>';
		html += '<input type="number" min="1" step="1" class="form-control input-sm lpb-gap" value="' + this.min_staff_gap + '">';
		html += '</div>';

		$(this.wrapper).find('.lpb-controls').html(html);
	}

	select_html(fieldname, label, values) {
		var html = '<div style="min-width:170px;">';
		html += '<label style="display:block;font-size:11px;color:#8d99a6;margin-bottom:2px;">' + label + '</label>';
		html += '<select class="form-control input-sm lpb-filter" data-fieldname="' + fieldname + '">';
		html += '<option value="">' + __('All') + '</option>';

		for (var i = 0; i < values.length; i++) {
			html += '<option value="' + frappe.utils.escape_html(values[i]) + '">' + frappe.utils.escape_html(values[i]) + '</option>';
		}

		html += '</select></div>';
		return html;
	}

	render_legend() {
		var html = '';
		html += this.legend_dot(LPB_STATUS_COLOR.Planned, __('Planned'));
		html += this.legend_dot(LPB_STATUS_COLOR.Approved, __('Approved'));
		html += this.legend_dot(LPB_STATUS_COLOR.Converted, __('Leave application created'));
		html += this.legend_dot('#F09595', __('Coverage gap'));
		$(this.wrapper).find('.lpb-legend').html(html);
	}

	legend_dot(color, label) {
		var html = '<span style="margin-right:14px;">';
		html += '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:' + color + ';margin-right:4px;"></span>';
		html += label + '</span>';
		return html;
	}

	bind_events() {
		var me = this;

		$(this.wrapper).on('change', '.lpb-filter', function () {
			me.filters[$(this).attr('data-fieldname')] = $(this).val();
			me.refresh();
		});

		$(this.wrapper).on('change', '.lpb-gap', function () {
			me.min_staff_gap = parseInt($(this).val(), 10) || 1;
			me.refresh();
		});

		$(this.wrapper).on('click', '.lpb-prev', function () {
			me.shift_month(-1);
		});

		$(this.wrapper).on('click', '.lpb-next', function () {
			me.shift_month(1);
		});

		$(this.wrapper).on('click', '.lpb-cell[data-plan]', function () {
			frappe.set_route('Form', 'Leave Plan Request', $(this).attr('data-plan'));
		});
	}

	shift_month(step) {
		this.month = this.month + step;

		if (this.month > 12) {
			this.month = 1;
			this.year = this.year + 1;
		}

		if (this.month < 1) {
			this.month = 12;
			this.year = this.year - 1;
		}

		this.refresh();
	}

	month_bounds() {
		var month_str = this.month < 10 ? '0' + this.month : '' + this.month;
		var start = this.year + '-' + month_str + '-01';
		var days = new Date(this.year, this.month, 0).getDate();
		var end = this.year + '-' + month_str + '-' + days;
		return { start: start, end: end, days: days };
	}

	refresh() {
		var me = this;
		var bounds = this.month_bounds();

		$(this.wrapper).find('.lpb-month-label').text(
			LPB_MONTH_NAMES[this.month - 1] + ' ' + this.year
		);

		frappe.call({
			method: LPB_METHOD + 'get_board_data',
			args: {
				start: bounds.start,
				end: bounds.end,
				company: this.filters.company,
				employment_type: this.filters.employment_type,
				department: this.filters.department,
				section: this.filters.section
			},
			callback: function (r) {
				var data = r.message || { plans: [] };
				me.render_grid(data.plans || [], bounds);
			}
		});
	}

	render_grid(plans, bounds) {
		if (!plans.length) {
			$(this.wrapper).find('.lpb-grid').html(
				'<div style="padding:30px;text-align:center;color:#8d99a6;">' +
				__('No leave plans for this month and filter.') + '</div>'
			);
			$(this.wrapper).find('.lpb-summary').html('');
			return;
		}

		var employees = {};
		var order = [];
		var coverage = {};
		var total_days = 0;
		var pending = 0;

		for (var i = 0; i < plans.length; i++) {
			var plan = plans[i];

			if (!employees[plan.employee]) {
				employees[plan.employee] = {
					employee_name: plan.employee_name || plan.employee,
					section: plan.section || plan.department || '',
					cells: {}
				};
				order.push(plan.employee);
			}

			total_days = total_days + (plan.total_days || 0);
			if (plan.status === 'Planned') {
				pending = pending + 1;
			}

			for (var d = 1; d <= bounds.days; d++) {
				var day_str = this.day_string(d);

				if (day_str >= plan.from_date && day_str <= plan.to_date) {
					employees[plan.employee].cells[d] = plan;
					coverage[d] = (coverage[d] || 0) + 1;
				}
			}
		}

		order.sort(function (a, b) {
			return employees[a].employee_name.localeCompare(employees[b].employee_name);
		});

		var html = '<table style="border-collapse:collapse;font-size:11px;width:100%;">';
		html += this.header_row(bounds);

		for (var e = 0; e < order.length; e++) {
			html += this.employee_row(employees[order[e]], bounds);
		}

		html += this.coverage_row(coverage, bounds);
		html += '</table>';

		$(this.wrapper).find('.lpb-grid').html(html);
		this.render_summary(order.length, total_days, pending, coverage);
	}

	day_string(day) {
		var month_str = this.month < 10 ? '0' + this.month : '' + this.month;
		var day_str = day < 10 ? '0' + day : '' + day;
		return this.year + '-' + month_str + '-' + day_str;
	}

	header_row(bounds) {
		var html = '<tr><th style="text-align:left;padding:4px 8px 4px 0;color:#8d99a6;font-weight:400;min-width:170px;">' + __('Employee') + '</th>';

		for (var d = 1; d <= bounds.days; d++) {
			html += '<th style="width:22px;text-align:center;color:#8d99a6;font-weight:400;padding-bottom:4px;">' + d + '</th>';
		}

		html += '</tr>';
		return html;
	}

	employee_row(employee, bounds) {
		var html = '<tr>';
		html += '<td style="padding:3px 8px 3px 0;white-space:nowrap;">' + frappe.utils.escape_html(employee.employee_name);
		html += ' <span style="color:#8d99a6;">' + frappe.utils.escape_html(employee.section) + '</span></td>';

		for (var d = 1; d <= bounds.days; d++) {
			var plan = employee.cells[d];

			if (!plan) {
				html += '<td style="height:22px;border-bottom:1px solid #f4f5f6;"></td>';
				continue;
			}

			var bg = LPB_STATUS_COLOR[plan.status] || '#D3D1C7';
			var fg = LPB_STATUS_TEXT[plan.status] || '#2C2C2A';
			var title = plan.leave_type + ' ' + plan.from_date + ' to ' + plan.to_date + ' (' + plan.status + ')';

			html += '<td class="lpb-cell" data-plan="' + plan.name + '" title="' + frappe.utils.escape_html(title) + '"';
			html += ' style="height:22px;background:' + bg + ';color:' + fg + ';cursor:pointer;"></td>';
		}

		html += '</tr>';
		return html;
	}

	coverage_row(coverage, bounds) {
		var html = '<tr><td style="padding:8px 8px 3px 0;color:#6c7680;border-top:1px solid #e2e6e9;">' + __('Out that day') + '</td>';

		for (var d = 1; d <= bounds.days; d++) {
			var count = coverage[d] || 0;
			var style = 'text-align:center;padding-top:8px;border-top:1px solid #e2e6e9;';

			if (count >= this.min_staff_gap) {
				style += 'background:#F09595;color:#501313;';
			} else if (count === 0) {
				style += 'color:#c8ccd0;';
			} else {
				style += 'color:#6c7680;';
			}

			html += '<td style="' + style + '">' + count + '</td>';
		}

		html += '</tr>';
		return html;
	}

	render_summary(employee_count, total_days, pending, coverage) {
		var gap_days = 0;

		for (var key in coverage) {
			if (coverage[key] >= this.min_staff_gap) {
				gap_days = gap_days + 1;
			}
		}

		var html = '';
		html += this.card(__('Employees planning leave'), employee_count, '');
		html += this.card(__('Planned days'), Math.round(total_days), '');
		html += this.card(__('Awaiting review'), pending, '');
		html += this.card(__('Coverage gap days'), gap_days, gap_days > 0 ? '#a32d2d' : '');

		$(this.wrapper).find('.lpb-summary').html(html);
	}

	card(label, value, color) {
		var html = '<div style="background:#f4f5f6;border-radius:8px;padding:12px 16px;min-width:150px;">';
		html += '<div style="font-size:12px;color:#6c7680;margin-bottom:4px;">' + label + '</div>';
		html += '<div style="font-size:22px;font-weight:500;' + (color ? 'color:' + color + ';' : '') + '">' + value + '</div>';
		html += '</div>';
		return html;
	}
};
