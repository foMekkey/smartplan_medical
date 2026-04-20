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
            label: __("أولوية الصرف (أيام)"),
            fieldtype: "Int",
            default: 0,
        },
        {
            fieldname: "auto_refresh",
            label: __("تحديث تلقائي 🔄"),
            fieldtype: "Check",
            default: 0,
            on_change: function () {
                let val = frappe.query_report.get_filter_value("auto_refresh");
                if (val) {
                    _start_realtime();
                } else {
                    _stop_realtime();
                }
            },
        },
    ],

    onload: function (report) {
        // Setup websocket listener for stock/sales changes
        frappe.realtime.on("profit_report_update", function (data) {
            if (frappe.query_report.get_filter_value("auto_refresh")) {
                _show_update_toast(data);
                frappe.query_report.refresh();
            }
        });
    },

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

        if (column.fieldname === "available_qty" && data) {
            if (data.available_qty <= 0) {
                value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
            }
        }

        if (column.fieldname === "reserved_qty" && data) {
            if (data.reserved_qty > 0) {
                value = "<span style='color:#e65100;font-weight:bold'>" + value + "</span>";
            }
        }

        return value;
    },
};

// === Real-time WebSocket Functions ===

function _start_realtime() {
    // Show live indicator
    if (!$(".realtime-indicator").length) {
        $("body").append(`
            <div class="realtime-indicator" style="
                position: fixed; bottom: 20px; left: 20px; z-index: 1100;
                background: linear-gradient(135deg, #2e7d32, #1b5e20);
                color: white; padding: 8px 16px; border-radius: 20px;
                font-size: 13px; font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                display: flex; align-items: center; gap: 8px;
            ">
                <span class="rt-dot" style="
                    width: 10px; height: 10px; background: #76ff03;
                    border-radius: 50%; display: inline-block;
                    animation: rt-blink 1.5s ease-in-out infinite;
                "></span>
                <span>بث مباشر — تحديث تلقائي</span>
            </div>
            <style>
                @keyframes rt-blink {
                    0%, 100% { opacity: 1; box-shadow: 0 0 4px #76ff03; }
                    50% { opacity: 0.4; box-shadow: 0 0 8px #76ff03; }
                }
            </style>
        `);
    }

    // Cleanup on page change
    $(document).one("page-change", _stop_realtime);
}

function _stop_realtime() {
    $(".realtime-indicator").remove();
}

function _show_update_toast(data) {
    let msg = data && data.message ? data.message : "تم تحديث البيانات";
    frappe.show_alert({
        message: `🔄 ${msg}`,
        indicator: "blue",
    }, 3);
}
