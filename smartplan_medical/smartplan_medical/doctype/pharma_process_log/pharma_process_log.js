// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pharma Process Log", {
    refresh(frm) {
        // زر إعادة المحاولة
        if (frm.doc.status === "Failed" && frm.doc.can_retry) {
            frm.add_custom_button(__("إعادة المحاولة"), function() {
                frappe.confirm(
                    __("هل تريد إعادة محاولة معالجة هذا المستند؟"),
                    function() {
                        frm.call({
                            method: "retry_process",
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __("جاري إعادة المعالجة..."),
                            callback: function(r) {
                                if (!r.exc) {
                                    frm.reload_doc();
                                    frappe.show_alert({
                                        message: __("تمت إعادة المعالجة بنجاح"),
                                        indicator: "green"
                                    });
                                }
                            }
                        });
                    }
                );
            }, __("إجراءات")).addClass("btn-primary");
        }
        
        // رابط للمستند المصدر
        if (frm.doc.source_docname) {
            frm.add_custom_button(__(frm.doc.source_docname), function() {
                frappe.set_route("Form", frm.doc.source_doctype, frm.doc.source_docname);
            }, __("فتح"));
        }
        
        // رابط للمستند الناتج
        if (frm.doc.target_docname) {
            frm.add_custom_button(__(frm.doc.target_docname), function() {
                frappe.set_route("Form", frm.doc.target_doctype, frm.doc.target_docname);
            }, __("فتح"));
        }
        
        // تلوين الحالة
        set_status_indicator(frm);
    }
});

function set_status_indicator(frm) {
    const status_colors = {
        "Pending": "orange",
        "Processing": "blue",
        "Success": "green",
        "Failed": "red",
        "Retry": "yellow"
    };
    
    const color = status_colors[frm.doc.status] || "grey";
    frm.page.set_indicator(__(frm.doc.status), color);
}
