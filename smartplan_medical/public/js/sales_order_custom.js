/**
 * Sales Order Custom Script - Fetch New Stock & Expiring Stock Items
 * Adds buttons to fetch recently received items and expiring items with batch & expiry details
 */

frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        // Remove mandatory from delivery_date
        frm.set_df_property('delivery_date', 'reqd', 0);
        let grid = frm.fields_dict.items.grid;
        grid.update_docfield_property('delivery_date', 'reqd', 0);
        grid.update_docfield_property('delivery_date', 'in_list_view', 0);
        grid.refresh();

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

            // Show auto-cancel countdown timer
            show_auto_cancel_timer(frm);

            // Add stock popup button to items grid
            add_stock_buttons_to_grid(frm);
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

        // Populate price before discount for existing items
        let total_before = 0;
        (frm.doc.items || []).forEach(row => {
            if (row.price_list_rate && !row.custom_price_before_discount) {
                frappe.model.set_value(row.doctype, row.name, 'custom_price_before_discount', row.price_list_rate);
            }
            total_before += (parseFloat(row.price_list_rate) || 0) * (parseFloat(row.qty) || 0);
        });
        if (total_before && !frm.doc.custom_total_before_discount) {
            frm.set_value('custom_total_before_discount', total_before);
        }

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

        // Auto-set sales person from customer + fetch classification pricing
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

                    // Fetch classification pricing
                    let classification = r.message && r.message.custom_classification;
                    if (classification) {
                        fetch_and_apply_classification_pricing(frm, classification);
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
    qty(frm, cdt, cdn) {
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },

    // Item Stock availability popup — shows all warehouses with reservations
    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item_code) return;
        show_stock_popup(frm, cdt, cdn);

        // Auto-apply classification pricing discount if available
        setTimeout(() => {
            apply_classification_discount_to_item(frm, cdt, cdn);
        }, 500);
    },

    // Add reopen button when item row form renders
    form_render(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item_code) return;

        let grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
        if (!grid_row) return;

        // Remove any existing button to avoid duplicates
        $(grid_row.wrapper).find('.btn-stock-popup').remove();

        // Add a stock popup button
        let btn = $(`<button class="btn btn-xs btn-default btn-stock-popup"
            style="margin: 4px 0; font-size: 11px; padding: 2px 10px; border-radius: 6px;">
            📦 رصيد الصنف
        </button>`);
        btn.on('click', function (e) {
            e.stopPropagation();
            show_stock_popup(frm, cdt, cdn);
        });

        // Append to the form area of the row
        $(grid_row.wrapper).find('.frappe-control[data-fieldname="item_code"]').append(btn);
    },
});

// Add per-row stock popup buttons to the items grid
function add_stock_buttons_to_grid(frm) {
    let grid = frm.fields_dict.items.grid;
    setTimeout(() => {
        grid.grid_rows.forEach(grid_row => {
            let row = grid_row.doc;
            let $row = $(grid_row.row);

            // Remove existing to avoid duplicates
            $row.find('.btn-row-stock').remove();

            if (row.item_code) {
                let btn = $(`<button class="btn btn-xs btn-row-stock"
                    style="padding: 1px 8px; font-size: 11px; border-radius: 4px;
                    background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9;
                    cursor: pointer; margin-right: 4px; line-height: 1.4;"
                    title="رصيد الصنف">📦</button>`);

                btn.on('click', function (e) {
                    e.stopPropagation();
                    show_stock_popup(frm, row.doctype, row.name);
                });

                // Inject the button into the row index cell
                $row.find('.row-index').prepend(btn);
            }
        });
    }, 300);
}

