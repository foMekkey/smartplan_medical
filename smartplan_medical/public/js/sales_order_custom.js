/**
 * Sales Order Custom Script - Fetch New Stock & Expiring Stock Items
 * Adds buttons to fetch recently received items and expiring items with batch & expiry details
 */

frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(
                __("📦 Fetch New Stock"),
                function () {
                    show_new_stock_dialog(frm);
                },
                __("Get Items From")
            );

            frm.add_custom_button(
                __("⚠️ Fetch Expiring Stock"),
                function () {
                    show_expiring_stock_dialog(frm);
                },
                __("Get Items From")
            );

            // Make it more prominent with styling
            setTimeout(() => {
                frm.$wrapper
                    .find('.btn-group .dropdown-menu a:contains("Fetch New Stock")')
                    .css({
                        "font-weight": "bold",
                        color: "#5e64ff",
                    });
            }, 300);
        }

        // Sales Person filter
        frm.set_query("custom_sales_person", () => {
            return {
                filters: [
                    ["Employee", "custom_مندوب_مبيعات", "=", 1]
                ]
            };
        });

        // Calculate total discount on refresh
        calculate_total_discount(frm);

        // Load customer balance on refresh
        load_customer_balance(frm);
    },

    onload(frm) {
        load_customer_balance(frm);
    },

    customer(frm) {
        // Load balance + show invoices summary
        load_customer_balance(frm);
        show_customer_invoices_summary(frm);

        // Auto-set sales person from customer
        if (frm.doc.customer) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.customer
                },
                callback(r) {
                    if (r.message && r.message.custom_sales_person) {
                        frm.set_value('custom_sales_person', r.message.custom_sales_person);
                        frappe.show_alert({
                            message: 'تم تحديد المندوب: ' + r.message.custom_sales_person,
                            indicator: 'green'
                        }, 3);
                    } else {
                        frappe.show_alert({
                            message: 'العميل ليس له مندوب مرتبط',
                            indicator: 'orange'
                        }, 3);
                    }
                }
            });
        } else {
            frm.set_value('custom_sales_person', '');
        }
    },

    custom_customer_balance(frm) {
        if (frm.doc.custom_customer_balance) {
            apply_balance_color(frm, frm.doc.custom_customer_balance);
        }
    }
});

function show_new_stock_dialog(frm) {
    let warehouse = frm.doc.set_warehouse || "";

    let d = new frappe.ui.Dialog({
        title: __("📦 Fetch New Stock Items"),
        size: "extra-large",
        fields: [
            {
                fieldtype: "Section Break",
                label: __("Filters"),
            },
            {
                fieldname: "warehouse",
                fieldtype: "Link",
                label: __("Warehouse"),
                options: "Warehouse",
                default: warehouse,
                change: function () {
                    fetch_and_render(d, frm);
                },
            },
            {
                fieldtype: "Column Break",
            },
            {
                fieldname: "days",
                fieldtype: "Select",
                label: __("Received in Last"),
                options: [
                    { label: __("7 Days"), value: "7" },
                    { label: __("15 Days"), value: "15" },
                    { label: __("30 Days"), value: "30" },
                    { label: __("60 Days"), value: "60" },
                    { label: __("90 Days"), value: "90" },
                ],
                default: "30",
                change: function () {
                    fetch_and_render(d, frm);
                },
            },
            {
                fieldtype: "Column Break",
            },
            {
                fieldname: "search",
                fieldtype: "Data",
                label: __("Search Item"),
                placeholder: __("Type to search..."),
                change: function () {
                    filter_results(d);
                },
            },
            {
                fieldtype: "Section Break",
            },
            {
                fieldname: "results_area",
                fieldtype: "HTML",
                label: "",
            },
        ],
        primary_action_label: __("➕ Add Selected Items"),
        primary_action(values) {
            add_selected_items(d, frm);
        },
    });

    d.show();
    d.$wrapper.find(".modal-dialog").css("max-width", "1100px");

    // Add custom styles
    inject_dialog_styles(d);

    // Fetch items immediately
    fetch_and_render(d, frm);
}

