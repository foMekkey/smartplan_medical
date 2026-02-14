frappe.query_reports["Cashbox Summary"] = {
    "filters": [
        {
            "fieldname": "cashbox",
            "label": __("الصندوق"),
            "fieldtype": "Link",
            "options": "Cashbox",
            "width": 150
        },
        {
            "fieldname": "cashbox_type",
            "label": __("نوع الصندوق"),
            "fieldtype": "Select",
            "options": "\nرئيسية\nفرعية\nمندوب",
            "width": 100
        },
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1,
            "width": 100
        },
        {
            "fieldname": "to_date",
            "label": __("إلى تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1,
            "width": 100
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // تلوين الفرق
        if (column.fieldname == "variance" && data) {
            if (data.variance > 0) {
                value = "<span style='color:green;'>" + value + "</span>";
            } else if (data.variance < 0) {
                value = "<span style='color:red;'>" + value + "</span>";
            }
        }
        
        // تلوين الحالة
        if (column.fieldname == "status" && data) {
            if (data.status == "متوازن") {
                value = "<span class='indicator-pill green'>" + value + "</span>";
            } else {
                value = "<span class='indicator-pill orange'>" + value + "</span>";
            }
        }
        
        return value;
    }
};
