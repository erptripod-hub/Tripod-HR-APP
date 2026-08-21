// Copyright (c) 2026, Tripod Mena
frappe.query_reports["Hiring Plan Summary"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company"
        },
        {
            "fieldname": "region",
            "label": __("Region"),
            "fieldtype": "Select",
            "options": "\nUAE\nKSA"
        },
        {
            "fieldname": "budget_unit",
            "label": __("Budget Unit"),
            "fieldtype": "Select",
            "options": "\nFit Out UAE\nDubai Production\nDubai Office\nLuxxe Production\nLuxxe Office\nLuxxe Fitout\nLuxxe Logistics\nKSA Office\nKSA National\nKSA Production\nKSA Fit Out\nLogistics\nAdmin\nTap Gulf"
        },
        {
            "fieldname": "section",
            "label": __("Section"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "designation",
            "label": __("Designation"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "planned_month",
            "label": __("Planned Month"),
            "fieldtype": "Select",
            "options": "\n2026-07\n2026-08\n2026-09\n2026-10\n2026-11\n2026-12"
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nOpen\nIn Progress\nFilled\nCancelled"
        },
        {
            "fieldname": "hire_type",
            "label": __("Hire Type"),
            "fieldtype": "Select",
            "options": "\nNew\nReplacement"
        }
    ],

	onload: function (report) {
		// Budget units and regions are read from the site, so each site
		// shows only what it actually uses instead of a hardcoded list.
		frappe.call({
			method: 'tripod_hr.tripod_hr.page.hr_budget_dashboard.hr_budget_dashboard.get_filter_options',
			callback: function (r) {
				var msg = (r && r.message) || {};
				var unit = report.get_filter('budget_unit');
				if (unit && (msg.units || []).length) {
					unit.df.options = [''].concat(msg.units);
					unit.set_options ? unit.set_options() : unit.refresh();
				}
				var region = report.get_filter('region');
				if (region && (msg.regions || []).length) {
					region.df.options = [''].concat(msg.regions);
					region.set_options ? region.set_options() : region.refresh();
				}
			}
		});
	},
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data && data.is_group) {
            value = `<span style="font-weight:700;">${value}</span>`;
        }
        return value;
    }
};
