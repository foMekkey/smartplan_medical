// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Operational Status Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("إلى تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "status" && data) {
            if (data.status.includes("معتمد")) {
                value = `<span style="color: green; font-weight: bold;">${value}</span>`;
            } else if (data.status.includes("ملغي")) {
                value = `<span style="color: red;">${value}</span>`;
            } else if (data.status.includes("انتظار")) {
                value = `<span style="color: orange;">${value}</span>`;
            }
        }
        
        return value;
    }
};
