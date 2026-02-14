// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pharma General Settings', {
	refresh: function(frm) {
		frm.dashboard.set_headline(__('الإعدادات المركزية لإدارة دورة شركة الأدوية'));
	},
	
	max_discount_allowed: function(frm) {
		if (frm.doc.max_discount_allowed > 100) {
			frappe.msgprint(__('أقصى خصم مسموح لا يمكن أن يتجاوز 100%'));
			frm.set_value('max_discount_allowed', 100);
		}
	}
});
