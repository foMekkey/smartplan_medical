// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Sales By Employee Report"] = {
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
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // تلوين نسبة التحصيل
        if (column.fieldname === "collection_rate") {
            if (data.collection_rate >= 90) {
                value = `<span style="color: green; font-weight: bold;">${value}</span>`;
            } else if (data.collection_rate >= 70) {
                value = `<span style="color: orange;">${value}</span>`;
            } else {
                value = `<span style="color: red;">${value}</span>`;
            }
        }
        
        return value;
    }
};