function inject_dialog_styles(d) {
    let styles = `
    <style>
        .new-stock-container {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .stock-summary-bar {
            display: flex;
            gap: 16px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .summary-card {
            flex: 1;
            min-width: 140px;
            padding: 14px 18px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .summary-card .number {
            font-size: 26px;
            font-weight: 700;
            line-height: 1.2;
        }
        .summary-card .label-text {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
            opacity: 0.85;
        }
        .card-total { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .card-ok { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .card-warning { background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); color: white; }
        .card-expired { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: white; }

        .stock-table-wrapper {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color, #e2e8f0);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }
        .stock-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        .stock-table thead th {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            padding: 12px 14px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
            z-index: 1;
        }
        .stock-table thead th:first-child {
            text-align: center;
            width: 45px;
        }
        .stock-table tbody tr {
            transition: background-color 0.15s ease;
            border-bottom: 1px solid var(--border-color, #edf2f7);
        }
        .stock-table tbody tr:hover {
            background-color: rgba(102, 126, 234, 0.06);
        }
        .stock-table tbody tr.row-selected {
            background-color: rgba(102, 126, 234, 0.12) !important;
        }
        .stock-table tbody td {
            padding: 10px 14px;
            vertical-align: middle;
        }
        .stock-table tbody td:first-child {
            text-align: center;
        }

        .item-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .item-code {
            font-weight: 600;
            color: var(--text-color, #2d3748);
            font-size: 13px;
        }
        .item-name {
            font-size: 11px;
            color: var(--text-muted, #718096);
        }
        .item-group-badge {
            display: inline-block;
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 10px;
            background: rgba(102, 126, 234, 0.1);
            color: #5e64ff;
            font-weight: 500;
            margin-top: 2px;
        }

        .batch-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            background: rgba(102, 126, 234, 0.1);
            color: #5e64ff;
        }
        .batch-none {
            color: var(--text-muted, #a0aec0);
            font-style: italic;
            font-size: 12px;
        }

        .expiry-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
        }
        .expiry-ok { background: rgba(56, 239, 125, 0.1); color: #0d9f6e; }
        .expiry-warning { background: rgba(242, 153, 74, 0.12); color: #c05621; }
        .expiry-near_expiry { background: rgba(237, 100, 52, 0.15); color: #c53030; }
        .expiry-expired { background: rgba(235, 51, 73, 0.12); color: #c53030; text-decoration: line-through; }
        .expiry-no_expiry { color: var(--text-muted, #a0aec0); font-style: italic; font-size: 12px; }

        .days-info {
            font-size: 10px;
            display: block;
            margin-top: 2px;
        }

        .qty-display {
            font-weight: 700;
            font-size: 14px;
            color: var(--text-color, #2d3748);
        }
        .qty-uom {
            font-size: 11px;
            color: var(--text-muted, #718096);
            margin-left: 3px;
        }

        .qty-input {
            width: 75px;
            padding: 6px 10px;
            border: 2px solid var(--border-color, #e2e8f0);
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            font-size: 13px;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .qty-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
            outline: none;
        }

        .select-all-cb {
            cursor: pointer;
            width: 18px;
            height: 18px;
            accent-color: #667eea;
        }
        .item-cb {
            cursor: pointer;
            width: 16px;
            height: 16px;
            accent-color: #667eea;
        }

        .rate-display {
            font-size: 12px;
            color: var(--text-muted, #718096);
        }

        .received-date {
            font-size: 11px;
            color: var(--text-muted, #718096);
        }

        .stock-loading {
            text-align: center;
            padding: 60px 20px;
        }
        .stock-loading .spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid rgba(102, 126, 234, 0.2);
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .stock-loading-text {
            margin-top: 14px;
            color: var(--text-muted, #718096);
            font-size: 14px;
        }

        .stock-empty {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted, #718096);
        }
        .stock-empty-icon {
            font-size: 48px;
            margin-bottom: 12px;
        }
        .stock-empty-text {
            font-size: 16px;
            font-weight: 500;
        }
        .stock-empty-hint {
            font-size: 13px;
            margin-top: 6px;
            opacity: 0.7;
        }

        .warehouse-tag {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(45, 55, 72, 0.08);
            color: var(--text-muted, #718096);
        }
    </style>
    `;
    d.$wrapper.find(".modal-body").prepend(styles);
}

function fetch_and_render(d, frm) {
    let wrapper = d.fields_dict.results_area.$wrapper;
    wrapper.html(`
        <div class="stock-loading">
            <div class="spinner"></div>
            <div class="stock-loading-text">${__("Loading stock items...")}</div>
        </div>
    `);

    let warehouse = d.get_value("warehouse") || "";
    let days = d.get_value("days") || "30";

    frappe.call({
        method: "smartplan_medical.fetch_new_stock.get_new_stock_items",
        args: { warehouse, days },
        callback: function (r) {
            if (r.message) {
                d._stock_items = r.message;
                render_results(d, r.message);
            } else {
                d._stock_items = [];
                render_empty(d);
            }
        },
        error: function () {
            wrapper.html(`
                <div class="stock-empty">
                    <div class="stock-empty-icon">⚠️</div>
                    <div class="stock-empty-text">${__("Error fetching items")}</div>
                    <div class="stock-empty-hint">${__("Please try again or check permissions")}</div>
                </div>
            `);
        },
    });
}

