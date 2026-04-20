frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        frm.set_query("custom_sales_person", () => {
            return {
                filters: [
                    ["Employee", "custom_مندوب_مبيعات", "=", 1]
                ]
            };
        });
    },
    
    customer(frm) {
        console.log('Customer changed to:', frm.doc.customer);
        
        if (frm.doc.customer) {
            // طريقة مباشرة أكتر
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.customer
                },
                callback(r) {
                    console.log('Customer data:', r.message);
                    
                    if (r.message && r.message.custom_sales_person) {
                        console.log('Setting sales person:', r.message.custom_sales_person);
                        frm.set_value('custom_sales_person', r.message.custom_sales_person);
                        
                        frappe.show_alert({
                            message: 'تم تحديد المندوب: ' + r.message.custom_sales_person,
                            indicator: 'green'
                        }, 3);
                    } else {
                        console.log('No sales person found for customer');
                        frappe.show_alert({
                            message: 'العميل ليس له مندوب مرتبط',
                            indicator: 'orange'
                        }, 3);
                    }
                },
                error(err) {
                    console.error('Error fetching customer:', err);
                }
            });
        } else {
            frm.set_value('custom_sales_person', '');
        }
    }
});