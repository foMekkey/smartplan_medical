frappe.ui.form.on("Sales Order Item", {
    qty(frm, cdt, cdn) {
        show_reservation_details(frm, cdt, cdn);
    }
});

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
                            <th>الفاتورة</th>
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
