// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Route', {
	refresh: function(frm) {
		// Add custom button to view route on map
		frm.add_custom_button(__('عرض الخط على الخريطة'), function() {
			frappe.msgprint(__('هذه الميزة ستكون متاحة في المرحلة الثانية'));
		});
	}
});
