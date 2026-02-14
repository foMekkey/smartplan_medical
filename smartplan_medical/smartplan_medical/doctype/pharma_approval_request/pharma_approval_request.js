// Copyright (c) 2026, Smartplan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pharma Approval Request", {
    refresh(frm) {
        set_status_indicator(frm);
        add_action_buttons(frm);
        setup_field_colors(frm);
    },
    
    current_value(frm) {
        calculate_exceeded(frm);
    },
    
    limit_value(frm) {
        calculate_exceeded(frm);
    },
    
    reference_doctype(frm) {
        frm.set_value("reference_docname", "");
    }
});

function set_status_indicator(frm) {
    const status_colors = {
        "مسودة": "red",
        "مُرسل": "blue",
        "قيد المراجعة": "orange",
        "مُعتمد": "green",
        "مرفوض": "red",
        "مُغلق": "grey"
    };
    
    const color = status_colors[frm.doc.workflow_state] || "grey";
    frm.page.set_indicator(frm.doc.workflow_state, color);
}

function add_action_buttons(frm) {
    if (frm.doc.docstatus !== 1) return;
    
    // أزرار الموافقة والرفض
    if (["مُرسل", "قيد المراجعة"].includes(frm.doc.workflow_state)) {
        
        // زر بدء المراجعة
        if (frm.doc.workflow_state === "مُرسل") {
            frm.add_custom_button(__("بدء المراجعة"), function() {
                frm.call({
                    method: "set_under_review",
                    doc: frm.doc,
                    freeze: true,
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }, __("إجراءات"));
        }
        
        // زر الموافقة
        frm.add_custom_button(__("موافقة"), function() {
            frappe.prompt({
                fieldname: "remarks",
                fieldtype: "Small Text",
                label: __("ملاحظات الموافقة")
            }, function(values) {
                frm.call({
                    method: "approve",
                    doc: frm.doc,
                    args: { remarks: values.remarks },
                    freeze: true,
                    freeze_message: __("جاري الموافقة..."),
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }, __("الموافقة على الطلب"), __("موافقة"));
        }, __("إجراءات")).addClass("btn-success");
        
        // زر الرفض
        frm.add_custom_button(__("رفض"), function() {
            frappe.prompt({
                fieldname: "remarks",
                fieldtype: "Small Text",
                label: __("سبب الرفض"),
                reqd: 1
            }, function(values) {
                frm.call({
                    method: "reject",
                    doc: frm.doc,
                    args: { remarks: values.remarks },
                    freeze: true,
                    freeze_message: __("جاري الرفض..."),
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }, __("رفض الطلب"), __("رفض"));
        }, __("إجراءات")).addClass("btn-danger");
    }
    
    // رابط المستند المرجعي
    if (frm.doc.reference_docname) {
        frm.add_custom_button(__(frm.doc.reference_docname), function() {
            frappe.set_route("Form", frm.doc.reference_doctype, frm.doc.reference_docname);
        }, __("فتح المستند"));
    }
}

function calculate_exceeded(frm) {
    if (frm.doc.current_value && frm.doc.limit_value) {
        const exceeded = Math.max(0, frm.doc.current_value - frm.doc.limit_value);
        frm.set_value("exceeded_value", exceeded);
    }
}

function setup_field_colors(frm) {
    // تلوين قيمة التجاوز
    if (frm.doc.exceeded_value > 0) {
        frm.get_field("exceeded_value").$wrapper.find(".control-value").css("color", "red");
    }
    
    // تلوين الأولوية
    const priority_colors = {
        "منخفض": "green",
        "متوسط": "blue",
        "عالي": "orange",
        "عاجل": "red"
    };
    
    const color = priority_colors[frm.doc.priority];
    if (color) {
        frm.get_field("priority").$wrapper.find(".control-value").css("color", color);
    }
}
