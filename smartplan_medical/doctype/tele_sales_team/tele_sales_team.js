// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tele Sales Team', {
	refresh: function(frm) {
		// Add button to create sales invoice
		if (frm.doc.name && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('إنشاء فاتورة مبيعات'), function() {
				frappe.new_doc('Sales Invoice', {
					'custom_tele_sales_employee': frm.doc.name
				});
			});
		}
	},
	
	monthly_target: function(frm) {
		// Calculate expected commission
		if (frm.doc.monthly_target && frm.doc.commission_per_million) {
			let expected_commission = (frm.doc.monthly_target / 1000000) * frm.doc.commission_per_million;
			frappe.msgprint(__('العمولة المتوقعة: {0} جنيه', [expected_commission.toFixed(2)]));
		}
	}
});
