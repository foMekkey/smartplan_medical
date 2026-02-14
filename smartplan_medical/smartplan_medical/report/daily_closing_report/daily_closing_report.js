// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Closing Report"] = {
    "filters": [
        {
            "fieldname": "report_date",
            "label": __("تاريخ التقرير"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "status") {
            if (data && data.status) {
                return data.status;
            }
        }
        
        if (column.fieldname === "amount" && data) {
            if (data.metric && data.metric.includes("الفرق")) {
                if (data.amount > 0) {
                    value = `<span style="color: red; font-weight: bold;">${value}</span>`;
                } else if (data.amount < 0) {
                    value = `<span style="color: green; font-weight: bold;">${value}</span>`;
                }
            }
        }
        
        if (column.fieldname === "metric" && data) {
            value = `<span style="font-weight: 500;">${value}</span>`;
        }
        
        return value;
    },
    
    "onload": function(report) {
        report.page.add_inner_button(__("تحديث"), function() {
            report.refresh();
        });
    }
};