function render_results(d, items) {
    let wrapper = d.fields_dict.results_area.$wrapper;

    if (!items || items.length === 0) {
        render_empty(d);
        return;
    }

    // Calculate summary
    let total_items = items.length;
    let ok_count = items.filter((i) => i.expiry_status === "ok" || i.expiry_status === "no_expiry").length;
    let warning_count = items.filter((i) => i.expiry_status === "warning" || i.expiry_status === "near_expiry").length;
    let expired_count = items.filter((i) => i.expiry_status === "expired").length;

    let html = `<div class="new-stock-container">`;

    // Summary Cards
    html += `
        <div class="stock-summary-bar">
            <div class="summary-card card-total">
                <div class="number">${total_items}</div>
                <div class="label-text">${__("Total Items")}</div>
            </div>
            <div class="summary-card card-ok">
                <div class="number">${ok_count}</div>
                <div class="label-text">${__("Good")}</div>
            </div>
            <div class="summary-card card-warning">
                <div class="number">${warning_count}</div>
                <div class="label-text">${__("Near Expiry")}</div>
            </div>
            <div class="summary-card card-expired">
                <div class="number">${expired_count}</div>
                <div class="label-text">${__("Expired")}</div>
            </div>
        </div>
    `;

    // Table
    html += `
        <div class="stock-table-wrapper" style="max-height: 400px; overflow-y: auto;">
        <table class="stock-table">
            <thead>
                <tr>
                    <th><input type="checkbox" class="select-all-cb" title="${__("Select All")}"></th>
                    <th>${__("Item")}</th>
                    <th>${__("Batch")}</th>
                    <th>${__("Expiry Date")}</th>
                    <th>${__("Available Qty")}</th>
                    <th>${__("Rate")}</th>
                    <th>${__("Warehouse")}</th>
                    <th>${__("Qty to Add")}</th>
                </tr>
            </thead>
            <tbody>
    `;

    items.forEach((item, idx) => {
        let expiry_html = get_expiry_html(item);
        let batch_html = item.batch_no
            ? `<span class="batch-badge">${item.batch_no}</span>`
            : `<span class="batch-none">${__("No Batch")}</span>`;

        html += `
            <tr class="stock-row" data-idx="${idx}">
                <td>
                    <input type="checkbox" class="item-cb" data-idx="${idx}">
                </td>
                <td>
                    <div class="item-info">
                        <span class="item-code">${item.item_code}</span>
                        <span class="item-name">${item.item_name || ""}</span>
                        ${item.item_group ? `<span class="item-group-badge">${item.item_group}</span>` : ""}
                    </div>
                </td>
                <td>${batch_html}</td>
                <td>${expiry_html}</td>
                <td>
                    <span class="qty-display">${item.available_qty}</span>
                    <span class="qty-uom">${item.stock_uom}</span>
                </td>
                <td>
                    <span class="rate-display">${format_currency(item.avg_incoming_rate)}</span>
                </td>
                <td>
                    <span class="warehouse-tag">${item.warehouse}</span>
                </td>
                <td>
                    <input type="number" class="qty-input" data-idx="${idx}"
                           value="1" min="0.01" max="${item.available_qty}" step="1">
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div></div>`;
    wrapper.html(html);

    // Event: Select All
    wrapper.find(".select-all-cb").on("change", function () {
        let checked = $(this).prop("checked");
        wrapper.find(".item-cb").prop("checked", checked);
        wrapper.find(".stock-row").toggleClass("row-selected", checked);
    });

    // Event: Individual checkbox
    wrapper.find(".item-cb").on("change", function () {
        let row = $(this).closest("tr");
        row.toggleClass("row-selected", $(this).prop("checked"));

        let all = wrapper.find(".item-cb").length;
        let selected = wrapper.find(".item-cb:checked").length;
        wrapper.find(".select-all-cb").prop("checked", all === selected);
    });
}

function get_expiry_html(item) {
    if (!item.expiry_date || item.expiry_status === "no_expiry") {
        return `<span class="expiry-no_expiry">${__("No Expiry")}</span>`;
    }

    let icon = "";
    let days_text = "";

    switch (item.expiry_status) {
        case "ok":
            icon = "🟢";
            days_text = `${item.days_to_expiry} ${__("days left")}`;
            break;
        case "warning":
            icon = "🟡";
            days_text = `${item.days_to_expiry} ${__("days left")}`;
            break;
        case "near_expiry":
            icon = "🔴";
            days_text = `${item.days_to_expiry} ${__("days left")}`;
            break;
        case "expired":
            icon = "❌";
            days_text = __("Expired!");
            break;
    }

    return `
        <div class="expiry-badge expiry-${item.expiry_status}">
            ${icon} ${item.expiry_date}
            <span class="days-info">${days_text}</span>
        </div>
    `;
}

function render_empty(d) {
    let wrapper = d.fields_dict.results_area.$wrapper;
    wrapper.html(`
        <div class="stock-empty">
            <div class="stock-empty-icon">📭</div>
            <div class="stock-empty-text">${__("No new stock items found")}</div>
            <div class="stock-empty-hint">${__("Try changing the warehouse or date range filter")}</div>
        </div>
    `);
}

function filter_results(d) {
    let search = (d.get_value("search") || "").toLowerCase();
    let wrapper = d.fields_dict.results_area.$wrapper;

    if (!search) {
        wrapper.find(".stock-row").show();
        return;
    }

    wrapper.find(".stock-row").each(function () {
        let row = $(this);
        let text = row.text().toLowerCase();
        row.toggle(text.includes(search));
    });
}

function add_selected_items(d, frm) {
    let wrapper = d.fields_dict.results_area.$wrapper;
    let items = d._stock_items || [];
    let selected = [];

    wrapper.find(".item-cb:checked").each(function () {
        let idx = parseInt($(this).data("idx"));
        let qty_input = wrapper.find(`.qty-input[data-idx="${idx}"]`);
        let qty = parseFloat(qty_input.val()) || 1;

        if (qty > 0 && items[idx]) {
            selected.push({
                item: items[idx],
                qty: qty,
            });
        }
    });

    if (selected.length === 0) {
        frappe.show_alert(
            {
                message: __("Please select at least one item"),
                indicator: "orange",
            },
            3
        );
        return;
    }

    // Remove empty first row if exists
    if (
        frm.doc.items &&
        frm.doc.items.length === 1 &&
        !frm.doc.items[0].item_code
    ) {
        frm.doc.items = [];
        frm.refresh_field("items");
    }

    selected.forEach((sel) => {
        let row = frm.add_child("items");
        frappe.model.set_value(row.doctype, row.name, "item_code", sel.item.item_code);
        frappe.model.set_value(row.doctype, row.name, "qty", sel.qty);
        frappe.model.set_value(row.doctype, row.name, "warehouse", sel.item.warehouse);
    });

    frm.refresh_field("items");
    d.hide();

    frappe.show_alert(
        {
            message: __("{0} item(s) added successfully!", [selected.length]),
            indicator: "green",
        },
        5
    );
}

function format_currency(value) {
    if (!value) return "-";
    return frappe.format(value, { fieldtype: "Currency" });
}

// ==========================================
// Expiring Stock Logic
// ==========================================

function show_expiring_stock_dialog(frm) {
    let warehouse = frm.doc.set_warehouse || "";

    let d = new frappe.ui.Dialog({
        title: __("⚠️ Fetch Expiring Stock"),
        size: "extra-large",
        fields: [
            {
                fieldtype: "Section Break",
                label: __("Filters"),
            },
            {
                fieldname: "warehouse",
                fieldtype: "Link",
                label: __("Warehouse"),
                options: "Warehouse",
                default: warehouse,
                change: function () {
                    fetch_expiring_stock(d);
                },
            },
            {
                fieldtype: "Column Break",
            },
            {
                fieldname: "days",
                fieldtype: "Select",
                label: __("Expires within (Days)"),
                options: [
                    { label: __("30 Days"), value: "30" },
                    { label: __("60 Days"), value: "60" },
                    { label: __("90 Days"), value: "90" },
                    { label: __("120 Days"), value: "120" },
                    { label: __("180 Days"), value: "180" },
                    { label: __("365 Days"), value: "365" },
                ],
                default: "90",
                change: function () {
                    fetch_expiring_stock(d);
                },
            },
            {
                fieldtype: "Column Break",
            },
            {
                fieldname: "search",
                fieldtype: "Data",
                label: __("Search Item"),
                placeholder: __("Type to search..."),
                change: function () {
                    filter_expiring_results(d);
                },
            },
            {
                fieldtype: "Section Break",
            },
            {
                fieldname: "results_area",
                fieldtype: "HTML",
                label: "",
            },
        ],
        primary_action_label: __("➕ Add Selected Items"),
        primary_action(values) {
            add_expiring_items(d, frm);
        },
    });

    d.show();
    d.$wrapper.find(".modal-dialog").css("max-width", "1100px");
    inject_dialog_styles(d); // Reuse styles
    fetch_expiring_stock(d);
}

function fetch_expiring_stock(d) {
    let wrapper = d.fields_dict.results_area.$wrapper;
    wrapper.html(`
        <div class="stock-loading">
            <div class="spinner"></div>
            <div class="stock-loading-text">${__("Searching for expiring items...")}</div>
        </div>
    `);

    let warehouse = d.get_value("warehouse") || "";
    let days = d.get_value("days") || "90";

    frappe.call({
        method: "smartplan_medical.fetch_new_stock.get_expiring_items",
        args: { warehouse, days },
        callback: function (r) {
            if (r.message) {
                d._stock_items = r.message;
                render_expiring_results(d, r.message);
            } else {
                d._stock_items = [];
                render_empty(d);
            }
        },
        error: function () {
            wrapper.html(`
                <div class="stock-empty">
                    <div class="stock-empty-icon">⚠️</div>
                    <div class="stock-empty-text">${__("Error fetching items")}</div>
                </div>
            `);
        }
    });
}

function render_expiring_results(d, items) {
    let wrapper = d.fields_dict.results_area.$wrapper;

    if (!items || items.length === 0) {
        render_empty(d);
        return;
    }

    let html = `<div class="new-stock-container">`;

    // Simple summary
    html += `
        <div class="stock-summary-bar">
             <div class="summary-card card-expired">
                <div class="number">${items.length}</div>
                <div class="label-text">${__("Items Found")}</div>
            </div>
        </div>
    `;

    html += `
        <div class="stock-table-wrapper" style="max-height: 400px; overflow-y: auto;">
        <table class="stock-table">
            <thead>
                <tr>
                    <th><input type="checkbox" class="select-all-cb"></th>
                    <th>${__("Item")}</th>
                    <th>${__("Batch")}</th>
                    <th>${__("Expiry Date")}</th>
                    <th>${__("Warehouse")}</th>
                    <th>${__("Available Qty")}</th>
                    <th>${__("Qty to Add")}</th>
                </tr>
            </thead>
            <tbody>
    `;

    items.forEach((item, idx) => {
        let batch_html = `<span class="batch-badge">${item.batch_no}</span>`;
        // Calculate days left for display
        let today = frappe.datetime.get_today();
        let days_left = frappe.datetime.get_diff(item.expiry_date, today);
        let expiry_class = days_left < 0 ? "expiry-expired" : (days_left < 30 ? "expiry-near_expiry" : "expiry-warning");
        let expiry_text = days_left < 0 ? __("Expired") : `${days_left} ${__("days left")}`;

        let expiry_html = `
            <div class="expiry-badge ${expiry_class}">
                📅 ${item.expiry_date}
                <span class="days-info">${expiry_text}</span>
            </div>
        `;

        html += `
            <tr class="stock-row" data-idx="${idx}">
                <td><input type="checkbox" class="item-cb" data-idx="${idx}"></td>
                <td>
                    <div class="item-info">
                        <span class="item-code">${item.item_code}</span>
                        <span class="item-name">${item.item_name || ""}</span>
                    </div>
                </td>
                <td>${batch_html}</td>
                <td>${expiry_html}</td>
                <td><span class="warehouse-tag">${item.warehouse}</span></td>
                <td><span class="qty-display">${item.available_qty}</span> <span class="qty-uom">${item.stock_uom}</span></td>
                <td>
                    <input type="number" class="qty-input" data-idx="${idx}"
                           value="1" min="0.01" max="${item.available_qty}" step="1">
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div></div>`;
    wrapper.html(html);

    // Event handlers (same as before)
    wrapper.find(".select-all-cb").on("change", function () {
        let checked = $(this).prop("checked");
        wrapper.find(".item-cb").prop("checked", checked);
        wrapper.find(".stock-row").toggleClass("row-selected", checked);
    });

    wrapper.find(".item-cb").on("change", function () {
        let row = $(this).closest("tr");
        row.toggleClass("row-selected", $(this).prop("checked"));
    });
}

function filter_expiring_results(d) {
    let search = (d.get_value("search") || "").toLowerCase();
    let wrapper = d.fields_dict.results_area.$wrapper;
    if (!search) {
        wrapper.find(".stock-row").show();
        return;
    }
    wrapper.find(".stock-row").each(function () {
        let row = $(this);
        let text = row.text().toLowerCase();
        row.toggle(text.includes(search));
    });
}

function add_expiring_items(d, frm) {
    let wrapper = d.fields_dict.results_area.$wrapper;
    let items = d._stock_items || [];
    let selected = [];

    wrapper.find(".item-cb:checked").each(function () {
        let idx = parseInt($(this).data("idx"));
        let qty_input = wrapper.find(`.qty-input[data-idx="${idx}"]`);
        let qty = parseFloat(qty_input.val()) || 1;

        if (qty > 0 && items[idx]) {
            selected.push({ item: items[idx], qty: qty });
        }
    });

    if (selected.length === 0) {
        frappe.show_alert({ message: __("Please select items"), indicator: "orange" });
        return;
    }

    selected.forEach((sel) => {
        let row = frm.add_child("items");
        frappe.model.set_value(row.doctype, row.name, "item_code", sel.item.item_code);
        frappe.model.set_value(row.doctype, row.name, "qty", sel.qty);
        frappe.model.set_value(row.doctype, row.name, "batch_no", sel.item.batch_no);
        frappe.model.set_value(row.doctype, row.name, "warehouse", sel.item.warehouse);
    });

    frm.refresh_field("items");
    d.hide();
    frappe.show_alert({ message: __("Items added!"), indicator: "green" });
}

// ==========================================
// Sales Order Item Events
// (Migrated from Client Scripts: stock reservation, Item Stock, Calculate Discount)
// ==========================================

frappe.ui.form.on("Sales Order Item", {
    // Stock reservation warning when qty changes
    qty(frm, cdt, cdn) {
        show_reservation_details(frm, cdt, cdn);
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },

    // Item Stock availability check
    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let warehouse = row.warehouse || frm.doc.set_warehouse;
        if (!row.item_code || !warehouse) return;

        frappe.call({
            method: "erpnext.stock.utils.get_stock_balance",
            args: {
                item_code: row.item_code,
                warehouse: warehouse
            },
            callback(r) {
                let qty = r.message || 0;
                if (qty <= 0) {
                    frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "Bin",
                            filters: {
                                item_code: row.item_code,
                                actual_qty: [">", 0]
                            },
                            fields: ["warehouse", "actual_qty"],
                            order_by: "actual_qty desc"
                        },
                        callback(res) {
                            let html = `
                                <div style="font-size:14px">
                                    <p><b>الصنف غير متوفر في المخزن المختار</b></p>
                                    <p style="color:#666">المتاح في المخازن التالية:</p>
                                    <table class="table table-bordered">
                                        <thead>
                                            <tr>
                                                <th>المخزن</th>
                                                <th>الكمية المتاحة</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                            `;

                            if (res.message && res.message.length) {
                                res.message.forEach(d => {
                                    html += `
                                        <tr>
                                            <td>${d.warehouse}</td>
                                            <td>${d.actual_qty}</td>
                                        </tr>
                                    `;
                                });
                            } else {
                                html += `<tr><td colspan="2">لا يوجد رصيد في أي مخزن</td></tr>`;
                            }

                            html += "</tbody></table></div>";

                            frappe.msgprint({
                                title: "Stock Availability",
                                message: html,
                                indicator: "red"
                            });
                        }
                    });
                }
            }
        });
    },

    // Calculate Discount
    custom_discount_(frm, cdt, cdn) {
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },

    price_list_rate(frm, cdt, cdn) {
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },

    items_remove(frm) {
        calculate_total_discount(frm);
    }
});

