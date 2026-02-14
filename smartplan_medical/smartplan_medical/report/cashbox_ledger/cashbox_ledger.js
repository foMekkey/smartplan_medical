frappe.query_reports["Cashbox Ledger"] = {
    "filters": [
        {
            "fieldname": "cashbox",
            "label": __("الصندوق"),
            "fieldtype": "Link",
            "options": "Cashbox",
            "reqd": 1,
            "width": 150
        },
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -30),
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
        
        // تمييز رصيد أول وآخر المدة
        if (data && (data.description == "رصيد أول المدة" || data.description == "رصيد آخر المدة")) {
            value = "<b>" + value + "</b>";
        }
        
        // تلوين الوارد باللون الأخضر
        if (column.fieldname == "receipt" && data && data.receipt > 0) {
            value = "<span style='color:green;'>" + value + "</span>";
        }
        
        // تلوين الصادر باللون الأحمر
        if (column.fieldname == "payment" && data && data.payment > 0) {
            value = "<span style='color:red;'>" + value + "</span>";
        }
        
        return value;
    },
    "onload": function(report) {
        report.page.add_inner_button(__("طباعة الدفتر"), function() {
            let filters = report.get_values();
            if (filters.cashbox) {
                frappe.route_options = {
                    cashbox: filters.cashbox,
                    from_date: filters.from_date,
                    to_date: filters.to_date
                };
                frappe.set_route("print", "Cashbox Ledger");
            }
        });
    }
};
