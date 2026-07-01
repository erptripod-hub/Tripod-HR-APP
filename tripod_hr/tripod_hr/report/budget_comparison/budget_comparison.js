frappe.query_reports["Budget Comparison"] = {
    "filters": [
        {"fieldname":"from_month","label":__("From Month (YYYY-MM)"),"fieldtype":"Data","reqd":1},
        {"fieldname":"to_month","label":__("To Month (YYYY-MM)"),"fieldtype":"Data","reqd":1}
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data && data._grand) value = `<span style="font-weight:700;">${value}</span>`;
        if (column.fieldname==="ctc_delta" && data && data.ctc_delta<0) value=`<span style="color:#C0392B;">${value}</span>`;
        if (column.fieldname==="ctc_delta" && data && data.ctc_delta>0) value=`<span style="color:#0F6E56;">${value}</span>`;
        return value;
    }
};
