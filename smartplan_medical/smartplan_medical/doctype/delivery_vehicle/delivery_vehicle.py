# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff

class DeliveryVehicle(Document):
	def validate(self):
		self.check_document_expiry()
	
	def check_document_expiry(self):
		"""Check if vehicle documents are expiring soon"""
		alert_days = 30
		
		if self.license_expiry:
			days_to_expiry = date_diff(self.license_expiry, getdate())
			if days_to_expiry <= alert_days and days_to_expiry >= 0:
				frappe.msgprint(
					f"تنبيه: رخصة السيارة {self.vehicle_number} تنتهي خلال {days_to_expiry} يوم",
					indicator="orange",
					alert=True
				)
		
		if self.insurance_expiry:
			days_to_expiry = date_diff(self.insurance_expiry, getdate())
			if days_to_expiry <= alert_days and days_to_expiry >= 0:
				frappe.msgprint(
					f"تنبيه: تأمين السيارة {self.vehicle_number} ينتهي خلال {days_to_expiry} يوم",
					indicator="orange",
					alert=True
				)
