// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pharma Customer', {
	refresh: function(frm) {
		// Add custom indicator based on category
		if (frm.doc.customer_category === 'عميل فئة A') {
			frm.dashboard.add_indicator(__('عميل متميز'), 'green');
		}
	},
	
	financial_volume_to: function(frm) {
		// Suggest category based on financial volume
		if (frm.doc.financial_volume_to >= 1000000) {
			frm.set_value('customer_category', 'عميل فئة A');
		} else if (frm.doc.financial_volume_to >= 500000) {
			frm.set_value('customer_category', 'عميل فئة B');
		} else {
			frm.set_value('customer_category', 'عميل فئة C');
		}
	}
});
