// Copyright (c) 2026, Tripod Mena
frappe.query_reports["CTC Budget Summary"] = {
    "filters": [
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
