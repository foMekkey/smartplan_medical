frappe.query_reports["Daily Collections"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
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
        },
        {
            "fieldname": "customer",
            "label": __("العميل"),
            "fieldtype": "Link",
            "options": "Pharma Customer",
            "width": 150
        },
        {
            "fieldname": "payment_mode",
            "label": __("طريقة الدفع"),
            "fieldtype": "Select",
            "options": "\nنقدي\nشيك\nتحويل بنكي",
            "width": 100
        },
        {
            "fieldname": "bank_account",
            "label": __("الحساب البنكي"),
            "fieldtype": "Link",
            "options": "Bank Account",
            "width": 120
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // تلوين طريقة الدفع
        if (column.fieldname == "payment_mode" && data) {
            let color = "";
            if (data.payment_mode == "نقدي") color = "green";
            else if (data.payment_mode == "شيك") color = "orange";
            else if (data.payment_mode == "تحويل بنكي") color = "blue";
            
            if (color) {
                value = "<span class='indicator-pill " + color + "'>" + value + "</span>";
            }
        }
        
        return value;
    }
};
