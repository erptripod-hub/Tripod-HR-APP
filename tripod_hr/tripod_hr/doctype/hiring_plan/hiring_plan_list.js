// Shows head count and cost totals directly above the Hiring Plan list,
// reflecting whatever filters are applied (e.g. Designation = Driver).

frappe.listview_settings['Hiring Plan'] = {
	onload: function (listview) {
		frappe.hp_render_totals(listview);
	},
	refresh: function (listview) {
		frappe.hp_render_totals(listview);
	}
};

frappe.hp_stat = function (label, value) {
	return (
		'<div style="min-width:120px;">' +
		'<div style="font-size:11px;text-transform:uppercase;letter-spacing:.04em;' +
		'color:var(--text-muted, #6b7280);font-weight:500;">' + label + '</div>' +
		'<div style="font-size:19px;font-weight:600;line-height:1.2;margin-top:2px;">' + value + '</div>' +
		'</div>'
	);
};

frappe.hp_render_totals = function (listview) {
	if (frappe.hp_totals_timer) {
		clearTimeout(frappe.hp_totals_timer);
	}

	frappe.hp_totals_timer = setTimeout(function () {
		var filters = [];
		try {
			if (listview && listview.get_filters_for_args) {
				filters = listview.get_filters_for_args() || [];
			}
		} catch (e) {
			filters = [];
		}

		frappe.call({
			method: 'tripod_hr.tripod_hr.doctype.hiring_plan.hiring_plan.get_list_totals',
			args: { filters: JSON.stringify(filters) },
			callback: function (r) {
				if (!r || !r.message) {
					return;
				}

				var d = r.message;
				var fmt = function (v) {
					try {
						return format_number(v || 0, null, 0);
					} catch (e) {
						return Math.round(v || 0);
					}
				};

				var html =
					'<div class="hp-totals-bar" style="display:flex;flex-wrap:wrap;gap:28px;' +
					'padding:12px 16px;margin-bottom:10px;border:1px solid var(--border-color, #e5e3dc);' +
					'border-radius:8px;background:var(--fg-color, #ffffff);">' +
					frappe.hp_stat(__('Positions'), fmt(d.count)) +
					frappe.hp_stat(__('Monthly Salary'), fmt(d.salary)) +
					frappe.hp_stat(__('Monthly CTC'), fmt(d.ctc)) +
					frappe.hp_stat(__('Annual CTC'), fmt(d.annual_ctc)) +
					'</div>';

				var $anchor = listview && listview.$result;
				if (!$anchor || !$anchor.length) {
					return;
				}

				var $existing = $anchor.parent().find('.hp-totals-bar');
				if ($existing.length) {
					$existing.replaceWith(html);
				} else {
					$anchor.before(html);
				}
			}
		});
	}, 250);
};
