# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PharmaCustomer(Document):
	def validate(self):
		self.auto_categorize_customer()
	
	def before_save(self):
		self.sync_with_erpnext_customer()
	
	def sync_with_erpnext_customer(self):
		"""
		Synchronize Pharma Customer with standard ERPNext Customer.
		Creates a new Customer if erpnext_customer is not set, otherwise updates existing one.
		"""
		if not self.erpnext_customer:
			# Create new ERPNext Customer
			customer = frappe.new_doc("Customer")
			customer.customer_name = self.legal_name
			customer.customer_type = "Company"
			customer.customer_group = "Commercial"  # Default group
			customer.territory = "Egypt"  # Default territory
			
			# Set additional fields
			if self.email:
				customer.email_id = self.email
			if self.phone:
				customer.mobile_no = self.phone
			if self.tax_card:
				customer.tax_id = self.tax_card
			
			try:
				customer.insert(ignore_permissions=True)
				self.erpnext_customer = customer.name
				frappe.msgprint(f"تم إنشاء عميل ERPNext: {customer.name}", alert=True)
			except Exception as e:
				frappe.log_error(f"Failed to create ERPNext Customer: {str(e)}")
				frappe.throw(f"فشل إنشاء عميل ERPNext: {str(e)}")
		else:
			# Update existing ERPNext Customer
			try:
				customer = frappe.get_doc("Customer", self.erpnext_customer)
				customer.customer_name = self.legal_name
				
				if self.email:
					customer.email_id = self.email
				if self.phone:
					customer.mobile_no = self.phone
				if self.tax_card:
					customer.tax_id = self.tax_card
				
				customer.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Failed to update ERPNext Customer: {str(e)}")
				# Don't throw on update failure, just log
	
	def auto_categorize_customer(self):
		"""Automatically categorize customer based on financial volume"""
		if self.financial_volume_to:
			if self.financial_volume_to >= 1000000:  # 1 million
				suggested_category = "عميل فئة A"
			elif self.financial_volume_to >= 500000:  # 500k
				suggested_category = "عميل فئة B"
			else:
				suggested_category = "عميل فئة C"
			
			# Only auto-set if not manually set
			if not self.customer_category:
				self.customer_category = suggested_category
			elif self.customer_category != suggested_category:
				frappe.msgprint(
					f"تنبيه: الفئة المقترحة بناءً على حجم التعامل هي: {suggested_category}",
					indicator="blue",
					alert=True
				)
