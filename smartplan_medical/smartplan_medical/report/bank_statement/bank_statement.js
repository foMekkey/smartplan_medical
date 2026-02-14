frappe.query_reports["Bank Statement"] = {
    "filters": [
        {
            "fieldname": "bank_account",
            "label": __("الحساب البنكي"),
            "fieldtype": "Link",
            "options": "Bank Account",
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
        
        // تلوين الإيداعات باللون الأخضر
        if (column.fieldname == "debit" && data && data.debit > 0) {
            value = "<span style='color:green;'>" + value + "</span>";
        }
        
        // تلوين السحوبات باللون الأحمر
        if (column.fieldname == "credit" && data && data.credit > 0) {
            value = "<span style='color:red;'>" + value + "</span>";
        }
        
        return value;
    },
    "onload": function(report) {
        report.page.add_inner_button(__("طباعة كشف الحساب"), function() {
            let filters = report.get_values();
            if (filters.bank_account) {
                frappe.route_options = {
                    bank_account: filters.bank_account,
                    from_date: filters.from_date,
                    to_date: filters.to_date
                };
                frappe.set_route("print", "Bank Statement");
            }
        });
    }
};
