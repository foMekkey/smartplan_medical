// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pharma Warehouse', {
	refresh: function(frm) {
		// Custom buttons and actions
		if (frm.doc.expiry_date) {
			let days_to_expiry = frappe.datetime.get_day_diff(frm.doc.expiry_date, frappe.datetime.nowdate());
			if (days_to_expiry <= frm.doc.expiry_alert_days && days_to_expiry >= 0) {
				frm.dashboard.add_indicator(__('تنبيه انتهاء صلاحية'), 'orange');
			}
		}
	}
});
