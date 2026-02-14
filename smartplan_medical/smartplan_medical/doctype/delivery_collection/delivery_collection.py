# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now, flt, nowdate, nowtime


class DeliveryCollection(Document):
	def validate(self):
		"""Validate delivery and collection document"""
		self.validate_warehouse_dispatch()
		self.validate_items()
		self.calculate_totals()
		self.validate_collection_amounts()
		self.set_collection_status()
		self.set_status()
		
	def before_submit(self):
		"""Pre-submission validations"""
		self.validate_delivery_completion()
		self.validate_collection_variance()
		
	def on_submit(self):
		"""Create Payment Entry and Sales Invoice on submit"""
		self.status = "Delivered"
		self.delivered_at = now()
		self.collected_by = frappe.session.user
		self.collection_time = now()
		
		self.create_sales_invoice()
		self.create_payment_entry()
		self.update_warehouse_dispatch()
		
		self.db_set({
			'status': 'Delivered',
			'delivered_at': now(),
			'collected_by': frappe.session.user,
			'collection_time': now()
		})
		
	def on_cancel(self):
		"""Cancel linked documents"""
		self.status = "Cancelled"
		self.cancel_linked_documents()
		self.db_set('status', 'Cancelled')
	
	def validate_warehouse_dispatch(self):
		"""Ensure Warehouse Dispatch is valid"""
		if not self.warehouse_dispatch:
			frappe.throw(_("يجب تحديد إذن الصرف"))
			
		dispatch = frappe.get_doc("Warehouse Dispatch", self.warehouse_dispatch)
		
		if dispatch.docstatus != 1:
			frappe.throw(_("إذن الصرف غير معتمد"))
			
		# Auto-populate items from dispatch if empty
		if not self.items and dispatch.items:
			for item in dispatch.items:
				self.append("items", {
					"item_code": item.item_code,
					"qty": item.qty,
					"delivered_qty": item.qty,
					"rate": item.rate,
					"amount": item.amount
				})
	
	def validate_items(self):
		"""Validate items"""
		if not self.items:
			frappe.throw(_("يجب إضافة أصناف"))
			
		for item in self.items:
			if not item.item_code:
				frappe.throw(_("الصنف مطلوب في السطر {0}").format(item.idx))
				
			if flt(item.delivered_qty) < 0:
				frappe.throw(_("الكمية المسلمة لا يمكن أن تكون سالبة في السطر {0}").format(item.idx))
				
			if flt(item.delivered_qty) > flt(item.qty):
				frappe.throw(_("الكمية المسلمة لا يمكن أن تتجاوز الكمية المطلوبة في السطر {0}").format(item.idx))
	
	def calculate_totals(self):
		"""Calculate expected amount based on delivered quantities"""
		self.expected_amount = 0
		
		for item in self.items:
			item.amount = flt(item.delivered_qty) * flt(item.rate)
			self.expected_amount += item.amount
	
	def validate_collection_amounts(self):
		"""Validate payment amounts"""
		if self.payment_type == "Mixed":
			total_payment = (
				flt(self.cash_amount) + 
				flt(self.cheque_amount) + 
				flt(self.bank_transfer_amount) + 
				flt(self.credit_amount)
			)
			
			if abs(total_payment - flt(self.collected_amount)) > 0.01:
				frappe.throw(_("مجموع طرق الدفع ({0}) لا يساوي المبلغ المحصل ({1})").format(
					total_payment, self.collected_amount
				))
		
		# Validate cheque details if cheque payment
		if self.payment_type == "Cheque" or flt(self.cheque_amount) > 0:
			if not self.cheque_no:
				frappe.throw(_("يجب إدخال رقم الشيك"))
			if not self.cheque_date:
				frappe.throw(_("يجب إدخال تاريخ الشيك"))
			if not self.bank_name:
				frappe.throw(_("يجب إدخال اسم البنك"))
	
	def set_collection_status(self):
		"""Set collection status based on collected amount"""
		variance = flt(self.collected_amount) - flt(self.expected_amount)
		self.variance_amount = variance
		
		if flt(self.collected_amount) == 0:
			self.collection_status = "Not Collected"
		elif abs(variance) < 0.01:
			self.collection_status = "Fully Collected"
		elif variance < 0:
			self.collection_status = "Partially Collected"
		else:
			self.collection_status = "Over Collected"
	
	def set_status(self):
		"""Set document status"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if self.delivered_at:
				self.status = "Delivered"
			else:
				self.status = "In Transit"
		elif self.docstatus == 2:
			self.status = "Cancelled"
	
	def validate_delivery_completion(self):
		"""Ensure delivery is marked as completed"""
		total_delivered = sum(flt(item.delivered_qty) for item in self.items)
		
		if total_delivered == 0:
			frappe.throw(_("لم يتم تسليم أي أصناف"))
	
	def validate_collection_variance(self):
		"""Check for significant collection variances"""
		variance_percent = 0
		if flt(self.expected_amount) > 0:
			variance_percent = abs(flt(self.variance_amount)) / flt(self.expected_amount) * 100
		
		max_variance = frappe.db.get_single_value("Pharma General Settings", "max_collection_variance") or 5
		
		if variance_percent > max_variance:
			if not frappe.has_permission("Delivery Collection", "approve"):
				frappe.throw(_(
					"فرق التحصيل ({0}%) يتجاوز الحد المسموح ({1}%). يتطلب موافقة المدير"
				).format(round(variance_percent, 2), max_variance))
	
	def create_sales_invoice(self):
		"""Create Sales Invoice for delivered items"""
		if not self.delivery_note:
			return
			
		sales_invoice = frappe.new_doc("Sales Invoice")
		sales_invoice.customer = self.customer
		sales_invoice.company = frappe.defaults.get_user_default("Company")
		sales_invoice.posting_date = self.posting_date
		sales_invoice.posting_time = self.posting_time
		sales_invoice.update_stock = 0  # Stock already updated via Delivery Note
		
		for item in self.items:
			if flt(item.delivered_qty) > 0:
				sales_invoice.append("items", {
					"item_code": item.item_code,
					"qty": item.delivered_qty,
					"rate": item.rate,
					"delivery_note": self.delivery_note
				})
		
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit()
		
		self.db_set('sales_invoice', sales_invoice.name)
		
		frappe.msgprint(_("تم إنشاء فاتورة البيع: {0}").format(
			frappe.get_desk_link("Sales Invoice", sales_invoice.name)
		))
	
	def create_payment_entry(self):
		"""Create Payment Entry for collected amount"""
		if flt(self.collected_amount) <= 0:
			return
		
		# Create payment entry for cash/cheque/bank transfer
		if flt(self.collected_amount) - flt(self.credit_amount) > 0:
			payment_entry = frappe.new_doc("Payment Entry")
			payment_entry.payment_type = "Receive"
			payment_entry.party_type = "Customer"
			payment_entry.party = self.customer
			payment_entry.company = frappe.defaults.get_user_default("Company")
			payment_entry.posting_date = self.posting_date
			payment_entry.paid_amount = flt(self.collected_amount) - flt(self.credit_amount)
			payment_entry.received_amount = payment_entry.paid_amount
			
			# Set mode of payment
			if self.payment_type == "Cash":
				payment_entry.mode_of_payment = "Cash"
			elif self.payment_type == "Cheque":
				payment_entry.mode_of_payment = "Cheque"
				payment_entry.reference_no = self.cheque_no
				payment_entry.reference_date = self.cheque_date
			elif self.payment_type == "Bank Transfer":
				payment_entry.mode_of_payment = "Bank Transfer"
			
			# Link to Sales Invoice
			if self.sales_invoice:
				payment_entry.append("references", {
					"reference_doctype": "Sales Invoice",
					"reference_name": self.sales_invoice,
					"allocated_amount": payment_entry.paid_amount
				})
			
			payment_entry.insert(ignore_permissions=True)
			payment_entry.submit()
			
			self.db_set('payment_entry', payment_entry.name)
			
			frappe.msgprint(_("تم إنشاء قيد الدفع: {0}").format(
				frappe.get_desk_link("Payment Entry", payment_entry.name)
			))
	
	def update_warehouse_dispatch(self):
		"""Update Warehouse Dispatch status"""
		frappe.db.set_value("Warehouse Dispatch", self.warehouse_dispatch, "status", "Delivered")
	
	def cancel_linked_documents(self):
		"""Cancel Sales Invoice and Payment Entry"""
		if self.payment_entry:
			try:
				payment = frappe.get_doc("Payment Entry", self.payment_entry)
				if payment.docstatus == 1:
					payment.cancel()
			except Exception as e:
				frappe.log_error(f"Error cancelling Payment Entry: {str(e)}")
		
		if self.sales_invoice:
			try:
				invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
				if invoice.docstatus == 1:
					invoice.cancel()
			except Exception as e:
				frappe.log_error(f"Error cancelling Sales Invoice: {str(e)}")


@frappe.whitelist()
def get_pending_dispatches(representative=None):
	"""Get dispatched orders pending delivery"""
	filters = {
		"docstatus": 1,
		"status": "Dispatched"
	}
	
	if representative:
		filters["delivery_representative"] = representative
	
	dispatches = frappe.get_all(
		"Warehouse Dispatch",
		filters=filters,
		# Avoid requesting fetched/display-only fields directly (customer_name).
		fields=["name", "customer", "posting_date", "total_amount", "delivery_representative"],
		order_by="posting_date desc"
	)

	# Populate customer_name safely for the UI callers
	for d in dispatches:
		try:
			d["customer_name"] = frappe.db.get_value("Pharma Customer", d.get("customer"), "legal_name") or d.get("customer")
		except Exception:
			d["customer_name"] = d.get("customer")

	return dispatches


@frappe.whitelist()
def make_delivery_collection(source_name, target_doc=None):
	"""Create Delivery & Collection from Warehouse Dispatch"""
	from frappe.model.mapper import get_mapped_doc
	
	def set_missing_values(source, target):
		target.posting_date = today()
		target.posting_time = nowtime()
		target.status = "In Transit"
	
	def update_item(source, target, source_parent):
		target.delivered_qty = source.qty
	
	doclist = get_mapped_doc(
		"Warehouse Dispatch",
		source_name,
		{
			"Warehouse Dispatch": {
				"doctype": "Delivery Collection",
				"field_map": {
					"name": "warehouse_dispatch",
					"customer": "customer",
					"delivery_representative": "delivery_representative"
				}
			},
			"Warehouse Dispatch Item": {
				"doctype": "Delivery Collection Item",
				"field_map": {
					"item_code": "item_code",
					"qty": "qty",
					"rate": "rate"
				},
				"postprocess": update_item
			}
		},
		target_doc,
		set_missing_values
	)
	
	return doclist
