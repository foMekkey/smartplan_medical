/**
 * Purchase Order Custom Script
 * - Per-item discount (same as Sales Order)
 * - Calculate total discount
 */
frappe.ui.form.on("Purchase Order", {
    refresh(frm) {
        // Calculate total discount on refresh
        po_calculate_total_discount(frm);
    },
});

frappe.ui.form.on("Purchase Order Item", {
    qty(frm, cdt, cdn) {
        po_apply_discount(frm, cdt, cdn);
    },

    custom_discount_(frm, cdt, cdn) {
        po_apply_discount(frm, cdt, cdn);
    },

    price_list_rate(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'custom_price_before_discount', row.price_list_rate || 0);
        po_apply_discount(frm, cdt, cdn);
    },

    rate(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // If price_list_rate isn't set yet, use rate as the base price
        if (!row.price_list_rate && row.rate) {
            frappe.model.set_value(cdt, cdn, 'custom_price_before_discount', row.rate);
        }
    },

    items_remove(frm) {
        po_calculate_total_discount(frm);
    }
});

// ==========================================
// Purchase Order Discount Functions
// ==========================================

function po_apply_discount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    if (row.custom_discount_ && row.price_list_rate) {
        let discount = parseFloat(row.custom_discount_);

        frappe.model.set_value(cdt, cdn, 'discount_percentage', discount)
            .then(() => {
                setTimeout(() => {
                    po_calculate_total_discount(frm);
                }, 200);
            });
    }
}

function po_calculate_total_discount(frm) {
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
