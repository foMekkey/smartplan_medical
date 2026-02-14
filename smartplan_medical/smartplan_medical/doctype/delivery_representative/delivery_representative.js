// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Representative', {
	refresh: function(frm) {
		// Add custom button to view route details
		if (frm.doc.linked_route) {
			frm.add_custom_button(__('عرض تفاصيل الخط'), function() {
				frappe.set_route('Form', 'Delivery Route', frm.doc.linked_route);
			});
		}
		
		// Add custom button to view vehicle details
		if (frm.doc.linked_vehicle) {
			frm.add_custom_button(__('عرض تفاصيل السيارة'), function() {
				frappe.set_route('Form', 'Delivery Vehicle', frm.doc.linked_vehicle);
			});
		}
	}
});