// Standalone function to show stock availability popup
function show_stock_popup(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.item_code) return;

    let set_warehouse = row.warehouse || frm.doc.set_warehouse || "";

    frappe.call({
        method: "smartplan_medical.stock_api.get_item_stock_info",
        args: {
            item_code: row.item_code,
            set_warehouse: set_warehouse
        },
        callback(r) {
            if (!r.message) return;
            let data = r.message;

            // Warehouse validation
            let warehouseAlert = '';
            let disableConfirm = false;

            if (!set_warehouse) {
                warehouseAlert = `<div style="margin-bottom: 14px; padding: 10px 16px; background: #fff3e0; border: 1px solid #ffb74d; border-radius: 8px; color: #e65100; font-weight: 600; font-size: 13px;">
                    ⚠️ لم يتم اختيار مخزن — يرجى تحديد المخزن (Set Source Warehouse) أولاً
                </div>`;
                disableConfirm = true;
            } else {
                // Check if selected warehouse has stock
                let selectedWh = data.warehouses.find(w => w.warehouse === set_warehouse);
                if (!selectedWh || selectedWh.actual_qty <= 0) {
                    warehouseAlert = `<div style="margin-bottom: 14px; padding: 10px 16px; background: #ffebee; border: 1px solid #ef9a9a; border-radius: 8px; color: #c62828; font-weight: 600; font-size: 13px;">
                        ❌ المخزن <b>${set_warehouse}</b> لا يحتوي على كميات من الصنف
                    </div>`;
                    disableConfirm = true;
                }
            }

            // Build the popup HTML
            let html = `
                <div style="font-family: inherit;">
                    ${warehouseAlert}
                    <!-- Summary Header -->
                    <div style="display: flex; gap: 15px; margin-bottom: 16px; flex-wrap: wrap;">
                        <div style="flex:1; min-width:120px; padding: 12px 16px; border-radius: 8px;
                            background: linear-gradient(135deg, #e8f5e9, #c8e6c9); text-align: center;">
                            <div style="font-size: 11px; color: #2e7d32; font-weight: 600; margin-bottom: 4px;">إجمالي المخزون</div>
                            <div style="font-size: 22px; font-weight: 700; color: #1b5e20;">${data.total_actual}</div>
                        </div>
                        <div style="flex:1; min-width:120px; padding: 12px 16px; border-radius: 8px;
                            background: linear-gradient(135deg, #fff3e0, #ffe0b2); text-align: center;">
                            <div style="font-size: 11px; color: #e65100; font-weight: 600; margin-bottom: 4px;">المحجوز</div>
                            <div style="font-size: 22px; font-weight: 700; color: #bf360c;">${data.total_reserved}</div>
                        </div>
                        <div style="flex:1; min-width:120px; padding: 12px 16px; border-radius: 8px;
                            background: linear-gradient(135deg, #e3f2fd, #bbdefb); text-align: center;">
                            <div style="font-size: 11px; color: #1565c0; font-weight: 600; margin-bottom: 4px;">المتاح للبيع</div>
                            <div style="font-size: 22px; font-weight: 700; color: #0d47a1;">${data.total_available}</div>
                        </div>
                    </div>

                    <!-- Warehouse Table -->
                    <table class="table table-bordered" style="margin-bottom: 0; font-size: 13px;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 8px 12px;">المخزن</th>
                                <th style="padding: 8px 12px; text-align: center;">المخزون</th>
                                <th style="padding: 8px 12px; text-align: center;">المحجوز</th>
                                <th style="padding: 8px 12px; text-align: center;">المتاح</th>
                                <th style="padding: 8px 12px;">تفاصيل الحجز</th>
                            </tr>
                        </thead>
                        <tbody>`;

            if (data.warehouses.length === 0) {
                html += `<tr><td colspan="5" style="text-align:center; padding: 20px; color: #d32f2f; font-weight: 600;">
                        ⛔ لا يوجد رصيد لهذا الصنف في أي مخزن
                    </td></tr>`;
            } else {
                data.warehouses.forEach(wh => {
                    // Highlight selected warehouse
                    let rowStyle = wh.is_selected
                        ? 'background: linear-gradient(135deg, #e8f5e9, #f1f8e9); border-right: 4px solid #4caf50;'
                        : '';
                    let badge = wh.is_selected
                        ? ' <span style="background:#4caf50; color:#fff; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; margin-right: 6px;">المخزن المختار ✓</span>'
                        : '';

                    // Available qty color
                    let availColor = wh.available_qty > 0 ? '#2e7d32' : '#d32f2f';

                    // Reservation details with batch allocations
                    let resHtml = '';
                    if (wh.reservations.length > 0) {
                        wh.reservations.forEach(r => {
                            let batchInfo = '';
                            if (r.batch_allocations && r.batch_allocations.length > 0) {
                                batchInfo = '<div style="margin-top: 3px; padding: 2px 0;">';
                                r.batch_allocations.forEach(ba => {
                                    batchInfo += `<span style="background: #e3f2fd; color: #1565c0; padding: 1px 6px; border-radius: 8px; font-size: 10px; margin-left: 3px;">🏷️ ${ba.batch_no}: ${ba.qty}</span>`;
                                });
                                batchInfo += '</div>';
                            }

                            resHtml += `<div style="margin: 2px 0; padding: 3px 8px; background: #fff3e0; border-radius: 4px; font-size: 11px;">
                                    <span style="color: #e65100;">📋</span>
                                    <a href="/app/sales-order/${r.sales_order}" target="_blank" style="color: #1565c0; font-weight: 600;">${r.sales_order}</a>
                                    <span style="color: #666; margin: 0 4px;">|</span>
                                    <span>${r.sales_person || '—'}</span>
                                    <span style="color: #666; margin: 0 4px;">|</span>
                                    <span style="font-weight: 600; color: #e65100;">${r.qty}</span>
                                    ${batchInfo}
                                </div>`;
                        });
                    } else {
                        resHtml = '<span style="color: #999; font-size: 11px;">لا يوجد حجز</span>';
                    }

                    html += `
                        <tr style="${rowStyle}">
                            <td style="padding: 8px 12px; font-weight: 500;">${wh.warehouse}${badge}</td>
                            <td style="padding: 8px 12px; text-align: center; font-weight: 600;">${wh.actual_qty}</td>
                            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: #e65100;">${wh.reserved_qty}</td>
                            <td style="padding: 8px 12px; text-align: center; font-weight: 700; color: ${availColor};">${wh.available_qty}</td>
                            <td style="padding: 6px 12px;">${resHtml}</td>
                        </tr>`;
                });
            }

            html += `</tbody></table>`;

            // Batch Details Section with input fields
            if (data.batches && data.batches.length > 0) {
                // Get current allocations from the row
                let currentAllocs = {};
                if (row.custom_batch_allocations) {
                    try {
                        let parsed = JSON.parse(row.custom_batch_allocations);
                        parsed.forEach(a => { currentAllocs[a.batch_no] = a.qty; });
                    } catch (e) { }
                }

                html += `
                    <div style="margin-top: 18px; padding-top: 14px; border-top: 2px solid #eee;">
                        <h5 style="margin-bottom: 10px; color: #333; font-weight: 600;">
                            🏷️ تحديد الكميات من الباتشات
                        </h5>
                        <div id="batch-alloc-msg" style="margin-bottom: 8px; padding: 8px 14px; background: #e3f2fd; border-radius: 6px; font-size: 13px; color: #1565c0; font-weight: 600;">
                            الكمية المخصصة: <b id="batch-alloc-total" style="font-size: 16px;">0</b>
                        </div>
                        <table class="table table-bordered" style="margin-bottom: 0; font-size: 13px;">
                            <thead>
                                <tr style="background: #f0f4ff;">
                                    <th style="padding: 8px 12px;">رقم الباتش</th>
                                    <th style="padding: 8px 12px; text-align: center;">الكمية</th>
                                    <th style="padding: 8px 12px; text-align: center; color: #e65100;">المحجوز</th>
                                    <th style="padding: 8px 12px; text-align: center; color: #2e7d32;">المتاح</th>
                                    <th style="padding: 8px 12px; text-align: center;">تاريخ الانتهاء</th>
                                    <th style="padding: 8px 12px; text-align: center;">الحالة</th>
                                    <th style="padding: 8px 12px; text-align: center;">الكمية المطلوبة</th>
                                </tr>
                            </thead>
                            <tbody>`;

                let today = new Date();
                data.batches.forEach((batch, idx) => {
                    let expiryDate = batch.expiry_date ? new Date(batch.expiry_date) : null;
                    let daysLeft = expiryDate ? Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24)) : null;

                    let statusBadge = '';
                    let batchRowStyle = '';
                    if (daysLeft !== null) {
                        if (daysLeft <= 0) {
                            statusBadge = '<span style="background:#d32f2f; color:#fff; padding: 2px 10px; border-radius: 12px; font-size: 11px;">منتهي ❌</span>';
                            batchRowStyle = 'background: #ffebee;';
                        } else if (daysLeft <= 90) {
                            statusBadge = `<span style="background:#ff9800; color:#fff; padding: 2px 10px; border-radius: 12px; font-size: 11px;">⚠️ ${daysLeft} يوم</span>`;
                            batchRowStyle = 'background: #fff8e1;';
                        } else {
                            statusBadge = `<span style="background:#4caf50; color:#fff; padding: 2px 10px; border-radius: 12px; font-size: 11px;">✓ ${daysLeft} يوم</span>`;
                        }
                    } else {
                        statusBadge = '<span style="color: #999;">—</span>';
                    }

                    let allocVal = currentAllocs[batch.batch_no] || 0;
                    let batchAvail = batch.available || 0;
                    let batchReserved = batch.reserved || 0;
                    let availColor = batchAvail > 0 ? '#2e7d32' : '#d32f2f';

                    html += `
                        <tr style="${batchRowStyle}">
                            <td style="padding: 8px 12px; font-weight: 600;">${batch.batch_no}</td>
                            <td style="padding: 8px 12px; text-align: center; font-weight: 600;">${batch.qty}</td>
                            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: #e65100;">${batchReserved}</td>
                            <td style="padding: 8px 12px; text-align: center; font-weight: 700; color: ${availColor};">${batchAvail}</td>
                            <td style="padding: 8px 12px; text-align: center; font-weight: 500;">${batch.expiry_date || '—'}</td>
                            <td style="padding: 8px 12px; text-align: center;">${statusBadge}</td>
                            <td style="padding: 4px 8px; text-align: center;">
                                <input type="number" class="batch-alloc-input form-control"
                                    data-batch="${batch.batch_no}" data-max="${batchAvail}"
                                    value="${allocVal}" min="0" max="${batchAvail}"
                                    style="width: 80px; margin: 0 auto; text-align: center; font-weight: 600; font-size: 14px;">
                            </td>
                        </tr>`;
                });

                html += `</tbody></table>
                        <div style="margin-top: 12px; text-align: center;">
                            <button class="btn btn-primary btn-sm" id="btn-save-batch-alloc"
                                ${disableConfirm ? 'disabled' : ''}
                                style="padding: 6px 30px; font-size: 13px; font-weight: 600; border-radius: 8px; ${disableConfirm ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                                ✅ تأكيد تخصيص الباتشات
                            </button>
                        </div>
                    </div>`;
            }

            html += `</div>`;

            let indicator = data.total_available > 0 ? "blue" : "red";

            let dialog = new frappe.ui.Dialog({
                title: `📦 رصيد الصنف: ${row.item_code}`,
                size: 'extra-large',
            });
            dialog.$body.html(html);
            dialog.show();

            // Widen the dialog
            setTimeout(() => {
                dialog.$wrapper.find('.modal-dialog').css('max-width', '1100px');
            }, 100);

            // Update total on input change
            dialog.$body.on('input', '.batch-alloc-input', function () {
                let total = 0;
                dialog.$body.find('.batch-alloc-input').each(function () {
                    let val = parseFloat($(this).val()) || 0;
                    let max = parseFloat($(this).data('max')) || 0;
                    if (val > max) { $(this).val(max); val = max; }
                    if (val < 0) { $(this).val(0); val = 0; }
                    total += val;
                });
                dialog.$body.find('#batch-alloc-total').text(total);

                let msgDiv = dialog.$body.find('#batch-alloc-msg');
                if (total > 0) {
                    msgDiv.css({ 'background': '#e8f5e9', 'color': '#2e7d32' });
                } else {
                    msgDiv.css({ 'background': '#e3f2fd', 'color': '#1565c0' });
                }
            });

            // Trigger initial total calc
            dialog.$body.find('.batch-alloc-input').first().trigger('input');

            // Save button
            dialog.$body.on('click', '#btn-save-batch-alloc', function () {
                let allocations = [];
                let total = 0;
                dialog.$body.find('.batch-alloc-input').each(function () {
                    let qty = parseFloat($(this).val()) || 0;
                    if (qty > 0) {
                        allocations.push({
                            batch_no: String($(this).attr('data-batch')),
                            qty: qty
                        });
                        total += qty;
                    }
                });

                if (total <= 0) {
                    frappe.msgprint({
                        title: 'خطأ',
                        message: 'يجب تخصيص كمية من باتش واحد على الأقل',
                        indicator: 'red'
                    });
                    return;
                }

                // Auto-set item qty to match the total batch allocation
                frappe.model.set_value(cdt, cdn, 'qty', total);

                // Save batch allocations to the row
                frappe.model.set_value(cdt, cdn, 'custom_batch_allocations', JSON.stringify(allocations));
                frm.dirty();

                // If SO is saved, also save via API
                if (frm.doc.name && !frm.doc.__islocal) {
                    frappe.call({
                        method: 'smartplan_medical.stock_api.save_batch_allocations',
                        args: {
                            so_name: frm.doc.name,
                            item_code: row.item_code,
                            allocations: JSON.stringify(allocations)
                        },
                        callback() {
                            frappe.show_alert({ message: '✅ تم حفظ تخصيص الباتشات', indicator: 'green' });
                        }
                    });
                } else {
                    frappe.show_alert({ message: '✅ تم تخصيص الباتشات — سيتم الحفظ عند حفظ الطلب', indicator: 'blue' });
                }

                dialog.hide();
            });
        }
    });
}