// ==========================================
// Stock Reservation Warning
// ==========================================

function show_reservation_details(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let warehouse = row.warehouse || frm.doc.set_warehouse;

    if (!row.item_code || !warehouse) return;

    let available = row.custom_available_qty || 0;

    if (row.qty <= available) return;

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Stock Reservation",
            filters: {
                item_code: row.item_code,
                warehouse: warehouse
            },
            fields: ["sales_order", "sales_person", "qty"]
        },
        callback(res) {
            let html = `
                <div>
                    <h4 style="color:#d9534f">الكمية غير متاحة</h4>
                    <b>الصنف:</b> ${row.item_code}<br>
                    <b>المخزن:</b> ${warehouse}<br><br>
                    <b>المتاح للبيع:</b> ${available}<br>
                    <b>المطلوب:</b> ${row.qty}<br><br>
                    <b>الحجوزات الحالية:</b>
                    <table class="table table-bordered">
                        <tr>
                            <th>الطلب</th>
                            <th>المندوب</th>
                            <th>الكمية</th>
                        </tr>
            `;

            (res.message || []).forEach(d => {
                html += `
                    <tr>
                        <td>${d.sales_order}</td>
                        <td>${d.sales_person}</td>
                        <td>${d.qty}</td>
                    </tr>
                `;
            });

            html += "</table></div>";
            frappe.msgprint({
                title: "Stock Reservation",
                message: html,
                indicator: "red"
            });
        }
    });
}

