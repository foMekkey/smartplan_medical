frappe.ui.form.on('Sales Order Item', {
    custom_discount_: function(frm, cdt, cdn) {
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },
    
    price_list_rate: function(frm, cdt, cdn) {
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },
    
    qty: function(frm, cdt, cdn) {
        apply_discount_and_calculate_total(frm, cdt, cdn);
    },
    
    items_remove: function(frm) {
        calculate_total_discount(frm);
    }
});

frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        calculate_total_discount(frm);
    }
});

function apply_discount_and_calculate_total(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (row.custom_discount_ && row.price_list_rate) {
        let discount = parseFloat(row.custom_discount_);
        
        // طبق الخصم على الصنف
        frappe.model.set_value(cdt, cdn, 'discount_percentage', discount)
            .then(() => {
                // بعد ما الخصم يتطبق، احسب الإجمالي
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
    
    frm.doc.items.forEach(function(item) {
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
    
    // حدث الحقل
    frm.set_value('custom_total_discount_amount', total_discount);
    
    // اعرض رسالة (اختياري)
    if (total_discount > 0) {
        frm.dashboard.add_indicator(
            __('Total Discount: {0}', [format_currency(total_discount, frm.doc.currency)]), 
            'orange'
        );
    }
}