// Re-register remaining Sales Order Item events
frappe.ui.form.on("Sales Order Item", {
    // Calculate Discount
    custom_discount_(frm, cdt, cdn) {
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },

    price_list_rate(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'custom_price_before_discount', row.price_list_rate || 0);
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },

    items_remove(frm) {
        calculate_total_discount(frm);
    }
});



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


/**
 * Auto-Cancel Countdown Timer
 * Shows a live countdown on draft Sales Orders indicating when they will be auto-deleted.
 */
function show_auto_cancel_timer(frm) {
    // Only show on saved drafts (not new unsaved docs)
    if (frm.is_new() || frm.doc.docstatus !== 0) return;

    // Clear any existing timer
    if (frm._auto_cancel_interval) {
        clearInterval(frm._auto_cancel_interval);
        frm._auto_cancel_interval = null;
    }

    // Remove existing timer banner
    frm.$wrapper.find('.auto-cancel-timer-banner').remove();

    // Fetch timeout setting
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Selling Settings',
            fieldname: 'custom_so_auto_cancel_hours'
        },
        async: false,
        callback(r) {
            let timeout_hours = (r.message && r.message.custom_so_auto_cancel_hours) || 2;
            timeout_hours = parseFloat(timeout_hours);

            if (timeout_hours <= 0) return; // Disabled

            let creation = frappe.datetime.str_to_obj(frm.doc.creation);
            let deadline = frappe.datetime.add_to_date(creation, { hours: timeout_hours });
            let now = frappe.datetime.now_datetime();

            // Create the timer banner
            let $banner = $(`
                <div class="auto-cancel-timer-banner" style="
                    padding: 12px 20px;
                    margin: 10px 0;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    font-size: 14px;
                    font-weight: 600;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                ">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 20px;">⏳</span>
                        <span class="timer-label">الوقت المتبقي قبل الحذف التلقائي</span>
                    </div>
                    <div class="timer-value" style="
                        font-size: 22px;
                        font-weight: 700;
                        font-family: monospace;
                        letter-spacing: 2px;
                    "></div>
                </div>
            `);

            frm.$wrapper.find('.form-message').after($banner);

            function updateTimer() {
                let now_dt = new Date();
                let deadline_dt = new Date(deadline);
                let diff_ms = deadline_dt - now_dt;

                if (diff_ms <= 0) {
                    $banner.css({
                        background: 'linear-gradient(135deg, #ff4444, #cc0000)',
                        color: '#fff'
                    });
                    $banner.find('.timer-value').text('⛔ تم انتهاء الوقت - سيتم الحذف قريباً');
                    clearInterval(frm._auto_cancel_interval);
                    // Refresh after a moment
                    setTimeout(() => {
                        frm.reload_doc();
                    }, 5000);
                    return;
                }

                let total_seconds = Math.floor(diff_ms / 1000);
                let hours = Math.floor(total_seconds / 3600);
                let minutes = Math.floor((total_seconds % 3600) / 60);
                let seconds = total_seconds % 60;

                let time_str = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

                $banner.find('.timer-value').text(time_str);

                // Calculate percentage remaining
                let total_ms = timeout_hours * 3600 * 1000;
                let pct = (diff_ms / total_ms) * 100;

                if (pct > 50) {
                    $banner.css({
                        background: 'linear-gradient(135deg, #d4edda, #c3e6cb)',
                        color: '#155724',
                        border: '1px solid #c3e6cb'
                    });
                } else if (pct > 20) {
                    $banner.css({
                        background: 'linear-gradient(135deg, #fff3cd, #ffeeba)',
                        color: '#856404',
                        border: '1px solid #ffeeba'
                    });
                } else {
                    $banner.css({
                        background: 'linear-gradient(135deg, #f8d7da, #f5c6cb)',
                        color: '#721c24',
                        border: '1px solid #f5c6cb'
                    });
                    // Pulse animation for urgency
                    if (pct < 10) {
                        $banner.css('animation', 'pulse 1s infinite');
                    }
                }
            }

            // Add pulse animation
            if (!document.getElementById('auto-cancel-timer-style')) {
                $('head').append(`
                    <style id="auto-cancel-timer-style">
                        @keyframes pulse {
                            0% { opacity: 1; transform: scale(1); }
                            50% { opacity: 0.85; transform: scale(1.01); }
                            100% { opacity: 1; transform: scale(1); }
                        }
                    </style>
                `);
            }

            updateTimer();
            frm._auto_cancel_interval = setInterval(updateTimer, 1000);
        }
    });
}

