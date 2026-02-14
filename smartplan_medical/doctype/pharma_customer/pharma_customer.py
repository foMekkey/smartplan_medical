# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PharmaCustomer(Document):
	def validate(self):
		self.auto_categorize_customer()
	
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
