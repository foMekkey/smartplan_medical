frappe.ui.form.on("Sales Order Item", {
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
    }
});
