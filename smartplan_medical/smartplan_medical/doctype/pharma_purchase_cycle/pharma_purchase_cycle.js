// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pharma Purchase Cycle', {
    refresh: function (frm) {
        // Calculate totals on refresh
        calculate_totals(frm);
        
        if (frm.doc.status === "Draft" && !frm.doc.__islocal) {
            frm.add_custom_button(__('إنشاء أمر شراء'), function () {
                frm.call('create_purchase_order', {}, function (r) {
                    if (!r.exc) frm.reload_doc();
                });
            }).addClass("btn-primary");
        }

        if (frm.doc.status === "Ordered") {
            frm.add_custom_button(__('إنشاء استلام مخزني'), function () {
                frm.call('create_purchase_receipt', {}, function (r) {
                    if (!r.exc) frm.reload_doc();
                });
            }).addClass("btn-primary");
        }

        if (frm.doc.status === "Received") {
            frm.add_custom_button(__('إنشاء فاتورة'), function () {
                frm.call('create_purchase_invoice', {}, function (r) {
                    if (!r.exc) frm.reload_doc();
                });
            }).addClass("btn-primary");
        }
    },

    create_po_btn: function (frm) {
        frm.call('create_purchase_order', {}, function (r) {
            if (!r.exc) frm.reload_doc();
        });
    },

    create_pr_btn: function (frm) {
        frm.call('create_purchase_receipt', {}, function (r) {
            if (!r.exc) frm.reload_doc();
        });
    },

    create_pi_btn: function (frm) {
        frm.call('create_purchase_invoice', {}, function (r) {
            if (!r.exc) frm.reload_doc();
        });
    }
});

// Child table: Pharma Purchase Cycle Item
frappe.ui.form.on('Pharma Purchase Cycle Item', {
    qty: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    
    items_remove: function(frm) {
        calculate_totals(frm);
    }
});

function calculate_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.amount = flt(row.qty) * flt(row.rate);
    frm.refresh_field('items');
    calculate_totals(frm);
}

function calculate_totals(frm) {
    let total_qty = 0;
    let total_amount = 0;
    
    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            total_qty += flt(item.qty);
            total_amount += flt(item.amount);
        });
    }
    
    frm.set_value('total_qty', total_qty);
    frm.set_value('total_amount', total_amount);
}
