// Copyright (c) 2026, SmartPlan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Commission Calculation', {
	refresh: function(frm) {
		// Status indicators
		if (frm.doc.status === "Approved") {
			frm.dashboard.add_indicator(__('معتمد'), 'green');
		} else if (frm.doc.status === "Pending Approval") {
			frm.dashboard.add_indicator(__('قيد الموافقة'), 'orange');
		} else if (frm.doc.status === "Paid") {
			frm.dashboard.add_indicator(__('تم الصرف'), 'blue');
		} else if (frm.doc.status === "Rejected") {
			frm.dashboard.add_indicator(__('مرفوض'), 'red');
		}
		
		// Calculate commission button
		if (frm.doc.docstatus === 0 && !frm.doc.commission_details.length) {
			frm.add_custom_button(__('حساب العمولة'), function() {
				frappe.call({
					method: 'calculate_commission',
					doc: frm.doc,
					callback: function(r) {
						frm.reload_doc();
						frappe.msgprint(__('تم حساب العمولة بنجاح'));
					}
				});
			}).addClass('btn-primary');
		}
		
		// Approval buttons
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending Approval") {
			if (frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager")) {
				frm.add_custom_button(__('موافقة'), function() {
					frappe.call({
						method: 'approve_commission',
						doc: frm.doc,
						callback: function(r) {
							frm.reload_doc();
						}
					});
				}, __("Actions")).addClass('btn-primary');
				
				frm.add_custom_button(__('رفض'), function() {
					frappe.prompt({
						label: __('سبب الرفض'),
						fieldname: 'reason',
						fieldtype: 'Small Text',
						reqd: 1
					}, function(values) {
						frappe.call({
							method: 'reject_commission',
							doc: frm.doc,
							args: {
								reason: values.reason
							},
							callback: function(r) {
								frm.reload_doc();
							}
						});
					}, __('رفض العمولة'));
				}, __("Actions")).addClass('btn-danger');
			}
		}
		
		// Mark as paid button
		if (frm.doc.docstatus === 1 && frm.doc.status === "Approved" && frm.doc.payment_status !== "Paid") {
			if (frappe.user.has_role("HR Manager") || frappe.user.has_role("Accounts Manager")) {
				frm.add_custom_button(__('تسجيل الصرف'), function() {
					frappe.prompt({
						label: __('مرجع الصرف'),
						fieldname: 'payment_reference',
						fieldtype: 'Data'
					}, function(values) {
						frappe.call({
							method: 'mark_as_paid',
							doc: frm.doc,
							args: {
								payment_reference: values.payment_reference
							},
							callback: function(r) {
								frm.reload_doc();
							}
						});
					}, __('تسجيل الصرف'));
				}, __("Actions")).addClass('btn-success');
			}
		}
		
		// Show summary
		if (frm.doc.total_commission) {
			let summary_html = `
				<div class="row">
					<div class="col-md-3">
						<div class="dashboard-stat">
							<div class="dashboard-stat-label">${__('عدد الطلبات')}</div>
							<div class="dashboard-stat-value">${frm.doc.total_orders || 0}</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="dashboard-stat">
							<div class="dashboard-stat-label">${__('إجمالي المبيعات')}</div>
							<div class="dashboard-stat-value">${format_currency(frm.doc.total_net_sales || 0)}</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="dashboard-stat">
							<div class="dashboard-stat-label">${__('معدل العمولة')}</div>
							<div class="dashboard-stat-value">${format_currency(frm.doc.commission_rate || 0)} / ${__('مليون')}</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="dashboard-stat">
							<div class="dashboard-stat-label">${__('إجمالي العمولة')}</div>
							<div class="dashboard-stat-value" style="color: green; font-weight: bold;">${format_currency(frm.doc.total_commission || 0)}</div>
						</div>
					</div>
				</div>
			`;
			frm.dashboard.add_section(summary_html);
		}
	},
	
	calculation_period: function(frm) {
		if (frm.doc.calculation_period === "Monthly") {
			// Set to current month
			let date = frappe.datetime.get_today();
			let first_day = frappe.datetime.month_start(date);
			let last_day = frappe.datetime.month_end(date);
			frm.set_value('from_date', first_day);
			frm.set_value('to_date', last_day);
		}
	},
	
	tele_sales_employee: function(frm) {
		// Fetch commission rate
		if (frm.doc.tele_sales_employee) {
			frappe.db.get_value('Tele Sales Team', frm.doc.tele_sales_employee, 'commission_per_million')
				.then(r => {
					if (r.message) {
						frm.set_value('commission_rate', r.message.commission_per_million);
					}
				});
		}
	}
});

frappe.ui.form.on('Commission Detail', {
	order_no: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.order_no) {
			// Show order details
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Tele Sales Order',
					name: row.order_no
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'customer', r.message.customer);
						frappe.model.set_value(cdt, cdn, 'customer_name', r.message.customer_name);
						frappe.model.set_value(cdt, cdn, 'order_date', r.message.posting_date);
						frappe.model.set_value(cdt, cdn, 'net_sales', r.message.net_amount);
						frappe.model.set_value(cdt, cdn, 'order_status', r.message.status);
					}
				}
			});
		}
	}
});
