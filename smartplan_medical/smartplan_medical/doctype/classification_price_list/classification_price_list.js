frappe.ui.form.on("Classification Price List", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(
                __("سحب الأصناف (Pull Items)"),
                function () {
                    show_pull_items_dialog(frm);
                },
                __("Actions")
            );
        }
    },

    classification(frm) {
        // When classification is selected, auto-show the pull dialog
        if (frm.doc.classification && frm.doc.docstatus === 0) {
            show_pull_items_dialog(frm);
        }
    },
});

frappe.ui.form.on("Classification Price List Item", {
    selling_discount(frm, cdt, cdn) {
        calc_selling_rate(frm, cdt, cdn);
    },

    standard_rate(frm, cdt, cdn) {
        calc_selling_rate(frm, cdt, cdn);
    },
});

function calc_selling_rate(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let rate = parseFloat(row.standard_rate) || 0;
    let discount = parseFloat(row.selling_discount) || 0;
    let discounted = rate * (1 - discount / 100);
    frappe.model.set_value(cdt, cdn, "discounted_rate", discounted);
}

function show_pull_items_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __("سحب الأصناف المشتراة (Pull Purchased Items)"),
        size: "small",
        fields: [
            {
                fieldname: "purchase_from_date",
                fieldtype: "Date",
                label: __("تاريخ بداية الشراء (Purchase From)"),
                reqd: 1,
                default: frm.doc.from_date || frappe.datetime.month_start(),
            },
            {
                fieldname: "purchase_to_date",
                fieldtype: "Date",
                label: __("تاريخ نهاية الشراء (Purchase To)"),
                reqd: 1,
                default: frm.doc.to_date || frappe.datetime.now_date(),
            },
        ],
        primary_action_label: __("سحب الأصناف"),
        primary_action(values) {
            d.hide();

            frappe.call({
                method: "smartplan_medical.classification_pricing_api.pull_purchased_items",
                args: {
                    from_date: values.purchase_from_date,
                    to_date: values.purchase_to_date,
                },
                freeze: true,
                freeze_message: __("جاري سحب الأصناف المشتراة..."),
                callback(r) {
                    if (r.message && r.message.length > 0) {
                        // Clear existing items
                        frm.doc.items = [];
                        frm.refresh_field("items");

                        // Add pulled items
                        r.message.forEach(function (item) {
                            let row = frm.add_child("items");
                            row.item_code = item.item_code;
                            row.item_name = item.item_name;
                            row.batch_no = item.batch_no || "";
                            row.expiry_date = item.expiry_date || "";
                            row.standard_rate = item.purchase_rate || 0;
                            row.purchase_discount =
                                item.purchase_discount || 0;
                            row.selling_discount = 0;
                            row.discounted_rate = item.purchase_rate || 0;
                        });

                        frm.refresh_field("items");
                        frm.dirty();

                        frappe.show_alert({
                            message: __(
                                "تم سحب {0} صنف/باتش بنجاح",
                                [r.message.length]
                            ),
                            indicator: "green",
                        }, 5);
                    } else {
                        frappe.show_alert({
                            message: __(
                                "لا توجد أصناف مشتراة في الفترة المحددة"
                            ),
                            indicator: "orange",
                        }, 5);
                    }
                },
            });
        },
    });

    d.show();
}
