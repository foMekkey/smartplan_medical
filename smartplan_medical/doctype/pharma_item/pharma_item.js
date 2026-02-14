// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pharma Item', {
	refresh: function(frm) {
		// Add custom indicators
		if (frm.doc.expiry_discount_percent > 0) {
			frm.dashboard.add_indicator(__('خصم قرب صلاحية'), 'orange');
		}
	},
	
	purchase_price: function(frm) {
		calculate_company_cost(frm);
	},
	
	purchase_discount_percent: function(frm) {
		calculate_company_cost(frm);
	},
	
	public_price: function(frm) {
		calculate_profit_margin(frm);
	}
});

function calculate_company_cost(frm) {
	if (frm.doc.purchase_price && frm.doc.purchase_discount_percent) {
		let discount = frm.doc.purchase_price * (frm.doc.purchase_discount_percent / 100);
		frm.set_value('company_cost', frm.doc.purchase_price - discount);
	} else {
		frm.set_value('company_cost', frm.doc.purchase_price || 0);
	}
}

function calculate_profit_margin(frm) {
	if (frm.doc.company_cost && frm.doc.public_price) {
		let profit = frm.doc.public_price - frm.doc.company_cost;
		let profit_percent = (profit / frm.doc.company_cost) * 100;
		frappe.msgprint(__('هامش الربح: {0} جنيه ({1}%)', 
			[profit.toFixed(2), profit_percent.toFixed(2)]));
	}
}
