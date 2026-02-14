// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Discount Analysis Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("من تاريخ"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("إلى تاريخ"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "sales_person",
            label: __("موظف المبيعات"),
            fieldtype: "Link",
            options: "Tele Sales Team"
        },
        {
            fieldname: "min_discount_percent",
            label: __("الحد الأدنى لنسبة الخصم %"),
            fieldtype: "Percent",
            default: 0
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "discount_percent") {
            if (data.discount_percent > 15) {
                value = `<span style="color: red; font-weight: bold;">${value}</span>`;
            } else if (data.discount_percent > 10) {
                value = `<span style="color: orange;">${value}</span>`;
            }
        }
        
        if (column.fieldname === "approved" && !data.approved) {
            value = `<span style="color: red;">✗</span>`;
        } else if (column.fieldname === "approved" && data.approved) {
            value = `<span style="color: green;">✓</span>`;
        }
        
        return value;
    }
};
