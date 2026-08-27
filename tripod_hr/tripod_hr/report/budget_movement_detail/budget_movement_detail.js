frappe.query_reports["Budget Movement Detail"] = {
    "onload": function (report) {
        frappe.db.get_list("HR Budget Snapshot", {
            fields: ["snapshot_month"], group_by: "snapshot_month",
            order_by: "snapshot_month desc", limit: 0
        }).then(rows => {
            const months = [...new Set(rows.map(r => r.snapshot_month))].filter(Boolean);
            const opts = "\n" + months.join("\n");
            ["from_month", "to_month"].forEach(f => {
                const flt = report.get_filter(f);
                if (flt) { flt.df.options = opts; flt.refresh(); }
            });
            if (months.length >= 2) {
                report.set_filter_value("from_month", months[1]);
                report.set_filter_value("to_month", months[0]);
            }
        });
    },
    "filters": [
        {"fieldname": "from_month", "label": __("From Month"), "fieldtype": "Select", "options": "", "reqd": 1},
        {"fieldname": "to_month", "label": __("To Month"), "fieldtype": "Select", "options": "", "reqd": 1},
        {"fieldname": "budget_unit", "label": __("Budget Unit"), "fieldtype": "Select",
         "options": "\nFit Out UAE\nDubai Production\nDubai Office\nKSA Office\nKSA National\nKSA Production\nKSA Fit Out\nLogistics\nAdmin\nTap Gulf"},
        {"fieldname": "movement", "label": __("Movement"), "fieldtype": "Select",
         "options": "\nNew Hire\nMoved In\nMoved Out\nRemoved\nPay Change"}
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "impact" && data) {
            if (data.impact > 0) value = `<span style="color:#C0392B;">${value}</span>`;
            if (data.impact < 0) value = `<span style="color:#0F6E56;">${value}</span>`;
        }
        return value;
    }
};
