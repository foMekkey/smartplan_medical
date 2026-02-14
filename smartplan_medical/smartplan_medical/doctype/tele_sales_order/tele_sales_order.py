# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class TeleSalesOrder(Document):
	def validate(self):
		"""Validation logic"""
		self.calculate_totals()
		self.check_discount_limits()
		self.set_status()
	
	def before_submit(self):
		"""Before submit validations"""
		# STRICT CHECK: If requires_approval is checked, MUST have approval
		if self.requires_approval == 1:
			if not self.approved_by:
				frappe.throw(
					_("⛔ هذا الطلب يتطلب موافقة قبل الإرسال. يرجى الموافقة عليه أولاً من قبل المدير."),
					title=_("موافقة مطلوبة")
				)
			
			if self.status != "Approved":
				frappe.throw(
					_("⛔ لا يمكن إرسال الطلب إلا بعد الموافقة عليه. الحالة الحالية: {0}").format(_(self.status)),
					title=_("موافقة مطلوبة")
				)
		
		# Additional safety check: if somehow not marked as requires_approval but still has no approval
		# and discount is high, throw error
		settings = frappe.get_single("Pharma General Settings")
		max_discount = flt(settings.max_discount_allowed or 50)
		
		if flt(self.total_discount_percent) > max_discount and not self.approved_by:
			frappe.throw(
				_("⛔ الخصم الإجمالي ({0:.2f}%) يتجاوز الحد المسموح ({1}%). يجب الموافقة على الطلب قبل الإرسال.").format(
					self.total_discount_percent, max_discount
				),
				title=_("موافقة مطلوبة")
			)
	
	def on_submit(self):
		"""Create backend Sales Order"""
		self.create_sales_order()
	
	def on_cancel(self):
		"""Cancel related documents"""
		self.status = "Cancelled"
		if self.sales_order_reference:
			so = frappe.get_doc("Sales Order", self.sales_order_reference)
			if so.docstatus == 1:
				so.cancel()
	
	def calculate_totals(self):
		"""Calculate order totals"""
		self.total_amount = 0
		total_discount = 0
		
		for item in self.items:
			# Calculate item amount
			item.amount = flt(item.qty) * flt(item.rate)
			
			# Calculate item discount
			item_disc = flt(item.amount) * flt(item.item_discount_percent) / 100
			item.discount_amount = item_disc
			item.net_amount = item.amount - item_disc
			
			self.total_amount += item.amount
			total_discount += item_disc
		
		# Add additional discount
		additional_disc = flt(self.total_amount) * flt(self.additional_discount_percent) / 100
		total_discount += additional_disc
		
		self.discount_amount = total_discount
		self.net_amount = self.total_amount - total_discount
		
		# Calculate total discount percent
		if self.total_amount:
			self.total_discount_percent = (total_discount / self.total_amount) * 100
	
	def check_discount_limits(self):
		"""Check discount against user role limits"""
		settings = frappe.get_single("Pharma General Settings")
		max_discount = flt(settings.max_discount_allowed or 50)
		
		# Check if total discount exceeds limit
		if flt(self.total_discount_percent) > max_discount:
			self.requires_approval = 1
			self.approval_reason = f"إجمالي الخصم ({self.total_discount_percent:.2f}%) يتجاوز الحد المسموح ({max_discount}%)"
			
			# Check if user has approval rights
			if not frappe.has_permission("Tele Sales Order", "approve", raise_exception=False):
				frappe.msgprint(
					_("هذا الطلب يتطلب موافقة من المدير لأن الخصم يتجاوز الحد المسموح"),
					indicator="orange",
					alert=True
				)
	
	def set_status(self):
		"""Set order status"""
		if self.docstatus == 0:
			if self.requires_approval and not self.approved_by:
				self.status = "Pending Approval"
			else:
				self.status = "Draft"
		elif self.docstatus == 1:
			if not self.sales_order_reference:
				self.status = "Approved"
			else:
				self.status = "Dispatched"
		elif self.docstatus == 2:
			self.status = "Cancelled"
	
	def create_sales_order(self):
		"""Create ERPNext Sales Order in background"""
		if self.sales_order_reference:
			return
		
		# Create Sales Order
		so = frappe.get_doc({
			"doctype": "Sales Order",
			"customer": self.customer,
			"transaction_date": self.order_date,
			"delivery_date": self.order_date,
			"custom_tele_sales_order": self.name,
			"custom_tele_sales_employee": self.tele_sales_employee,
			"items": []
		})
		
		# Add items
		for item in self.items:
			so.append("items", {
				"item_code": item.item_code,
				"qty": item.qty,
				"rate": item.rate,
				"discount_percentage": item.item_discount_percent
			})
		
		# Save and submit
		so.flags.ignore_permissions = True
		so.insert()
		so.submit()
		
		# Update reference
		self.db_set("sales_order_reference", so.name)
		
		frappe.msgprint(
			_("تم إنشاء أمر البيع: {0}").format(so.name),
			indicator="green",
			alert=True
		)
	
	@frappe.whitelist()
	def approve_order(self):
		"""Approve order by Sales Manager"""
		if not frappe.has_permission(self.doctype, "approve"):
			frappe.throw(_("غير مصرح لك بالموافقة على الطلبات"))
		
		if self.docstatus != 0:
			frappe.throw(_("يمكن الموافقة على الطلبات في حالة المسودة فقط"))
		
		if self.approved_by:
			frappe.throw(_("تمت الموافقة على هذا الطلب مسبقاً"))
		
		self.approved_by = frappe.session.user
		self.approval_date = frappe.utils.now()
		self.status = "Approved"
		self.save()
		
		frappe.msgprint(
			_("✅ تمت الموافقة على الطلب. يمكنك الآن عمل Submit"),
			indicator="green",
			alert=True
		)
		
		return True


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
