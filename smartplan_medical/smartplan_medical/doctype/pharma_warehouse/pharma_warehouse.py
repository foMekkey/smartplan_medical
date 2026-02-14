# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff

class PharmaWarehouse(Document):
	def validate(self):
		self.check_expiry_date()
		self.check_stock_levels()
	
	def before_save(self):
		self.sync_with_erpnext_warehouse()
	
	def sync_with_erpnext_warehouse(self):
		"""
		Synchronize Pharma Warehouse with standard ERPNext Warehouse.
		Creates a new Warehouse if erpnext_warehouse is not set, otherwise updates existing one.
		"""
		if not self.erpnext_warehouse:
			# Create new ERPNext Warehouse
			warehouse = frappe.new_doc("Warehouse")
			warehouse.warehouse_name = self.warehouse_name
			warehouse.company = frappe.defaults.get_user_default("Company") or frappe.get_all("Company", limit=1)[0].name
			warehouse.is_group = 0
			
			# Set warehouse type only if Transit type is selected
			# Don't set warehouse_type if not needed (many ERPNext installations don't use it)
			if self.warehouse_type and self.warehouse_type == "توزيع":
				warehouse.warehouse_type = "Transit"
			
			try:
				warehouse.insert(ignore_permissions=True)
				self.erpnext_warehouse = warehouse.name
				frappe.msgprint(f"تم إنشاء مخزن ERPNext: {warehouse.name}", alert=True)
			except Exception as e:
				frappe.log_error(f"Failed to create ERPNext Warehouse: {str(e)}")
				frappe.throw(f"فشل إنشاء مخزن ERPNext: {str(e)}")
		else:
			# Update existing ERPNext Warehouse
			try:
				warehouse = frappe.get_doc("Warehouse", self.erpnext_warehouse)
				warehouse.warehouse_name = self.warehouse_name
				
				# Set warehouse type only if Transit type is selected
				if self.warehouse_type and self.warehouse_type == "توزيع":
					warehouse.warehouse_type = "Transit"
				
				warehouse.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Failed to update ERPNext Warehouse: {str(e)}")
				# Don't throw on update failure, just log
	
	def check_expiry_date(self):
		"""Check if items are approaching expiry"""
		if self.expiry_date and self.expiry_alert_days:
			days_to_expiry = date_diff(self.expiry_date, getdate())
			if days_to_expiry <= self.expiry_alert_days and days_to_expiry >= 0:
				frappe.msgprint(
					f"تنبيه: المخزن {self.warehouse_name} يحتوي على أصناف تقترب من تاريخ الصلاحية ({days_to_expiry} يوم متبقي)",
					indicator="orange",
					alert=True
				)
	
	def check_stock_levels(self):
		"""Check if stock is below threshold"""
		# This would be implemented with actual stock levels in production
		pass
