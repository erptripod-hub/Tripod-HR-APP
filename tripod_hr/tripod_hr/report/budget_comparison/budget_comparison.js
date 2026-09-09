frappe.query_reports["Budget Comparison"] = {
    "onload": function(report) {
        // Load available snapshot months into the dropdowns
        frappe.db.get_list("HR Budget Snapshot", {
            fields: ["snapshot_month"],
            group_by: "snapshot_month",
            order_by: "snapshot_month desc",
            limit: 0
        }).then(rows => {
            let months = [...new Set(rows.map(r => r.snapshot_month))].filter(Boolean);
            let opts = "\n" + months.join("\n");
            report.get_filter("from_month").df.options = opts;
            report.get_filter("to_month").df.options = opts;
            report.get_filter("from_month").refresh();
            report.get_filter("to_month").refresh();
            // auto-select: from = second latest, to = latest
            if (months.length >= 2) {
                report.set_filter_value("from_month", months[1]);
                report.set_filter_value("to_month", months[0]);
            } else if (months.length === 1) {
                report.set_filter_value("to_month", months[0]);
            }
        });
    },
    "filters": [
        {"fieldname":"from_month","label":__("From Month"),"fieldtype":"Select","options":"","reqd":1},
        {"fieldname":"to_month","label":__("To Month"),"fieldtype":"Select","options":"","reqd":1}
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data && data._grand) value = `<span style="font-weight:700;">${value}</span>`;
        const money_col = ["ctc_delta","ctc_pct","effect"].includes(column.fieldname);
        if (money_col && data && data.ctc_delta < 0) value=`<span style="color:#0F6E56;">${value}</span>`;
        if (money_col && data && data.ctc_delta > 0) value=`<span style="color:#C0392B;">${value}</span>`;
        return value;
    }
};
