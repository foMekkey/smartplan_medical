/**
 * Sales Invoice Custom Script - Fetch New Stock Items
 * Adds a button to fetch recently received items with batch & expiry details
 */

frappe.ui.form.on("Sales Invoice", {
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
    },
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
