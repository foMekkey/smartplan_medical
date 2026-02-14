// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pharma Approval Matrix", {
    refresh(frm) {
        if (!frm.is_new()) {
            // زر لعرض طلبات الموافقة المرتبطة
            frm.add_custom_button(__("طلبات الموافقة"), function() {
                frappe.set_route("List", "Pharma Approval Request", {
                    approval_type: frm.doc.approval_type
                });
            }, __("عرض"));
        }
    }
});

frappe.ui.form.on("Pharma Approval Level", {
    approval_levels_add(frm, cdt, cdn) {
        // تعيين المستوى التالي تلقائياً
        let row = locals[cdt][cdn];
        let max_level = 0;
        frm.doc.approval_levels.forEach(function(r) {
            if (r.name !== cdn && r.level > max_level) {
                max_level = r.level;
            }
        });
        frappe.model.set_value(cdt, cdn, "level", max_level + 1);
    }
});
