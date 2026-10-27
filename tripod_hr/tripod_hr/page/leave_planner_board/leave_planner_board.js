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

var LPB_WEEKDAY_LETTERS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

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

var LPB_HATCH = 'repeating-linear-gradient(45deg,#F1EFE8,#F1EFE8 3px,#D3D1C7 3px,#D3D1C7 5px)';

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
		html += this.legend_dot(LPB_STATUS_COLOR.Converted, __('Application created'));
		html += this.legend_dot(LPB_HATCH, __('Holiday / weekend, not counted'));
		html += this.legend_dot('#F09595', __('Coverage gap'));
		$(this.wrapper).find('.lpb-legend').html(html);
	}

	legend_dot(background, label) {
		var html = '<span style="margin-right:14px;white-space:nowrap;">';
		html += '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:' + background + ';margin-right:4px;"></span>';
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

	day_string(day) {
		var month_str = this.month < 10 ? '0' + this.month : '' + this.month;
		var day_str = day < 10 ? '0' + day : '' + day;
		return this.year + '-' + month_str + '-' + day_str;
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
				var data = r.message || {};
				me.holidays = data.holidays || {};
				me.common_holidays = {};

				var common = data.common_holidays || [];
				for (var i = 0; i < common.length; i++) {
					me.common_holidays[common[i]] = 1;
				}

				me.render_grid(data.plans || [], bounds);
			}
		});
	}

	is_holiday_for(employee, day_str) {
		var dates = this.holidays[employee] || [];
		return dates.indexOf(day_str) !== -1;
	}

	build_employees(plans, bounds) {
		var employees = {};
		var order = [];

		for (var i = 0; i < plans.length; i++) {
			var plan = plans[i];

			if (!employees[plan.employee]) {
				employees[plan.employee] = {
					employee: plan.employee,
					employee_name: plan.employee_name || plan.employee,
					department: plan.department || __('No department'),
					section: plan.section || '',
					days: {},
					counted: 0
				};
				order.push(plan.employee);
			}

			var row = employees[plan.employee];

			for (var d = 1; d <= bounds.days; d++) {
				var day_str = this.day_string(d);

				if (day_str >= plan.from_date && day_str <= plan.to_date) {
					var counted = !this.is_holiday_for(plan.employee, day_str);
					row.days[d] = { plan: plan, counted: counted };

					if (counted) {
						row.counted = row.counted + 1;
					}
				}
			}
		}

		return { employees: employees, order: order };
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

		var built = this.build_employees(plans, bounds);
		var employees = built.employees;
		var order = built.order;

		order.sort(function (a, b) {
			var dept = employees[a].department.localeCompare(employees[b].department);
			if (dept !== 0) {
				return dept;
			}
			return employees[a].employee_name.localeCompare(employees[b].employee_name);
		});

		var coverage = {};
		var total_counted = 0;
		var pending = 0;

		for (var i = 0; i < order.length; i++) {
			var row = employees[order[i]];
			total_counted = total_counted + row.counted;

			for (var d = 1; d <= bounds.days; d++) {
				var cell = row.days[d];
				if (cell && cell.counted) {
					coverage[d] = (coverage[d] || 0) + 1;
				}
			}
		}

		for (var p = 0; p < plans.length; p++) {
			if (plans[p].status === 'Planned') {
				pending = pending + 1;
			}
		}

		var html = '<table style="border-collapse:collapse;font-size:11px;width:100%;table-layout:fixed;">';
		html += '<colgroup><col style="width:180px;"><col span="' + bounds.days + '"><col style="width:42px;"></colgroup>';
		html += this.weekday_row(bounds);
		html += this.day_row(bounds);

		var current_department = null;

		for (var e = 0; e < order.length; e++) {
			var employee = employees[order[e]];

			if (employee.department !== current_department) {
				current_department = employee.department;
				html += this.department_row(current_department, bounds);
			}

			html += this.employee_row(employee, bounds);
		}

		html += this.coverage_row(coverage, bounds);
		html += '</table>';

		$(this.wrapper).find('.lpb-grid').html(html);
		this.render_summary(order.length, total_counted, pending, coverage);
	}

	weekday_row(bounds) {
		var html = '<tr><th style="padding-bottom:2px;"></th>';

		for (var d = 1; d <= bounds.days; d++) {
			var weekday = new Date(this.year, this.month - 1, d).getDay();
			var style = 'text-align:center;color:#b3b9bf;font-weight:400;padding-bottom:2px;';

			if (this.common_holidays[this.day_string(d)]) {
				style += 'background:#f4f5f6;';
			}

			html += '<th style="' + style + '">' + LPB_WEEKDAY_LETTERS[weekday] + '</th>';
		}

		html += '<th style="padding-bottom:2px;"></th></tr>';
		return html;
	}

	day_row(bounds) {
		var html = '<tr><th style="text-align:left;padding:0 8px 4px 0;color:#8d99a6;font-weight:400;">' + __('Employee') + '</th>';

		for (var d = 1; d <= bounds.days; d++) {
			var style = 'text-align:center;color:#8d99a6;font-weight:400;padding-bottom:4px;';

			if (this.common_holidays[this.day_string(d)]) {
				style += 'background:#f4f5f6;';
			}

			html += '<th style="' + style + '">' + d + '</th>';
		}

		html += '<th style="text-align:center;color:#8d99a6;font-weight:400;padding-bottom:4px;">' + __('Days') + '</th></tr>';
		return html;
	}

	department_row(department, bounds) {
		var html = '<tr><td colspan="' + (bounds.days + 2) + '"';
		html += ' style="padding:10px 0 3px;color:#6c7680;font-weight:500;">';
		html += frappe.utils.escape_html(department) + '</td></tr>';
		return html;
	}

	employee_row(employee, bounds) {
		var html = '<tr>';
		html += '<td style="padding:3px 8px 3px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">';
		html += frappe.utils.escape_html(employee.employee_name);

		if (employee.section) {
			html += ' <span style="color:#8d99a6;">' + frappe.utils.escape_html(employee.section) + '</span>';
		}

		html += '</td>';

		var d = 1;

		while (d <= bounds.days) {
			var cell = employee.days[d];

			if (!cell) {
				html += this.empty_cell(d);
				d = d + 1;
				continue;
			}

			var span = 1;

			while (d + span <= bounds.days) {
				var next_cell = employee.days[d + span];
				if (!next_cell || next_cell.plan.name !== cell.plan.name || next_cell.counted !== cell.counted) {
					break;
				}
				span = span + 1;
			}

			html += this.bar_cell(cell, span, employee);
			d = d + span;
		}

		html += '<td style="text-align:center;color:#6c7680;">' + employee.counted + '</td>';
		html += '</tr>';
		return html;
	}

	empty_cell(day) {
		var style = 'height:21px;border-bottom:1px solid #f4f5f6;';

		if (this.common_holidays[this.day_string(day)]) {
			style += 'background:#f4f5f6;';
		}

		return '<td style="' + style + '"></td>';
	}

	bar_cell(cell, span, employee) {
		var plan = cell.plan;
		var label = '';
		var style = 'height:21px;cursor:pointer;';

		if (cell.counted) {
			style += 'background:' + (LPB_STATUS_COLOR[plan.status] || '#D3D1C7') + ';';
			style += 'color:' + (LPB_STATUS_TEXT[plan.status] || '#2C2C2A') + ';text-align:center;';

			if (span >= 4) {
				label = plan.leave_type;
			}
		} else {
			style += 'background:' + LPB_HATCH + ';';
		}

		var title = plan.leave_type + ' ' + plan.from_date + ' to ' + plan.to_date;
		title = title + ' (' + plan.status + ')';

		if (!cell.counted) {
			title = title + ' - ' + __('holiday, not counted');
		}

		var html = '<td class="lpb-cell" colspan="' + span + '" data-plan="' + plan.name + '"';
		html += ' title="' + frappe.utils.escape_html(title) + '" style="' + style + '">';
		html += frappe.utils.escape_html(label) + '</td>';
		return html;
	}

	coverage_row(coverage, bounds) {
		var html = '<tr><td style="padding:8px 8px 3px 0;color:#6c7680;border-top:1px solid #e2e6e9;">' + __('Out that day') + '</td>';

		for (var d = 1; d <= bounds.days; d++) {
			var style = 'text-align:center;padding-top:8px;border-top:1px solid #e2e6e9;';
			var text = coverage[d] || 0;

			if (this.common_holidays[this.day_string(d)]) {
				style += 'background:#f4f5f6;color:#b3b9bf;';
				text = '&middot;';
			} else if (text >= this.min_staff_gap) {
				style += 'background:#F09595;color:#501313;';
			} else if (text === 0) {
				style += 'color:#c8ccd0;';
			} else {
				style += 'color:#6c7680;';
			}

			html += '<td style="' + style + '">' + text + '</td>';
		}

		html += '<td style="border-top:1px solid #e2e6e9;"></td></tr>';
		return html;
	}

	render_summary(employee_count, total_counted, pending, coverage) {
		var gap_days = 0;

		for (var key in coverage) {
			if (!this.common_holidays[this.day_string(parseInt(key, 10))] && coverage[key] >= this.min_staff_gap) {
				gap_days = gap_days + 1;
			}
		}

		var html = '';
		html += this.card(__('Employees on leave'), employee_count, '');
		html += this.card(__('Planned days'), total_counted, '');
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
