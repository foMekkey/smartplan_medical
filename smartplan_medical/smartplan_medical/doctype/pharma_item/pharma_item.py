# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PharmaItem(Document):
	def validate(self):
		self.calculate_company_cost()
		self.log_price_changes()
	
	def before_save(self):
		self.sync_with_erpnext_item()
	
	def sync_with_erpnext_item(self):
		"""
		Synchronize Pharma Item with standard ERPNext Item.
		Creates a new Item if item_code is not set, otherwise updates existing one.
		"""
		if not self.item_code:
			# Create new ERPNext Item
			item = frappe.new_doc("Item")
			item.item_code = self.item_name  # Use item_name as item_code
			item.item_name = self.item_name
			item.item_group = "Products"  # Default group
			item.stock_uom = self.unit_of_measure or "Unit"
			item.is_stock_item = 1
			item.include_item_in_manufacturing = 0
			
			# Set pricing
			if self.public_price:
				item.standard_rate = self.public_price
			
			# Set manufacturer
			if self.manufacturer:
				item.brand = self.manufacturer
			
			try:
				item.insert(ignore_permissions=True)
				self.item_code = item.name
				frappe.msgprint(f"تم إنشاء صنف ERPNext: {item.name}", alert=True)
			except Exception as e:
				frappe.log_error(f"Failed to create ERPNext Item: {str(e)}")
				frappe.throw(f"فشل إنشاء صنف ERPNext: {str(e)}")
		else:
			# Update existing ERPNext Item
			try:
				item = frappe.get_doc("Item", self.item_code)
				item.item_name = self.item_name
				
				if self.public_price:
					item.standard_rate = self.public_price
				if self.manufacturer:
					item.brand = self.manufacturer
				if self.unit_of_measure:
					item.stock_uom = self.unit_of_measure
				
				item.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Failed to update ERPNext Item: {str(e)}")
				# Don't throw on update failure, just log
	
	def calculate_company_cost(self):
		"""Calculate the actual company cost after purchase discount"""
		if self.purchase_price and self.purchase_discount_percent:
			discount_amount = self.purchase_price * (self.purchase_discount_percent / 100)
			self.company_cost = self.purchase_price - discount_amount
		else:
			self.company_cost = self.purchase_price or 0
	
	def log_price_changes(self):
		"""Log price changes to price history"""
		if self.is_new():
			return
		
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return
		
		# Check if prices or discounts changed
		price_changed = (
			old_doc.purchase_price != self.purchase_price or
			old_doc.public_price != self.public_price or
			old_doc.purchase_discount_percent != self.purchase_discount_percent or
			old_doc.public_discount_percent != self.public_discount_percent or
			old_doc.item_discount_percent != self.item_discount_percent or
			old_doc.special_discount_percent != self.special_discount_percent or
			old_doc.expiry_discount_percent != self.expiry_discount_percent
		)
		
		if price_changed:
			self.append("price_history", {
				"date": frappe.utils.nowdate(),
				"purchase_price": self.purchase_price,
				"public_price": self.public_price,
				"purchase_discount": self.purchase_discount_percent,
				"public_discount": self.public_discount_percent,
				"item_discount": self.item_discount_percent,
				"special_discount": self.special_discount_percent,
				"expiry_discount": self.expiry_discount_percent,
				"user": frappe.session.user
			})
