// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Overdue Collections Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("من تاريخ الصرف"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -3)
        },
        {
            fieldname: "to_date",
            label: __("إلى تاريخ الصرف"),
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "customer",
            label: __("العميل"),
            fieldtype: "Link",
            options: "Pharma Customer"
        },
        {
            fieldname: "delivery_rep",
            label: __("مندوب التوصيل"),
            fieldtype: "Link",
            options: "Delivery Representative"
        },
        {
            fieldname: "min_days_overdue",
            label: __("الحد الأدنى لأيام التأخير"),
            fieldtype: "Int",
            default: 0
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "days_overdue") {
            if (data.days_overdue > 90) {
                value = `<span style="color: red; font-weight: bold;">${value}</span>`;
            } else if (data.days_overdue > 60) {
                value = `<span style="color: orange; font-weight: bold;">${value}</span>`;
            } else if (data.days_overdue > 30) {
                value = `<span style="color: #cc9900;">${value}</span>`;
            }
        }
        
        if (column.fieldname === "aging_bucket") {
            const colors = {
                "0-30 يوم": "blue",
                "31-60 يوم": "orange", 
                "61-90 يوم": "#cc0000",
                ">90 يوم": "red"
            };
            value = `<span style="color: ${colors[data.aging_bucket] || 'black'}; font-weight: bold;">${value}</span>`;
        }
        
        if (column.fieldname === "pending_amount") {
            value = `<span style="color: red;">${value}</span>`;
        }
        
        return value;
    }
};
