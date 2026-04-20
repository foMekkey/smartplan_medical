frappe.ui.form.on("Sales Order Item", {
    item_code(frm, cdt, cdn) {
        load_stock(frm, cdt, cdn);
    },

    warehouse(frm, cdt, cdn) {
        load_stock(frm, cdt, cdn);
    },

    qty(frm, cdt, cdn) {
        validate_qty(frm, cdt, cdn);
    }
});

function load_stock(frm, cdt, cdn) {

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

            let actual = r.message || 0;

            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Stock Reservation",
                    filters: {
                        item_code: row.item_code,
                        warehouse: warehouse
                    },
                    fields: ["qty"]
                },
                callback(res) {

                    let reserved = 0;
                    (res.message || []).forEach(d => reserved += d.qty);

                    frappe.model.set_value(cdt, cdn, "custom_reserved_qty", reserved);
                    frappe.model.set_value(cdt, cdn, "custom_available_qty", actual - reserved);

                }
            });
        }
    });
}

function validate_qty(frm, cdt, cdn) {

    let row = locals[cdt][cdn];
    let warehouse = row.warehouse || frm.doc.set_warehouse;
    let available = row.custom_available_qty || 0;

    if (row.qty <= available) return;

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
                <div>
                    <h4 style="color:#d9534f">لا يمكن حجز كمية أكبر من المتاح</h4>

                    <b>الصنف:</b> ${row.item_code}<br>
                    <b>المخزن:</b> ${warehouse}<br>
                    <b>المتاح:</b> ${available}<br>
                    <b>المطلوب:</b> ${row.qty}<br><br>

                    <b>المتاح في مخازن أخرى:</b>
                    <table class="table table-bordered">
                        <tr>
                            <th>المخزن</th>
                            <th>الكمية</th>
                        </tr>
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
                html += `<tr><td colspan="2">لا يوجد رصيد في مخازن أخرى</td></tr>`;
            }

            html += "</table></div>";

            frappe.msgprint({
                title: "Stock Availability",
                message: html,
                indicator: "red"
            });
        }
    });
}
