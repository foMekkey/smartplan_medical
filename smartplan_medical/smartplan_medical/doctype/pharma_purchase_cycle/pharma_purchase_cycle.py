# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

class PharmaPurchaseCycle(Document):
	def validate(self):
		self.validate_items()
		self.calculate_totals()

	def validate_items(self):
		if not self.items:
			frappe.throw(_("يجب إضافة صنف واحد على الأقل"))
		
		if not self.target_warehouse:
			frappe.throw(_("يجب تحديد المخزن المستهدف"))
	
	def calculate_totals(self):
		"""Calculate amount for each item and total"""
		self.total_qty = 0
		self.total_amount = 0
		
		for item in self.items:
			item.amount = flt(item.qty) * flt(item.rate)
			self.total_qty += flt(item.qty)
			self.total_amount += flt(item.amount)

	@frappe.whitelist()
	def create_purchase_order(self):
		"""Creates a standard ERPNext Purchase Order"""
		if self.purchase_order:
			frappe.throw(_("تم إنشاء أمر شراء بالفعل لهذا المستند"))
		
		if self.status != "Draft":
			frappe.throw(_("يمكن إنشاء أمر شراء فقط في حالة المسودة"))
		
		if not self.target_warehouse:
			frappe.throw(_("يجب تحديد المخزن المستهدف قبل إنشاء أمر الشراء"))

		pharma_supplier = frappe.get_doc("Pharma Supplier", self.pharma_supplier)
		if not pharma_supplier.erpnext_supplier:
			frappe.throw(_("هذا المورد غير مربوط بمورد في ERPNext"))

		po = frappe.new_doc("Purchase Order")
		po.supplier = pharma_supplier.erpnext_supplier
		po.transaction_date = self.transaction_date
		po.schedule_date = self.transaction_date
		po.company = frappe.defaults.get_user_default("Company")
		
		for item in self.items:
			pharma_item = frappe.get_doc("Pharma Item", item.pharma_item)
			if not pharma_item.item_code:
				frappe.throw(_("الصنف {0} غير مربوط بصنف ERPNext. يرجى حفظ الصنف أولاً لإنشاء الربط التلقائي.").format(pharma_item.item_name))
			
			po.append("items", {
				"item_code": pharma_item.item_code,
				"qty": item.qty,
				"rate": item.rate,
				"warehouse": self.target_warehouse,
				"schedule_date": self.transaction_date
			})
		
		po.flags.ignore_permissions = True
		po.insert()
		po.submit() # Auto-submit as per requirements implied by "Updates Status -> Ordered"

		self.purchase_order = po.name
		self.status = "Ordered"
		self.save()
		
		frappe.msgprint(_("تم إنشاء أمر الشراء: {0}").format(po.name), alert=True)
		return po.name

	@frappe.whitelist()
	def create_purchase_receipt(self):
		"""Creates a standard ERPNext Purchase Receipt linked to the PO"""
		if not self.purchase_order:
			frappe.throw(_("يجب إنشاء أمر شراء أولاً"))
		
		if self.purchase_receipt:
			frappe.throw(_("تم إنشاء استلام مخزني بالفعل لهذا المستند"))

		# Make PR from PO
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
		pr = make_purchase_receipt(self.purchase_order)
		
		# Set warehouse for all items
		for item in pr.items:
			item.warehouse = self.target_warehouse
		
		pr.flags.ignore_permissions = True
		pr.insert()
		pr.submit()

		self.purchase_receipt = pr.name
		self.status = "Received"
		self.save()

		frappe.msgprint(_("تم إنشاء استلام مخزني: {0}").format(pr.name), alert=True)
		return pr.name

	@frappe.whitelist()
	def create_purchase_invoice(self):
		"""Creates a standard ERPNext Purchase Invoice linked to the PR"""
		if not self.purchase_receipt:
			frappe.throw(_("يجب إنشاء استلام مخزني أولاً"))
		
		if self.purchase_invoice:
			frappe.throw(_("تم إنشاء فاتورة بالفعل لهذا المستند"))

		# Make PI from PR
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
		pi = make_purchase_invoice(self.purchase_receipt)
		
		# Set posting date to match transaction date
		pi.posting_date = self.transaction_date
		pi.bill_date = self.transaction_date
		
		# Note: update_stock should be 0 because PR already updated stock
		# PI from PR is only for billing purposes
		pi.update_stock = 0
		
		pi.flags.ignore_permissions = True
		pi.insert()
		pi.submit()

		self.purchase_invoice = pi.name
		self.status = "Billed"
		self.save()

		frappe.msgprint(_("تم إنشاء فاتورة المشتريات: {0}").format(pi.name), alert=True)
		return pi.name
