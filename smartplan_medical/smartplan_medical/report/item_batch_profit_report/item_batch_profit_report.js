frappe.query_reports["Item Batch Profit Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("من تاريخ (From Date)"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.now_date(), -3),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("إلى تاريخ (To Date)"),
            fieldtype: "Date",
            default: frappe.datetime.now_date(),
            reqd: 1,
        },
        {
            fieldname: "item_code",
            label: __("الصنف (Item)"),
            fieldtype: "Link",
            options: "Item",
        },
        {
            fieldname: "classification",
            label: __("تصنيف العميل"),
            fieldtype: "Link",
            options: "Customer Classification",
        },
        {
            fieldname: "show_loss_only",
            label: __("الأصناف الخاسرة فقط"),
            fieldtype: "Check",
            default: 0,
        },
        {
            fieldname: "dispatch_priority",
            label: __("أولوية الصرف"),
            fieldtype: "Select",
            options: "\n90 يوم\n180 يوم\n365 يوم",
            default: "",
        },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "profit_margin" && data) {
            if (data.profit_margin < 0) {
                value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
            } else {
                value = "<span style='color:green'>" + value + "</span>";
            }
        }

        if (column.fieldname === "status" && data) {
            if (data.status === "خسارة ❌") {
                value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
            } else if (data.status === "أولوية صرف ⚠️") {
                value = "<span style='color:orange;font-weight:bold'>" + value + "</span>";
            } else {
                value = "<span style='color:green'>" + value + "</span>";
            }
        }

        if (column.fieldname === "days_to_expiry" && data) {
            if (data.days_to_expiry !== null && data.days_to_expiry <= 90) {
                value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
            } else if (data.days_to_expiry !== null && data.days_to_expiry <= 180) {
                value = "<span style='color:orange'>" + value + "</span>";
            }
        }

        return value;
    },
};
