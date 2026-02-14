# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TeleSalesTeam(Document):
	def validate(self):
		self.validate_dates()
	
	def validate_dates(self):
		"""Validate target dates"""
		if self.target_from_date and self.target_to_date:
			if self.target_from_date > self.target_to_date:
				frappe.throw("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
