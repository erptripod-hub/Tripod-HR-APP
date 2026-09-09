// Copyright (c) 2026, Tripod Mena
const TRIPOD_UNITS_BY_REGION = {
    "UAE": ["Fit Out UAE", "Dubai Production", "Dubai Office", "Logistics", "Admin"],
    "KSA": ["KSA Office", "KSA National", "KSA Production", "KSA Fit Out", "Tap Gulf", "Logistics", "Admin"]
};
const TRIPOD_ALL_UNITS = [
    "Fit Out UAE", "Dubai Production", "Dubai Office",
    "KSA Office", "KSA National", "KSA Production", "KSA Fit Out",
    "Logistics", "Admin", "Tap Gulf"
];

function tripod_set_unit_options(report, region) {
    const units = region ? (TRIPOD_UNITS_BY_REGION[region] || []) : TRIPOD_ALL_UNITS;
    const unit_filter = report.get_filter("budget_unit");
    if (!unit_filter) return;
    const current = unit_filter.get_value();
    unit_filter.df.options = "\n" + units.join("\n");
    unit_filter.refresh();
    if (current && !units.includes(current)) {
        unit_filter.set_value("");
    }
}

frappe.query_reports["CTC Budget Summary"] = {
    "onload": function (report) {
        tripod_set_unit_options(report, report.get_filter_value("region"));
    },
    "filters": [
        {
            "fieldname": "region",
            "label": __("Region"),
            "fieldtype": "Select",
            "options": "\nUAE\nKSA",
            "on_change": function () {
                const report = frappe.query_report;
                tripod_set_unit_options(report, report.get_filter_value("region"));
                report.refresh();
            }
        },
        {
            "fieldname": "budget_unit",
            "label": __("Budget Unit"),
            "fieldtype": "Select",
            "options": "\nFit Out UAE\nDubai Production\nDubai Office\nLuxxe Production\nLuxxe Office\nLuxxe Fitout\nLuxxe Logistics\nKSA Office\nKSA National\nKSA Production\nKSA Fit Out\nLogistics\nAdmin\nTap Gulf"
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
        if (data && data._grand) {
            value = `<span style="font-weight:700;">${value}</span>`;
        } else if (data && data._region) {
            value = `<span style="font-weight:700;color:#185FA5;">${value}</span>`;
        } else if (data && data._bold) {
            value = `<span style="font-weight:600;">${value}</span>`;
        }
        return value;
    }
};
