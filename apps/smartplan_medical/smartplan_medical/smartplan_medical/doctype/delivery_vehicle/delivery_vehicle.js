// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Vehicle', {
	refresh: function(frm) {
		// Check document expiry
		check_expiry_alerts(frm, 'license_expiry', 'رخصة السيارة');
		check_expiry_alerts(frm, 'insurance_expiry', 'التأمين');
		check_expiry_alerts(frm, 'next_maintenance_date', 'موعد الصيانة');
		
		// Add button to view representative
		if (frm.doc.linked_representative) {
			frm.add_custom_button(__('عرض المندوب'), function() {
				frappe.set_route('Form', 'Delivery Representative', frm.doc.linked_representative);
			});
		}
	}
});

function check_expiry_alerts(frm, field, label) {
	if (frm.doc[field]) {
		let days_diff = frappe.datetime.get_day_diff(frm.doc[field], frappe.datetime.nowdate());
		if (days_diff <= 30 && days_diff >= 0) {
			frm.dashboard.add_indicator(__('{0} ينتهي قريباً ({1} يوم)', [label, days_diff]), 'orange');
		} else if (days_diff < 0) {
			frm.dashboard.add_indicator(__('{0} منتهي', [label]), 'red');
		}
	}
}
