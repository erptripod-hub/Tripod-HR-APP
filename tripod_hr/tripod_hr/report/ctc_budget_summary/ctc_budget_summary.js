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
            "options": "\nFit Out UAE\nDubai Production\nDubai Office\nKSA Office\nKSA National\nKSA Production\nKSA Fit Out\nLogistics\nAdmin\nTap Gulf"
        }
    ],
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
