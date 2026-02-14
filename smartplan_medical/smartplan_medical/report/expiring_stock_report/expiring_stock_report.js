// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Expiring Stock Report"] = {
    filters: [
        {
            fieldname: "warning_days",
            label: __("أيام التحذير"),
            fieldtype: "Int",
            default: 90,
            reqd: 1
        },
        {
            fieldname: "warehouse",
            label: __("المخزن"),
            fieldtype: "Link",
            options: "Warehouse"
        },
        {
            fieldname: "item_code",
            label: __("الصنف"),
            fieldtype: "Link",
            options: "Item"
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "status") {
            if (data.status === "خطر") {
                value = `<span style="color: red; font-weight: bold;">${value}</span>`;
            } else if (data.status === "تحذير") {
                value = `<span style="color: orange; font-weight: bold;">${value}</span>`;
            }
        }
        
        if (column.fieldname === "days_to_expiry" && data.days_to_expiry <= 30) {
            value = `<span style="color: red; font-weight: bold;">${value}</span>`;
        }
        
        return value;
    }
};
