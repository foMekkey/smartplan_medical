// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Warehouse Dispatch', {
	refresh: function(frm) {
		// Status indicators
		if (frm.doc.status === "Dispatched") {
			frm.dashboard.add_indicator(__('تم الصرف'), 'green');
		} else if (frm.doc.status === "Pending") {
			frm.dashboard.add_indicator(__('قيد الانتظار'), 'orange');
		}
		
		// Custom buttons
		if (frm.doc.docstatus === 1 && frm.doc.status === "Dispatched") {
			frm.add_custom_button(__('إنشاء التوصيل والتحصيل'), function() {
				frappe.model.open_mapped_doc({
					method: "smartplan_medical.smartplan_medical.doctype.warehouse_dispatch.warehouse_dispatch.make_delivery_collection",
					frm: frm
				});
			}, __("Actions"));
		}
		
		// View linked documents
		if (frm.doc.stock_entry) {
			frm.add_custom_button(__('عرض الحركة المخزنية'), function() {
				frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
			}, __("View"));
		}
		
		if (frm.doc.delivery_note) {
			frm.add_custom_button(__('عرض إذن التسليم'), function() {
				frappe.set_route('Form', 'Delivery Note', frm.doc.delivery_note);
			}, __("View"));
		}
	},
	
	tele_sales_order: function(frm) {
		if (frm.doc.tele_sales_order) {
			// Load items from Tele Sales Order
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Tele Sales Order',
					name: frm.doc.tele_sales_order
				},
				callback: function(r) {
					if (r.message) {
						// Clear existing items
						frm.clear_table('items');
						
						// Add items from order
						r.message.items.forEach(function(item) {
							let row = frm.add_child('items');
							row.item_code = item.item_code;
							row.qty = item.qty;
							row.rate = item.net_amount / item.qty;
						});
						
						frm.refresh_field('items');
						frm.trigger('calculate_totals');
					}
				}
			});
		}
	},
	
	warehouse: function(frm) {
		// Refresh stock availability
		frm.trigger('check_stock_availability');
	},
	
	fefo_selection_method: function(frm) {
		if (frm.doc.fefo_selection_method === "Auto") {
			frappe.msgprint(__('سيتم اختيار الدفعات تلقائياً عند الحفظ'));
		}
	}
});

frappe.ui.form.on('Warehouse Dispatch Item', {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code && frm.doc.warehouse) {
			// Get available stock
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Bin',
					filters: {
						item_code: row.item_code,
						warehouse: frm.doc.warehouse
					},
					fieldname: 'actual_qty'
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'available_qty', r.message.actual_qty || 0);
					}
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
	
	items_remove: function(frm) {
		frm.trigger('calculate_totals');
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let amount = flt(row.qty) * flt(row.rate);
	frappe.model.set_value(cdt, cdn, 'amount', amount);
	frm.trigger('calculate_totals');
}

frappe.ui.form.on('Warehouse Dispatch', {
	calculate_totals: function(frm) {
		let total_qty = 0;
		let total_amount = 0;
		
		frm.doc.items.forEach(function(item) {
			total_qty += flt(item.qty);
			total_amount += flt(item.amount);
		});
		
		frm.set_value('total_qty', total_qty);
		frm.set_value('total_amount', total_amount);
	},
	
	check_stock_availability: function(frm) {
		if (!frm.doc.warehouse) return;
		
		frm.doc.items.forEach(function(item) {
			if (item.item_code) {
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
						doctype: 'Bin',
						filters: {
							item_code: item.item_code,
							warehouse: frm.doc.warehouse
						},
						fieldname: 'actual_qty'
					},
					callback: function(r) {
						if (r.message) {
							let available = r.message.actual_qty || 0;
							frappe.model.set_value(item.doctype, item.name, 'available_qty', available);
							
							if (available < item.qty) {
								frappe.msgprint({
									title: __('تحذير'),
									indicator: 'orange',
									message: __('الكمية المتاحة للصنف {0} هي {1} فقط', [item.item_code, available])
								});
							}
						}
					}
				});
			}
		});
	}
});