// ==========================================
// Calculate Discount
// ==========================================

function apply_discount_and_calculate_total(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    if (row.custom_discount_ && row.price_list_rate) {
        let discount = parseFloat(row.custom_discount_);

        frappe.model.set_value(cdt, cdn, 'discount_percentage', discount)
            .then(() => {
                setTimeout(() => {
                    calculate_total_discount(frm);
                }, 200);
            });
    }
}

function calculate_total_discount(frm) {
    if (!frm.doc.items) return;

    let total_discount = 0;
    let total_before_discount = 0;

    frm.doc.items.forEach(function (item) {
        let price = parseFloat(item.price_list_rate) || 0;
        let qty = parseFloat(item.qty) || 0;
        let discount_percent = parseFloat(item.custom_discount_) || 0;

        if (discount_percent > 0 && price > 0 && qty > 0) {
            let item_total_before = price * qty;
            let discount_amount = item_total_before * (discount_percent / 100);

            total_before_discount += item_total_before;
            total_discount += discount_amount;
        }
    });

    frm.set_value('custom_total_discount_amount', total_discount);

    if (total_discount > 0) {
        frm.dashboard.add_indicator(
            __('Total Discount: {0}', [format_currency(total_discount)]),
            'orange'
        );
    }
}

// ==========================================
// Customer Balance & Invoices Summary
// (Migrated from Client Script: 'Customer Balance')
// ==========================================

