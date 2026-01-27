// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tele Sales Order', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 1 && frm.doc.status === "Approved") {
			frm.add_custom_button(__('إنشاء إذن صرف'), function() {
				frappe.model.open_mapped_doc({
					method: "smartplan_medical.smartplan_medical.doctype.tele_sales_order.tele_sales_order.make_warehouse_dispatch",
					frm: frm
				});
			}, __("Actions"));
		}
		
		// Approval button
		if (frm.doc.docstatus === 0 && frm.doc.requires_approval && !frm.doc.approved_by) {
			if (frappe.user.has_role("Sales Manager")) {
				frm.add_custom_button(__('موافقة'), function() {
					frm.call({
						method: 'approve_order',
						doc: frm.doc,
						callback: function(r) {
							frm.reload_doc();
						}
					});
				}).addClass('btn-primary');
			}
		}
		
		// Status indicators
		if (frm.doc.requires_approval) {
			frm.dashboard.add_indicator(__('يتطلب موافقة'), 'orange');
		}
		if (frm.doc.status === "Approved") {
			frm.dashboard.add_indicator(__('معتمد'), 'green');
		}
	},
	
	customer: function(frm) {
		// Load customer's assigned tele sales employee
		if (frm.doc.customer) {
			frappe.db.get_value('Pharma Customer', frm.doc.customer, 'assigned_tele_sales')
				.then(r => {
					if (r.message && r.message.assigned_tele_sales) {
						frm.set_value('tele_sales_employee', r.message.assigned_tele_sales);
					}
				});
		}
	},
	
	additional_discount_percent: function(frm) {
		calculate_totals(frm);
	}
});

frappe.ui.form.on('Tele Sales Order Item', {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			// Fetch item details
			frappe.db.get_value('Pharma Item', row.item_code, ['public_price', 'item_discount_percent'])
				.then(r => {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'rate', r.message.public_price);
						frappe.model.set_value(cdt, cdn, 'max_discount_allowed', r.message.item_discount_percent);
					}
				});
		}
	},
	
	qty: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	
	item_discount_percent: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// Validate discount
		if (row.item_discount_percent > row.max_discount_allowed) {
			frappe.msgprint(__('الخصم يتجاوز الحد المسموح ({0}%)', [row.max_discount_allowed]));
		}
		calculate_item_amount(frm, cdt, cdn);
	},
	
	items_remove: function(frm) {
		calculate_totals(frm);
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let amount = flt(row.qty) * flt(row.rate);
	let discount = amount * flt(row.item_discount_percent) / 100;
	let net_amount = amount - discount;
	
	frappe.model.set_value(cdt, cdn, 'amount', amount);
	frappe.model.set_value(cdt, cdn, 'discount_amount', discount);
	frappe.model.set_value(cdt, cdn, 'net_amount', net_amount);
	
	calculate_totals(frm);
}

function calculate_totals(frm) {
	let total_amount = 0;
	let total_discount = 0;
	
	frm.doc.items.forEach(function(item) {
		total_amount += flt(item.amount);
		total_discount += flt(item.discount_amount);
	});
	
	// Add additional discount
	let additional_discount = total_amount * flt(frm.doc.additional_discount_percent) / 100;
	total_discount += additional_discount;
	
	let net_amount = total_amount - total_discount;
	let total_discount_percent = total_amount ? (total_discount / total_amount) * 100 : 0;
	
	frm.set_value('total_amount', total_amount);
	frm.set_value('discount_amount', total_discount);
	frm.set_value('net_amount', net_amount);
	frm.set_value('total_discount_percent', total_discount_percent);
}
