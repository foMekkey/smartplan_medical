# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PharmaGeneralSettings(Document):
	def validate(self):
		self.validate_discount_limits()
	
	def validate_discount_limits(self):
		"""Validate discount limits"""
		if self.max_discount_allowed and self.max_discount_allowed > 100:
			frappe.throw("أقصى خصم مسموح لا يمكن أن يتجاوز 100%")
		
		if self.default_item_discount and self.default_item_discount > self.max_discount_allowed:
			frappe.throw("الخصم الافتراضي على الصنف يجب ألا يتجاوز أقصى خصم مسموح")
		
		if self.default_invoice_discount and self.default_invoice_discount > self.max_discount_allowed:
			frappe.throw("الخصم الافتراضي على الفاتورة يجب ألا يتجاوز أقصى خصم مسموح")
