frappe.query_reports["Customer Aging Report"] = {
    "filters": [
        {
            "fieldname": "customer",
            "label": __("العميل"),
            "fieldtype": "Link",
            "options": "Pharma Customer",
            "width": 150
        },
        {
            "fieldname": "customer_category",
            "label": __("فئة العميل"),
            "fieldtype": "Select",
            "options": "\nصيدلية\nمستشفى\nموزع\nأخرى",
            "width": 100
        },
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -12),
            "width": 100
        },
        {
            "fieldname": "to_date",
            "label": __("إلى تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "width": 100
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "outstanding" && data && data.outstanding > 0) {
            value = "<span style='color:red;font-weight:bold;'>" + value + "</span>";
        }
        
        if (column.fieldname == "age_90_plus" && data && data.age_90_plus > 0) {
            value = "<span style='color:darkred;font-weight:bold;'>" + value + "</span>";
        }
        
        return value;
    }
};
