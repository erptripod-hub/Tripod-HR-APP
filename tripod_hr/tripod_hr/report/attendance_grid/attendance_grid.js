// Copyright (c) 2026, Tripod Mena
frappe.query_reports["Attendance Grid"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_end(),
            "reqd": 1
        },
        {
            "fieldname": "employment_type",
            "label": __("Employment Type"),
            "fieldtype": "Link",
            "options": "Employment Type"
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        // only the day columns (d_YYYYMMDD) get colored blocks
        if (column.fieldname && column.fieldname.indexOf("d_") === 0 && value) {
            var styles = {
                "P":  ["#E4F4EC", "#1F7A50"],   // present  - light green
                "A":  ["#FBE9E7", "#B23A2E"],   // absent   - light red
                "AL": ["#E8F0FA", "#2A5C8A"],   // annual   - light blue
                "SL": ["#FCF0DF", "#9A6B1E"],   // sick     - light orange
                "L":  ["#EFEDE7", "#5A5A5A"],   // other lv - neutral
                "H":  ["#EEECE6", "#8C8C8C"],   // holiday  - grey
                "\u00bd": ["#FBF3DD", "#8A6B1E"] // half day - light gold
            };
            var s = styles[value];
            if (s) {
                return '<span style="display:inline-block;min-width:30px;padding:2px 6px;'
                    + 'border-radius:5px;font-weight:600;font-size:11px;'
                    + 'background:' + s[0] + ';color:' + s[1] + ';">' + value + '</span>';
            }
        }
        return default_formatter(value, row, column, data);
    }
};
