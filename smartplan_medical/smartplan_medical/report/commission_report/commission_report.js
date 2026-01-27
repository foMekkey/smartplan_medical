// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.query_reports["Commission Report"] = {
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
            fieldname: "employee",
            label: __("الموظف"),
            fieldtype: "Data"
        },
        {
            fieldname: "status",
            label: __("الحالة"),
            fieldtype: "Select",
            options: "\nDraft\nPending Approval\nApproved\nPaid\nPartially Paid"
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "pending_commission" && data.pending_commission > 0) {
            value = `<span style="color: orange; font-weight: bold;">${value}</span>`;
        }
        
        if (column.fieldname === "status") {
            const status_colors = {
                "Draft": "red",
                "Pending Approval": "orange",
                "Approved": "blue",
                "Paid": "green",
                "Partially Paid": "orange"
            };
            const color = status_colors[data.status] || "grey";
            value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
        }
        
        return value;
    }
};