function load_customer_balance(frm) {
    if (!frm.doc.customer) return;

    frappe.call({
        method: "erpnext.accounts.utils.get_balance_on",
        args: {
            party_type: "Customer",
            party: frm.doc.customer,
            company: frm.doc.company
        },
        callback(r) {
            let balance = r.message || 0;
            frm.set_value("custom_customer_balance", balance);

            setTimeout(() => {
                apply_balance_color(frm, balance);
            }, 300);
        }
    });
}

function apply_balance_color(frm, balance) {
    let field = frm.fields_dict.custom_customer_balance;
    if (!field) return;

    let input = field.$wrapper.find("input");
    let wrapper = field.$wrapper;

    wrapper.removeClass("text-danger text-success");

    if (balance > 0) {
        input.css({
            "color": "#d9534f",
            "font-weight": "bold",
            "background-color": "#fff5f5"
        });
        wrapper.addClass("text-danger");
    } else {
        input.css({
            "color": "#000",
            "font-weight": "normal",
            "background-color": "#fff"
        });
    }
}

function show_customer_invoices_summary(frm) {
    if (!frm.doc.customer) return;

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Sales Invoice",
            filters: {
                customer: frm.doc.customer,
                docstatus: 1,
                outstanding_amount: [">", 0]
            },
            fields: [
                "name",
                "posting_date",
                "grand_total",
                "outstanding_amount",
                "paid_amount",
                "due_date",
                "status"
            ],
            order_by: "posting_date desc",
            limit: 100
        },
        callback(r) {
            if (!r.message || r.message.length === 0) {
                frappe.show_alert({
                    message: __('✅ العميل ليس عليه أي فواتير مستحقة'),
                    indicator: 'green'
                }, 5);
                return;
            }

            let invoices = r.message;

            let promises = invoices.map(inv => {
                return new Promise((resolve) => {
                    frappe.db.get_doc('Sales Invoice', inv.name)
                        .then(doc => {
                            let sales_person = '-';
                            if (doc.sales_team && doc.sales_team.length > 0) {
                                sales_person = doc.sales_team[0].sales_person;
                            }
                            inv.sales_person = sales_person;
                            resolve(inv);
                        })
                        .catch(() => {
                            inv.sales_person = '-';
                            resolve(inv);
                        });
                });
            });

            Promise.all(promises).then(invoices_with_sales_person => {
                let total_outstanding = 0;
                let total_invoices = invoices_with_sales_person.length;
                let overdue_invoices = 0;

                invoices_with_sales_person.forEach(inv => {
                    total_outstanding += inv.outstanding_amount;
                    if (inv.due_date && frappe.datetime.get_diff(frappe.datetime.get_today(), inv.due_date) > 0) {
                        overdue_invoices++;
                    } else if (!inv.due_date) {
                        let days_since_posting = frappe.datetime.get_diff(frappe.datetime.get_today(), inv.posting_date);
                        if (days_since_posting > 30) {
                            overdue_invoices++;
                        }
                    }
                });

                show_invoices_dialog(frm, invoices_with_sales_person, total_outstanding, total_invoices, overdue_invoices);
            });
        }
    });
}

