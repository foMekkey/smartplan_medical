// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Expired Stock Report"] = {
    filters: [
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
        },
        {
            fieldname: "from_date",
            label: __("من تاريخ الانتهاء"),
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: __("إلى تاريخ الانتهاء"),
            fieldtype: "Date"
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "total_value") {
            value = `<span style="color: red; font-weight: bold;">${value}</span>`;
        }
        
        return value;
    }
};
