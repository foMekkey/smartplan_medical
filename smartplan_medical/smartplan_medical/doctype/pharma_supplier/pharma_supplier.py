# Copyright (c) 2025, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PharmaSupplier(Document):
	def before_save(self):
		self.sync_with_erpnext_supplier()

	def sync_with_erpnext_supplier(self):
		"""
		Synchronize Pharma Supplier with standard ERPNext Supplier.
		Creates a new Supplier if erpnext_supplier is not set, otherwise updates existing one.
		"""
		if not self.erpnext_supplier:
			# Create new ERPNext Supplier
			supplier = frappe.new_doc("Supplier")
			supplier.supplier_name = self.legal_name
			supplier.supplier_type = self.supplier_type or "Company"
			
			# Set additional fields
			if self.email:
				supplier.email_id = self.email
			if self.phone:
				supplier.mobile_no = self.phone
			if self.country:
				supplier.country = self.country
			
			try:
				supplier.insert(ignore_permissions=True)
				self.erpnext_supplier = supplier.name
				frappe.msgprint(f"تم إنشاء مورد ERPNext: {supplier.name}")
			except Exception as e:
				frappe.log_error(f"Failed to create ERPNext Supplier: {str(e)}")
				frappe.throw(f"فشل إنشاء مورد ERPNext: {str(e)}")
		else:
			# Update existing ERPNext Supplier
			try:
				supplier = frappe.get_doc("Supplier", self.erpnext_supplier)
				supplier.supplier_name = self.legal_name
				supplier.supplier_type = self.supplier_type or "Company"
				
				if self.email:
					supplier.email_id = self.email
				if self.phone:
					supplier.mobile_no = self.phone
				if self.country:
					supplier.country = self.country
				
				supplier.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Failed to update ERPNext Supplier: {str(e)}")
				frappe.throw(f"فشل تحديث مورد ERPNext: {str(e)}")