// ==========================================
// Classification Pricing Auto-Apply
// ==========================================

function fetch_and_apply_classification_pricing(frm, classification) {
    /**
     * Fetch active Classification Price List for the given classification
     * and apply discounts to existing SO items.
     */
    frappe.call({
        method: "smartplan_medical.classification_pricing_api.get_classification_pricing",
        args: { classification: classification },
        callback(r) {
            if (r.message && r.message.length > 0) {
                // Store pricing data on the form for use when new items are added
                frm._classification_pricing = r.message;

                frappe.show_alert({
                    message: __("تم تحميل تسعير تصنيف العميل: {0} ({1} صنف)", [classification, r.message.length]),
                    indicator: "blue",
                }, 5);

                // Apply to existing items
                if (frm.doc.items && frm.doc.items.length > 0) {
                    frm.doc.items.forEach(function (item) {
                        if (item.item_code) {
                            apply_classification_discount_to_item(frm, item.doctype, item.name);
                        }
                    });
                }
            } else {
                frm._classification_pricing = null;
                frappe.show_alert({
                    message: __("لا توجد قائمة تسعير فعالة لتصنيف: {0}", [classification]),
                    indicator: "orange",
                }, 4);
            }
        },
    });
}

function apply_classification_discount_to_item(frm, cdt, cdn) {
    /**
     * Apply classification pricing discount to a single item row.
     * Matches by item_code (and optionally batch_no).
     */
    if (!frm._classification_pricing) return;

    let row = locals[cdt][cdn];
    if (!row || !row.item_code) return;

    let pricing = frm._classification_pricing;

    // Try exact match (item_code + batch_no) first, then item_code only
    let match = null;
    if (row.custom_batch_no) {
        match = pricing.find(
            (p) => p.item_code === row.item_code && p.batch_no === row.custom_batch_no
        );
    }
    if (!match) {
        match = pricing.find((p) => p.item_code === row.item_code);
    }

    if (match && match.discount_percentage) {
        frappe.model.set_value(cdt, cdn, "custom_discount_", match.discount_percentage);
        frappe.show_alert({
            message: __("خصم {0}% تم تطبيقه على {1}", [match.discount_percentage, row.item_code]),
            indicator: "green",
        }, 3);
    }
}

