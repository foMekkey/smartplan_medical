# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class Cashbox(Document):
    def validate(self):
        self.validate_account()
        self.validate_limits()
    
    def validate_account(self):
        """التحقق من الحساب المحاسبي"""
        if self.erp_account:
            account = frappe.get_doc("Account", self.erp_account)
            if account.account_type != "Cash":
                frappe.msgprint(_("تنبيه: الحساب المحدد ليس من نوع نقدية"))
    
    def validate_limits(self):
        """التحقق من صحة الحدود"""
        if flt(self.min_balance) > flt(self.max_balance):
            frappe.throw(_("الحد الأدنى لا يمكن أن يكون أكبر من الحد الأقصى"))
    
    def update_balance(self, amount, transaction_type="receipt"):
        """تحديث رصيد الخزينة"""
        if transaction_type == "receipt":
            new_balance = flt(self.current_balance) + flt(amount)
        else:
            new_balance = flt(self.current_balance) - flt(amount)
        
        # التحقق من الحدود
        if new_balance < flt(self.min_balance):
            frappe.throw(_("الرصيد الناتج ({0}) أقل من الحد الأدنى المسموح ({1})").format(
                new_balance, self.min_balance))
        
        if new_balance > flt(self.max_balance):
            frappe.throw(_("الرصيد الناتج ({0}) أكبر من الحد الأقصى المسموح ({1})").format(
                new_balance, self.max_balance))
        
        self.db_set("current_balance", new_balance)
        self.db_set("last_transaction_date", frappe.utils.now())
        
        return new_balance


@frappe.whitelist()
def get_cashbox_balance(cashbox):
    """جلب رصيد الخزينة الحالي"""
    return frappe.db.get_value("Cashbox", cashbox, "current_balance") or 0


@frappe.whitelist()
def get_active_cashboxes():
    """جلب الخزائن النشطة"""
    return frappe.get_all("Cashbox", 
        filters={"is_active": 1},
        fields=["name", "cashbox_name", "cashbox_type", "current_balance", "custodian_name"])
