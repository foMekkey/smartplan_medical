# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, nowtime, add_days, getdate, flt


class WarehouseDispatch(Document):
	def validate(self):
		"""Validate dispatch document before save"""
		self.validate_tele_sales_order()
		self.validate_items()
		self.calculate_totals()
		self.set_status()
		
	def before_submit(self):
		"""Pre-submission validations"""
		self.validate_stock_availability()
		self.apply_fefo_logic()
		self.validate_expiry_dates()
		
	def on_submit(self):
		"""Create Stock Entry and Delivery Note on submit"""
		self.status = "Dispatched"
		self.dispatched_by = frappe.session.user
		self.create_stock_entry()
		self.create_delivery_note()
		self.update_tele_sales_order()
		self.db_set('status', 'Dispatched')
		
	def on_cancel(self):
		"""Cancel linked documents"""
		self.status = "Cancelled"
		self.cancel_linked_documents()
		self.db_set('status', 'Cancelled')
	
	def validate_tele_sales_order(self):
		"""Ensure Tele Sales Order is approved and not already dispatched"""
		if not self.tele_sales_order:
			frappe.throw(_("يجب تحديد طلب التلي سيلز"))
			
		order = frappe.get_doc("Tele Sales Order", self.tele_sales_order)
		
		if order.docstatus != 1:
			frappe.throw(_("طلب التلي سيلز غير معتمد"))
			
		if order.status == "Dispatched":
			frappe.throw(_("تم صرف هذا الطلب مسبقاً"))
			
		# Auto-populate items from order if empty
		if not self.items and order.items:
			for item in order.items:
				self.append("items", {
					"item_code": item.item_code,
					"qty": item.qty,
					"rate": item.net_amount / item.qty if item.qty else 0,
					"amount": item.net_amount
				})
	
	def validate_items(self):
		"""Validate items exist and have positive quantities"""
		if not self.items:
			frappe.throw(_("يجب إضافة أصناف للصرف"))
			
		for item in self.items:
			if not item.item_code:
				frappe.throw(_("الصنف مطلوب في السطر {0}").format(item.idx))
				
			if flt(item.qty) <= 0:
				frappe.throw(_("الكمية يجب أن تكون أكبر من صفر في السطر {0}").format(item.idx))
	
	def calculate_totals(self):
		"""Calculate total quantity and amount"""
		self.total_qty = 0
		self.total_amount = 0
		
		for item in self.items:
			item.amount = flt(item.qty) * flt(item.rate)
			self.total_qty += flt(item.qty)
			self.total_amount += flt(item.amount)
	
	def validate_stock_availability(self):
		"""Check if requested quantities are available in warehouse"""
		for item in self.items:
			available_qty = frappe.db.sql("""
				SELECT SUM(actual_qty) 
				FROM `tabBin` 
				WHERE item_code = %s AND warehouse = %s
			""", (item.item_code, self.warehouse))[0][0] or 0
			
			if flt(available_qty) < flt(item.qty):
				frappe.throw(_(
					"الكمية المتاحة للصنف {0} في المخزن {1} هي {2} فقط، والمطلوب {3}"
				).format(
					frappe.bold(item.item_code),
					frappe.bold(self.warehouse),
					frappe.bold(available_qty),
					frappe.bold(item.qty)
				))
	
	def apply_fefo_logic(self):
		"""Apply FEFO (First Expiry First Out) logic to select batches"""
		if self.fefo_selection_method != "Auto":
			return
			
		for item in self.items:
			# Get batches with earliest expiry dates
			batches = frappe.db.sql("""
				SELECT 
					sle.batch_no,
					batch.expiry_date,
					SUM(sle.actual_qty) as available_qty
				FROM `tabStock Ledger Entry` sle
				INNER JOIN `tabBatch` batch ON batch.name = sle.batch_no
				WHERE 
					sle.item_code = %s 
					AND sle.warehouse = %s
					AND sle.actual_qty > 0
					AND batch.expiry_date IS NOT NULL
					AND batch.expiry_date > %s
				GROUP BY sle.batch_no, batch.expiry_date
				HAVING available_qty > 0
				ORDER BY batch.expiry_date ASC
			""", (item.item_code, self.warehouse, today()), as_dict=1)
			
			if not batches:
				frappe.throw(_(
					"لا توجد دفعات متاحة للصنف {0} في المخزن {1}"
				).format(item.item_code, self.warehouse))
			
			# Select batches to fulfill quantity
			remaining_qty = flt(item.qty)
			selected_batches = []
			
			for batch in batches:
				if remaining_qty <= 0:
					break
					
				# Check expiry proximity
				days_to_expiry = (getdate(batch.expiry_date) - getdate(today())).days
				
				if days_to_expiry < self.near_expiry_days and not self.allow_near_expiry:
					continue
					
				batch_qty = min(flt(batch.available_qty), remaining_qty)
				selected_batches.append({
					"batch_no": batch.batch_no,
					"qty": batch_qty,
					"expiry_date": batch.expiry_date
				})
				remaining_qty -= batch_qty
			
			if remaining_qty > 0:
				frappe.throw(_(
					"لا يمكن تلبية الكمية المطلوبة {0} للصنف {1} من الدفعات المتاحة"
				).format(item.qty, item.item_code))
			
			# Store selected batches in item
			item.selected_batches = frappe.as_json(selected_batches)
	
	def validate_expiry_dates(self):
		"""Ensure no expired batches are being dispatched"""
		for item in self.items:
			if item.batch_no:
				expiry_date = frappe.db.get_value("Batch", item.batch_no, "expiry_date")
				
				if expiry_date and getdate(expiry_date) <= getdate(today()):
					frappe.throw(_(
						"لا يمكن صرف الدفعة {0} للصنف {1} - منتهية الصلاحية"
					).format(item.batch_no, item.item_code))
	
	def create_stock_entry(self):
		"""Create Stock Entry for material issue"""
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Material Issue"
		stock_entry.company = frappe.defaults.get_user_default("Company")
		stock_entry.posting_date = self.posting_date
		stock_entry.posting_time = self.posting_time
		
		for item in self.items:
			stock_entry.append("items", {
				"item_code": item.item_code,
				"qty": item.qty,
				"s_warehouse": self.warehouse,
				"batch_no": item.batch_no,
				"basic_rate": item.rate
			})
		
		stock_entry.insert(ignore_permissions=True)
		stock_entry.submit()
		
		self.db_set('stock_entry', stock_entry.name)
		
		frappe.msgprint(_("تم إنشاء حركة مخزنية: {0}").format(
			frappe.get_desk_link("Stock Entry", stock_entry.name)
		))
	
	def create_delivery_note(self):
		"""Create Delivery Note for customer delivery"""
		if not self.sales_order:
			return
			
		delivery_note = frappe.new_doc("Delivery Note")
		delivery_note.customer = self.customer
		delivery_note.company = frappe.defaults.get_user_default("Company")
		delivery_note.posting_date = self.posting_date
		delivery_note.posting_time = self.posting_time
		delivery_note.set_warehouse = self.warehouse
		
		for item in self.items:
			delivery_note.append("items", {
				"item_code": item.item_code,
				"qty": item.qty,
				"rate": item.rate,
				"warehouse": self.warehouse,
				"batch_no": item.batch_no,
				"against_sales_order": self.sales_order
			})
		
		delivery_note.insert(ignore_permissions=True)
		delivery_note.submit()
		
		self.db_set('delivery_note', delivery_note.name)
		
		frappe.msgprint(_("تم إنشاء إذن تسليم: {0}").format(
			frappe.get_desk_link("Delivery Note", delivery_note.name)
		))
	
	def update_tele_sales_order(self):
		"""Update Tele Sales Order status"""
		frappe.db.set_value("Tele Sales Order", self.tele_sales_order, "status", "Dispatched")
	
	def cancel_linked_documents(self):
		"""Cancel Stock Entry and Delivery Note"""
		if self.stock_entry:
			try:
				stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
				if stock_entry.docstatus == 1:
					stock_entry.cancel()
			except Exception as e:
				frappe.log_error(f"Error cancelling Stock Entry: {str(e)}")
		
		if self.delivery_note:
			try:
				delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)
				if delivery_note.docstatus == 1:
					delivery_note.cancel()
			except Exception as e:
				frappe.log_error(f"Error cancelling Delivery Note: {str(e)}")
	
	def set_status(self):
		"""Set document status based on workflow"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if self.delivery_note:
				self.status = "Dispatched"
			else:
				self.status = "Pending"
		elif self.docstatus == 2:
			self.status = "Cancelled"


@frappe.whitelist()
def get_pending_tele_sales_orders(warehouse=None):
	"""Get approved Tele Sales Orders pending dispatch"""
	filters = {
		"docstatus": 1,
		"status": "Approved"
	}
	
	orders = frappe.get_all(
		"Tele Sales Order",
		filters=filters,
		fields=["name", "customer", "customer_name", "posting_date", "net_amount"],
		order_by="posting_date desc"
	)
	
	return orders


@frappe.whitelist()
def make_warehouse_dispatch(source_name, target_doc=None):
	"""Create Warehouse Dispatch from Tele Sales Order"""
	from frappe.model.mapper import get_mapped_doc
	
	def set_missing_values(source, target):
		target.warehouse = frappe.db.get_single_value("Pharma General Settings", "default_warehouse")
		target.posting_date = today()
		target.posting_time = nowtime()
	
	def update_item(source, target, source_parent):
		target.qty = source.qty
		target.rate = source.net_amount / source.qty if source.qty else 0
	
	doclist = get_mapped_doc(
		"Tele Sales Order",
		source_name,
		{
			"Tele Sales Order": {
				"doctype": "Warehouse Dispatch",
				"field_map": {
					"name": "tele_sales_order",
					"customer": "customer"
				}
			},
			"Tele Sales Order Item": {
				"doctype": "Warehouse Dispatch Item",
				"field_map": {
					"item_code": "item_code",
					"qty": "qty"
				},
				"postprocess": update_item
			}
		},
		target_doc,
		set_missing_values
	)
	
	return doclist
