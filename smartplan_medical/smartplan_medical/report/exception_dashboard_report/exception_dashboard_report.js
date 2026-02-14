// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Exception Dashboard Report"] = {
    "filters": [],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "severity" && data) {
            if (data.severity && data.severity.includes("حرج")) {
                value = `<span style="background-color: #ffebee; color: #c62828; padding: 3px 8px; border-radius: 4px; font-weight: bold;">${value}</span>`;
            } else if (data.severity && data.severity.includes("عالي")) {
                value = `<span style="background-color: #fff3e0; color: #ef6c00; padding: 3px 8px; border-radius: 4px; font-weight: bold;">${value}</span>`;
            } else if (data.severity && data.severity.includes("متوسط")) {
                value = `<span style="background-color: #fffde7; color: #f9a825; padding: 3px 8px; border-radius: 4px;">${value}</span>`;
            }
        }
        
        if (column.fieldname === "count" && data && data.count > 0) {
            if (data.severity && data.severity.includes("حرج")) {
                value = `<span style="color: #c62828; font-weight: bold; font-size: 14px;">${value}</span>`;
            }
        }
        
        if (column.fieldname === "action_required" && data) {
            value = `<span style="color: #1565c0; font-style: italic;">${value}</span>`;
        }
        
        return value;
    },
    
    "onload": function(report) {
        report.page.add_inner_button(__("تحديث"), function() {
            report.refresh();
        });
        
        // Auto refresh every 5 minutes
        setInterval(function() {
            report.refresh();
        }, 300000);
    }
};
