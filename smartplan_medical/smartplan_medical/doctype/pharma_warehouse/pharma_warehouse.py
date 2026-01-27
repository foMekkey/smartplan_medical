# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff

class PharmaWarehouse(Document):
	def validate(self):
		self.check_expiry_date()
		self.check_stock_levels()
	
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