function show_invoices_dialog(frm, invoices, total_outstanding, total_invoices, overdue_invoices) {
    let html = `
        <style>
            .customer-summary-container {
                font-family: 'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                direction: rtl;
                background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
                padding: 10px;
                border-radius: 12px;
            }
            .summary-header {
                background: linear-gradient(135deg, #0d47a1 0%, #1976d2 50%, #42a5f5 100%);
                color: white;
                padding: 25px;
                border-radius: 12px 12px 0 0;
                margin: -15px -15px 25px -15px;
                box-shadow: 0 4px 12px rgba(13, 71, 161, 0.3);
                position: relative;
            }
            .summary-header::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320"><path fill="%23ffffff" fill-opacity="0.1" d="M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,144C960,149,1056,139,1152,128C1248,117,1344,107,1392,101.3L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path></svg>');
                background-size: cover;
                border-radius: 12px 12px 0 0;
            }
            .summary-header h3 {
                margin: 0 0 12px 0;
                font-size: 24px;
                font-weight: bold;
                position: relative;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .summary-header .customer-name {
                font-size: 19px;
                opacity: 0.95;
                margin-bottom: 8px;
                position: relative;
                font-weight: 600;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 18px;
                margin: 25px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 2px solid transparent;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                position: relative;
                overflow: hidden;
            }
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 4px;
                background: linear-gradient(90deg, transparent, currentColor, transparent);
            }
            .stat-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 16px rgba(0,0,0,0.12);
            }
            .stat-card.danger { border-color: #f44336; color: #f44336; }
            .stat-card.danger::before { background: linear-gradient(90deg, transparent, #f44336, transparent); }
            .stat-card.warning { border-color: #ff9800; color: #ff9800; }
            .stat-card.warning::before { background: linear-gradient(90deg, transparent, #ff9800, transparent); }
            .stat-card.success { border-color: #4caf50; color: #4caf50; }
            .stat-card.success::before { background: linear-gradient(90deg, transparent, #4caf50, transparent); }
            .stat-icon { font-size: 32px; margin-bottom: 8px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)); }
            .stat-number { font-size: 32px; font-weight: bold; margin: 8px 0; text-shadow: 0 1px 2px rgba(0,0,0,0.1); }
            .stat-label { font-size: 12px; color: #666; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
            .invoices-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                border-radius: 12px;
                overflow: hidden;
            }
            .invoices-table thead { background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%); color: white; }
            .invoices-table th { padding: 14px 10px; text-align: center; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
            .invoices-table td { padding: 12px 10px; text-align: center; border-bottom: 1px solid #e0e0e0; font-size: 13px; background: white; }
            .invoices-table tbody tr { transition: all 0.2s ease; }
            .invoices-table tbody tr:hover { background: #f0f7ff !important; transform: scale(1.01); }
            .invoices-table tbody tr:last-child td { border-bottom: none; }
            .invoice-link { color: #1976d2; font-weight: bold; text-decoration: none; transition: all 0.2s; }
            .invoice-link:hover { color: #0d47a1; text-decoration: underline; }
            .status-badge { padding: 5px 12px; border-radius: 16px; font-size: 11px; font-weight: bold; display: inline-block; text-transform: uppercase; letter-spacing: 0.3px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status-overdue { background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%); color: white; }
            .status-unpaid { background: linear-gradient(135deg, #f57c00 0%, #ff9800 100%); color: white; }
            .status-partial { background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%); color: white; }
            .amount-outstanding { color: #d32f2f; font-weight: bold; font-size: 14px; }
            .amount-paid { color: #388e3c; font-weight: 600; }
            .section-title { font-size: 17px; font-weight: bold; color: #1976d2; margin: 25px 0 15px 0; padding: 12px 15px; background: linear-gradient(90deg, #e3f2fd 0%, transparent 100%); border-right: 4px solid #1976d2; border-radius: 4px; }
            .table-footer { background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%) !important; font-weight: bold; font-size: 15px; box-shadow: 0 -2px 8px rgba(0,0,0,0.05); }
            .copyright { text-align: center; margin-top: 20px; padding: 12px 15px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); border-radius: 10px; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.2); position: relative; overflow: hidden; border: 1px solid rgba(255, 215, 0, 0.3); }
            .copyright::after { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); animation: shine 3s infinite; }
            @keyframes shine { 0% { left: -100%; } 100% { left: 100%; } }
            .copyright-content { position: relative; z-index: 1; display: flex; align-items: center; justify-content: center; gap: 8px; }
            .copyright-logo { font-size: 18px; animation: float 3s ease-in-out infinite; }
            @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-3px); } }
            .copyright-brand { font-size: 16px; font-weight: 900; background: linear-gradient(135deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: 2px; }
            .copyright-text { font-size: 11px; color: #e0e0e0; font-weight: 500; }
            .copyright-year { color: #b0b0b0; font-size: 10px; }
            .row-overdue { background: linear-gradient(90deg, #ffebee 0%, #ffcdd2 100%) !important; border-right: 4px solid #f44336 !important; }
            .sales-person-badge { background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 100%); color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; display: inline-block; box-shadow: 0 2px 4px rgba(74, 20, 140, 0.3); }
        </style>

        <div class="customer-summary-container">
            <div class="summary-header">
                <h3>📊 ملخص حساب العميل</h3>
                <div class="customer-name">🏢 ${frm.doc.customer}</div>
            </div>

            <div class="stats-grid">
                <div class="stat-card danger">
                    <div class="stat-icon">💰</div>
                    <div class="stat-label">إجمالي المستحق</div>
                    <div class="stat-number">${format_currency(total_outstanding)}</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">📝</div>
                    <div class="stat-label">عدد الفواتير المستحقة</div>
                    <div class="stat-number">${total_invoices}</div>
                </div>
                <div class="stat-card ${overdue_invoices > 0 ? 'danger' : 'success'}">
                    <div class="stat-icon">${overdue_invoices > 0 ? '⚠️' : '✅'}</div>
                    <div class="stat-label">فواتير متأخرة</div>
                    <div class="stat-number">${overdue_invoices}</div>
                </div>
            </div>

            <div class="section-title">📋 تفاصيل الفواتير المستحقة</div>

            <table class="invoices-table">
                <thead>
                    <tr>
                        <th>رقم الفاتورة</th>
                        <th>التاريخ</th>
                        <th>تاريخ الاستحقاق</th>
                        <th>المندوب</th>
                        <th>الإجمالي</th>
                        <th>المدفوع</th>
                        <th>المتبقي</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
    `;

    invoices.forEach(inv => {
        let is_overdue = false;
        let days_overdue = 0;

        if (inv.due_date) {
            days_overdue = frappe.datetime.get_diff(frappe.datetime.get_today(), inv.due_date);
            is_overdue = days_overdue > 0;
        } else {
            let days_since_posting = frappe.datetime.get_diff(frappe.datetime.get_today(), inv.posting_date);
            is_overdue = days_since_posting > 30;
            days_overdue = days_since_posting;
        }

        let status_html = '';
        if (is_overdue) {
            status_html = `<span class="status-badge status-overdue">متأخر ${days_overdue} يوم</span>`;
        } else if (inv.paid_amount > 0) {
            status_html = `<span class="status-badge status-partial">مدفوع جزئياً</span>`;
        } else {
            status_html = `<span class="status-badge status-unpaid">غير مدفوع</span>`;
        }

        let sales_person_html = inv.sales_person && inv.sales_person !== '-'
            ? `<span class="sales-person-badge">👤 ${inv.sales_person}</span>`
            : '<span style="color: #999;">-</span>';

        html += `
            <tr class="${is_overdue ? 'row-overdue' : ''}">
                <td>
                    <a href="/app/sales-invoice/${inv.name}" target="_blank" class="invoice-link">
                        ${inv.name}
                    </a>
                </td>
                <td>${frappe.datetime.str_to_user(inv.posting_date)}</td>
                <td>${inv.due_date ? frappe.datetime.str_to_user(inv.due_date) : '<span style="color: #999;">-</span>'}</td>
                <td>${sales_person_html}</td>
                <td>${format_currency(inv.grand_total)}</td>
                <td class="amount-paid">${format_currency(inv.paid_amount || 0)}</td>
                <td class="amount-outstanding">${format_currency(inv.outstanding_amount)}</td>
                <td>${status_html}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
                <tfoot>
                    <tr class="table-footer">
                        <td colspan="6" style="text-align: right; padding: 15px;">
                            <strong>الإجمالي المستحق:</strong>
                        </td>
                        <td class="amount-outstanding" style="font-size: 17px;">
                            <strong>${format_currency(total_outstanding)}</strong>
                        </td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>

            <div class="copyright">
                <div class="copyright-content">
                    <span class="copyright-logo">🚀</span>
                    <span class="copyright-brand">SPS</span>
                    <span class="copyright-text">Smart Plan Solutions</span>
                    <span class="copyright-year">© ${new Date().getFullYear()}</span>
                </div>
            </div>
        </div>
    `;

    let dialog = frappe.msgprint({
        title: `💼 حساب العميل - ${frm.doc.customer}`,
        message: html,
        indicator: total_outstanding > 0 ? 'red' : 'green',
        wide: true
    });

    setTimeout(() => {
        dialog.$wrapper.find('.modal-dialog').css('max-width', '1300px');
    }, 100);
}
