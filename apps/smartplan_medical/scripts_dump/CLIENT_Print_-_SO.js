frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        // فلتر المندوب
        frm.set_query("custom_sales_person", () => {
            return {
                filters: [
                    ["Employee", "custom_مندوب_مبيعات", "=", 1]
                ]
            };
        });
        
        // زرار طباعة مخصص
        if (frm.doc.docstatus === 1 && !frm.is_new()) {
            frm.add_custom_button(__('طباعة الفاتورة والتسليم'), function() {
                print_invoice_and_delivery(frm);
            }, __('Print'));
        }
    },
    
    customer(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.customer
                },
                callback(r) {
                    if (r.message && r.message.custom_sales_person) {
                        frm.set_value('custom_sales_person', r.message.custom_sales_person);
                    }
                }
            });
        } else {
            frm.set_value('custom_sales_person', '');
        }
    },
    
    // بعد الـ Submit مباشرة
    on_submit(frm) {
        // انتظر ثانية عشان الـ Submit يخلص
        setTimeout(() => {
            show_print_dialog(frm);
        }, 500);
    }
});

function show_print_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('طباعة المستندات'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'print_options',
                options: `
                    <div style="padding: 20px; text-align: center;">
                        <h4 style="margin-bottom: 20px;">تم حفظ الفاتورة بنجاح!</h4>
                        <p style="margin-bottom: 20px;">هل تريد طباعة المستندات؟</p>
                    </div>
                `
            },
            {
                fieldtype: 'Check',
                fieldname: 'print_invoice',
                label: 'طباعة الفاتورة',
                default: 1
            },
            {
                fieldtype: 'Check',
                fieldname: 'print_delivery',
                label: 'طباعة إيصال التسليم',
                default: 1
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'Select',
                fieldname: 'invoice_format',
                label: 'تنسيق الفاتورة',
                options: get_print_formats('Sales Order'),
                default: 'Reunion Invoice' // غير الاسم ده للـ Print Format بتاعك
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Select',
                fieldname: 'delivery_format',
                label: 'تنسيق إيصال التسليم',
                options: get_print_formats('Delivery Note'),
                default: 'Standard'
            }
        ],
        primary_action_label: __('طباعة'),
        primary_action(values) {
            print_documents(frm, values);
            d.hide();
        },
        secondary_action_label: __('إلغاء'),
        secondary_action() {
            d.hide();
        }
    });
    
    d.show();
}

function get_print_formats(doctype) {
    let formats = ['Standard'];
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Print Format',
            filters: {
                doc_type: doctype,
                disabled: 0
            },
            fields: ['name'],
            limit_page_length: 0
        },
        async: false,
        callback(r) {
            if (r.message) {
                formats = r.message.map(f => f.name);
                if (!formats.includes('Standard')) {
                    formats.unshift('Standard');
                }
            }
        }
    });
    
    return formats.join('\n');
}

function print_documents(frm, values) {
    // طباعة الفاتورة
    if (values.print_invoice) {
        print_document(frm.doc.doctype, frm.doc.name, values.invoice_format);
    }
    
    // طباعة إيصال التسليم
    if (values.print_delivery && frm.doc.update_stock) {
        // جيب الـ Delivery Note المرتبط
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Delivery Note',
                filters: {
                    'items.against_sales_order': frm.doc.name
                },
                fields: ['name'],
                limit: 1
            },
            callback(r) {
                if (r.message && r.message.length > 0) {
                    print_document('Delivery Note', r.message[0].name, values.delivery_format);
                } else {
                    // لو مفيش Delivery Note، اطبع الفاتورة كإيصال تسليم
                    print_delivery_from_invoice(frm, values.delivery_format);
                }
            }
        });
    }
}

function print_document(doctype, docname, format) {
    let print_url = frappe.urllib.get_full_url(
        '/api/method/frappe.utils.print_format.download_pdf?' +
        'doctype=' + encodeURIComponent(doctype) +
        '&name=' + encodeURIComponent(docname) +
        '&format=' + encodeURIComponent(format) +
        '&no_letterhead=0' +
        '&letterhead=your_letterhead' + // غير ده للـ Letterhead بتاعك
        '&settings=%7B%7D' +
        '&_lang=ar'
    );
    
    // فتح في نافذة جديدة للطباعة
    let print_window = window.open(print_url);
    
    // انتظر التحميل ثم اطبع تلقائياً
    if (print_window) {
        setTimeout(() => {
            print_window.print();
        }, 1000);
    }
}

function print_delivery_from_invoice(frm, format) {
    // استخدم الفاتورة كإيصال تسليم
    let print_url = frappe.urllib.get_full_url(
        '/api/method/frappe.utils.print_format.download_pdf?' +
        'doctype=Sales Order' +
        '&name=' + encodeURIComponent(frm.doc.name) +
        '&format=' + encodeURIComponent(format) +
        '&no_letterhead=0' +
        '&settings=%7B%7D' +
        '&_lang=ar'
    );
    
    window.open(print_url);
}

function print_invoice_and_delivery(frm) {
    // نفس الـ Dialog بس من الزرار
    show_print_dialog(frm);
}