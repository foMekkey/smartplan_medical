frappe.query_reports["Supplier Statement"] = {
    "filters": [
        {
            "fieldname": "supplier",
            "label": __("المورد"),
            "fieldtype": "Link",
            "options": "Supplier",
            "reqd": 1,
            "width": 150
        },
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
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
        
        // تلوين الرصيد
        if (column.fieldname == "balance" && data) {
            if (data.balance > 0) {
                value = "<span style='color:blue;'>" + value + "</span>";
            } else if (data.balance < 0) {
                value = "<span style='color:green;'>" + value + "</span>";
            }
        }
        
        return value;
    },
    "onload": function(report) {
        report.page.add_inner_button(__("طباعة كشف الحساب"), function() {
            let filters = report.get_values();
            if (filters.supplier) {
                frappe.route_options = {
                    supplier: filters.supplier,
                    from_date: filters.from_date,
                    to_date: filters.to_date
                };
                frappe.set_route("print", "Supplier Statement");
            }
        });
    }
};
