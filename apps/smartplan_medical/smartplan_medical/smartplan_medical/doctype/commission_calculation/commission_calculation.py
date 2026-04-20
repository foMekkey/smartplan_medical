# Copyright (c) 2026, SmartPlan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now, flt, getdate, get_first_day, get_last_day, add_months


class CommissionCalculation(Document):
	def validate(self):
		"""Validate commission calculation"""
		self.validate_dates()
		self.validate_employee()
		self.set_status()
		
	def before_submit(self):
		"""Calculate commission before submission"""
		if not self.commission_details:
			self.calculate_commission()
		self.validate_calculation()
		
	def on_submit(self):
		"""Mark as pending approval"""
		self.status = "Pending Approval"
		self.calculated_by = frappe.session.user
		self.calculated_at = now()
		self.db_set({
			'status': 'Pending Approval',
			'calculated_by': frappe.session.user,
			'calculated_at': now()
		})
		
	def on_cancel(self):
		"""Cancel commission"""
		self.status = "Cancelled"
		self.db_set('status', 'Cancelled')
	
	def validate_dates(self):
		"""Validate date range"""
		if getdate(self.from_date) > getdate(self.to_date):
			frappe.throw(_("تاريخ البداية يجب أن يكون قبل تاريخ النهاية"))
		
		# Check for overlapping periods
		overlapping = frappe.db.sql("""
			SELECT name 
			FROM `tabCommission Calculation`
			WHERE 
				tele_sales_employee = %s
				AND docstatus = 1
				AND name != %s
				AND (
					(from_date BETWEEN %s AND %s)
					OR (to_date BETWEEN %s AND %s)
					OR (from_date <= %s AND to_date >= %s)
				)
		""", (
			self.tele_sales_employee, 
			self.name or '',
			self.from_date, self.to_date,
			self.from_date, self.to_date,
			self.from_date, self.to_date
		))
		
		if overlapping:
			frappe.throw(_(
				"يوجد حساب عمولة آخر ({0}) لنفس الموظف في فترة متداخلة"
			).format(overlapping[0][0]))
	
	def validate_employee(self):
		"""Validate tele sales employee exists"""
		if not frappe.db.exists("Tele Sales Team", self.tele_sales_employee):
			frappe.throw(_("موظف التلي سيلز غير موجود"))
	
	def validate_calculation(self):
		"""Ensure calculation is complete"""
		if not self.commission_details:
			frappe.throw(_("لا توجد بيانات للعمولة. قم بحساب العمولة أولاً"))
		
		if flt(self.total_commission) <= 0:
			frappe.msgprint(_("إجمالي العمولة صفر"), indicator='orange')
	
	def set_status(self):
		"""Set document status"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if self.approved_by:
				if self.payment_status == "Paid":
					self.status = "Paid"
				else:
					self.status = "Approved"
			else:
				self.status = "Pending Approval"
		elif self.docstatus == 2:
			self.status = "Cancelled"
	
	def calculate_commission(self):
		"""Calculate commission based on sales orders"""
		# Clear existing details
		self.commission_details = []
		
		# Get all approved orders for this employee in the period
		orders = frappe.db.sql("""
			SELECT 
				tso.name,
				tso.customer,
				tso.customer_name,
				tso.posting_date,
				tso.net_amount,
				tso.status
			FROM `tabTele Sales Order` tso
			WHERE 
				tso.tele_sales_employee = %s
				AND tso.docstatus = 1
				AND tso.posting_date BETWEEN %s AND %s
				AND tso.status IN ('Approved', 'Dispatched', 'Delivered')
			ORDER BY tso.posting_date
		""", (self.tele_sales_employee, self.from_date, self.to_date), as_dict=1)
		
		total_sales = 0
		
		for order in orders:
			# Add to commission details
			self.append("commission_details", {
				"order_no": order.name,
				"customer": order.customer,
				"customer_name": order.customer_name,
				"order_date": order.posting_date,
				"net_sales": order.net_amount,
				"order_status": order.status
			})
			
			total_sales += flt(order.net_amount)
		
		# Calculate commission
		self.total_net_sales = total_sales
		self.total_orders = len(orders)
		
		# Commission formula: commission_per_million for each 1,000,000 EGP
		millions = total_sales / 1000000
		self.total_commission = millions * flt(self.commission_rate)
		
		# Update each detail with proportional commission
		if self.total_orders > 0:
			for detail in self.commission_details:
				detail.commission_amount = (
					flt(detail.net_sales) / total_sales * self.total_commission
				) if total_sales > 0 else 0
	
	def approve_commission(self):
		"""Approve commission calculation"""
		if not frappe.has_permission(self.doctype, "approve"):
			frappe.throw(_("غير مصرح لك بالموافقة على العمولات"))
		
		if self.docstatus != 1:
			frappe.throw(_("يجب اعتماد المستند أولاً"))
		
		if self.status == "Approved":
			frappe.throw(_("تمت الموافقة على هذه العمولة مسبقاً"))
		
		self.status = "Approved"
		self.approved_by = frappe.session.user
		self.approved_at = now()
		
		self.db_set({
			'status': 'Approved',
			'approved_by': frappe.session.user,
			'approved_at': now()
		})
		
		frappe.msgprint(_("تمت الموافقة على العمولة بنجاح"))
	
	def reject_commission(self, reason=None):
		"""Reject commission calculation"""
		if not frappe.has_permission(self.doctype, "approve"):
			frappe.throw(_("غير مصرح لك برفض العمولات"))
		
		if self.docstatus != 1:
			frappe.throw(_("يجب اعتماد المستند أولاً"))
		
		self.status = "Rejected"
		if reason:
			self.approval_notes = reason
		
		self.db_set({
			'status': 'Rejected',
			'approval_notes': reason or self.approval_notes
		})
		
		frappe.msgprint(_("تم رفض العمولة"))
	
	def mark_as_paid(self, payment_reference=None):
		"""Mark commission as paid"""
		if self.status != "Approved":
			frappe.throw(_("يجب الموافقة على العمولة أولاً"))
		
		self.payment_status = "Paid"
		self.payment_date = today()
		self.status = "Paid"
		
		if payment_reference:
			self.payment_reference = payment_reference
		
		self.db_set({
			'payment_status': 'Paid',
			'payment_date': today(),
			'status': 'Paid',
			'payment_reference': payment_reference or self.payment_reference
		})
		
		frappe.msgprint(_("تم تسجيل صرف العمولة"))


@frappe.whitelist()
def calculate_commission_for_employee(employee, from_date, to_date):
	"""Calculate commission for a specific employee and period"""
	# Create new commission calculation
	doc = frappe.new_doc("Commission Calculation")
	doc.tele_sales_employee = employee
	doc.from_date = from_date
	doc.to_date = to_date
	doc.calculation_period = "Custom"
	
	# Calculate
	doc.calculate_commission()
	
	return doc.as_dict()


@frappe.whitelist()
def auto_calculate_monthly_commissions():
	"""Auto-calculate commissions for all tele sales employees (scheduled job)"""
	# Get last month's date range
	last_month_end = add_months(get_first_day(today()), -1)
	last_month_end = get_last_day(last_month_end)
	last_month_start = get_first_day(last_month_end)
	
	# Get all active tele sales employees
	employees = frappe.get_all(
		"Tele Sales Team",
		filters={"status": "Active"},
		fields=["name", "employee_name"]
	)
	
	created_count = 0
	
	for emp in employees:
		# Check if commission already calculated for this period
		existing = frappe.db.exists({
			"doctype": "Commission Calculation",
			"tele_sales_employee": emp.name,
			"from_date": last_month_start,
			"to_date": last_month_end,
			"docstatus": ["!=", 2]
		})
		
		if not existing:
			try:
				doc = frappe.new_doc("Commission Calculation")
				doc.tele_sales_employee = emp.name
				doc.from_date = last_month_start
				doc.to_date = last_month_end
				doc.calculation_period = "Monthly"
				doc.calculate_commission()
				doc.insert()
				created_count += 1
			except Exception as e:
				frappe.log_error(
					f"Error calculating commission for {emp.name}: {str(e)}",
					"Commission Auto-Calculation"
				)
	
	return {
		"success": True,
		"message": _("تم حساب {0} عمولة").format(created_count),
		"created": created_count
	}


@frappe.whitelist()
def get_employee_commission_summary(employee, from_date=None, to_date=None):
	"""Get commission summary for an employee"""
	filters = {
		"tele_sales_employee": employee,
		"docstatus": 1
	}
	
	if from_date:
		filters["from_date"] = [">=", from_date]
	if to_date:
		filters["to_date"] = ["<=", to_date]
	
	commissions = frappe.get_all(
		"Commission Calculation",
		filters=filters,
		fields=[
			"name", "from_date", "to_date", 
			"total_net_sales", "total_orders", "total_commission",
			"status", "payment_status"
		],
		order_by="from_date desc"
	)
	
	total_commission = sum(flt(c.total_commission) for c in commissions if c.status == "Approved")
	paid_commission = sum(flt(c.total_commission) for c in commissions if c.payment_status == "Paid")
	pending_commission = total_commission - paid_commission
	
	return {
		"commissions": commissions,
		"summary": {
			"total_commission": total_commission,
			"paid_commission": paid_commission,
			"pending_commission": pending_commission,
			"total_records": len(commissions)
		}
	}
