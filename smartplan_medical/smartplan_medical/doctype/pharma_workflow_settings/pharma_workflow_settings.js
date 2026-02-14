// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pharma Workflow Settings", {
    refresh(frm) {
        frm.add_custom_button(__("عرض سجل العمليات"), function() {
            frappe.set_route("List", "Pharma Process Log");
        });
        
        frm.add_custom_button(__("عرض طلبات الموافقة"), function() {
            frappe.set_route("List", "Pharma Approval Request");
        });
    }
});
