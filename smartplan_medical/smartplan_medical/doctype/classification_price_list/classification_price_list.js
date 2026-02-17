frappe.ui.form.on("Classification Price List", {
    // No special logic needed on parent — validation is server-side
});

frappe.ui.form.on("Classification Price List Item", {
    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // Filter batch by selected item
        if (row.item_code) {
            // Fetch standard selling rate from Item Price
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Item Price",
                    filters: {
                        item_code: row.item_code,
                        selling: 1,
                    },
                    fields: ["price_list_rate"],
                    order_by: "modified desc",
                    limit_page_length: 1,
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        frappe.model.set_value(
                            cdt,
                            cdn,
                            "standard_rate",
                            r.message[0].price_list_rate
                        );
                    }
                },
            });
        }
    },

    batch_no(frm, cdt, cdn) {
        // Expiry date is fetched automatically via fetch_from
        // Trigger discount recalculation
        calc_discounted_rate(frm, cdt, cdn);
    },

    standard_rate(frm, cdt, cdn) {
        calc_discounted_rate(frm, cdt, cdn);
    },

    discount_percentage(frm, cdt, cdn) {
        calc_discounted_rate(frm, cdt, cdn);
    },
});

function calc_discounted_rate(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let rate = parseFloat(row.standard_rate) || 0;
    let discount = parseFloat(row.discount_percentage) || 0;
    let discounted = rate * (1 - discount / 100);
    frappe.model.set_value(cdt, cdn, "discounted_rate", discounted);
}
