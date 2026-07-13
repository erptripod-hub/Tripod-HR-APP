// Copyright (c) 2026, Tripod HR
frappe.query_reports["Manpower Matrix"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": "Tripod Media FZ LLC",
            "reqd": 1
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data && data._grand) {
            value = `<span style="font-weight:700;">${value}</span>`;
        } else if (data && data._dept) {
            value = `<span style="font-weight:700;color:#185FA5;">${value}</span>`;
        }
        return value;
    }
};
