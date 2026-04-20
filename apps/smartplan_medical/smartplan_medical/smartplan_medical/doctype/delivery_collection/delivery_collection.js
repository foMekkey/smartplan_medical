// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Collection', {
	refresh: function(frm) {
		// Status indicators
		if (frm.doc.collection_status === "Fully Collected") {
			frm.dashboard.add_indicator(__('تم التحصيل بالكامل'), 'green');
		} else if (frm.doc.collection_status === "Partially Collected") {
			frm.dashboard.add_indicator(__('تحصيل جزئي'), 'orange');
		} else if (frm.doc.collection_status === "Not Collected") {
			frm.dashboard.add_indicator(__('لم يتم التحصيل'), 'red');
		}
		
		// Custom buttons
		if (frm.doc.docstatus === 1) {
			if (frm.doc.sales_invoice) {
				frm.add_custom_button(__('عرض الفاتورة'), function() {
					frappe.set_route('Form', 'Sales Invoice', frm.doc.sales_invoice);
				}, __("View"));
			}
			
			if (frm.doc.payment_entry) {
				frm.add_custom_button(__('عرض قيد الدفع'), function() {
					frappe.set_route('Form', 'Payment Entry', frm.doc.payment_entry);
				}, __("View"));
			}
		}
		
		// Mobile-friendly: Add signature capture button
		if (frm.doc.docstatus === 0 && !frm.doc.customer_signature) {
			frm.add_custom_button(__('التقاط التوقيع'), function() {
				capture_signature(frm);
			});
		}
	},
	
	warehouse_dispatch: function(frm) {
		if (frm.doc.warehouse_dispatch) {
			// Load items from Warehouse Dispatch
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Warehouse Dispatch',
					name: frm.doc.warehouse_dispatch
				},
				callback: function(r) {
					if (r.message) {
						// Clear existing items
						frm.clear_table('items');
						
						let total = 0;
						// Add items from dispatch
						r.message.items.forEach(function(item) {
							let row = frm.add_child('items');
							row.item_code = item.item_code;
							row.qty = item.qty;
							row.delivered_qty = item.qty;
							row.rate = item.rate;
							row.amount = item.amount;
							total += item.amount;
						});
						
						frm.set_value('expected_amount', total);
						frm.set_value('collected_amount', total);
						frm.refresh_field('items');
					}
				}
			});
		}
	},
	
	payment_type: function(frm) {
		if (frm.doc.payment_type === "Cash") {
			frm.set_value('cash_amount', frm.doc.collected_amount);
			frm.set_value('cheque_amount', 0);
			frm.set_value('bank_transfer_amount', 0);
			frm.set_value('credit_amount', 0);
		} else if (frm.doc.payment_type === "Cheque") {
			frm.set_value('cheque_amount', frm.doc.collected_amount);
			frm.set_value('cash_amount', 0);
			frm.set_value('bank_transfer_amount', 0);
			frm.set_value('credit_amount', 0);
		} else if (frm.doc.payment_type === "Credit") {
			frm.set_value('credit_amount', frm.doc.collected_amount);
			frm.set_value('cash_amount', 0);
			frm.set_value('cheque_amount', 0);
			frm.set_value('bank_transfer_amount', 0);
		}
	},
	
	collected_amount: function(frm) {
		calculate_variance(frm);
	},
	
	expected_amount: function(frm) {
		calculate_variance(frm);
	}
});

frappe.ui.form.on('Delivery Collection Item', {
	delivered_qty: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		row.amount = flt(row.delivered_qty) * flt(row.rate);
		frm.refresh_field('items');
		calculate_expected_amount(frm);
	}
});

function calculate_expected_amount(frm) {
	let total = 0;
	frm.doc.items.forEach(function(item) {
		total += flt(item.amount);
	});
	frm.set_value('expected_amount', total);
}

function calculate_variance(frm) {
	let variance = flt(frm.doc.collected_amount) - flt(frm.doc.expected_amount);
	frm.set_value('variance_amount', variance);
	
	// Auto-set collection status
	if (flt(frm.doc.collected_amount) === 0) {
		frm.set_value('collection_status', 'Not Collected');
	} else if (Math.abs(variance) < 0.01) {
		frm.set_value('collection_status', 'Fully Collected');
	} else if (variance < 0) {
		frm.set_value('collection_status', 'Partially Collected');
	} else {
		frm.set_value('collection_status', 'Over Collected');
	}
}

function capture_signature(frm) {
	// This would integrate with a signature pad library in production
	let d = new frappe.ui.Dialog({
		title: __('التقاط التوقيع'),
		fields: [
			{
				fieldname: 'signature',
				fieldtype: 'Attach Image',
				label: __('التوقيع')
			}
		],
		primary_action_label: __('حفظ'),
		primary_action: function() {
			let values = d.get_values();
			if (values.signature) {
				frm.set_value('customer_signature', values.signature);
			}
			d.hide();
		}
	});
	d.show();
}
