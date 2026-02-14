# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, now


class CashTransaction(Document):
    def validate(self):
        self.validate_amount()
        self.validate_cashbox()
        self.set_party_name()
        self.set_balance_before()
    
    def validate_amount(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("المبلغ يجب أن يكون أكبر من صفر"))
    
    def validate_cashbox(self):
        """التحقق من الخزينة"""
        cashbox = frappe.get_doc("Cashbox", self.cashbox)
        
        if not cashbox.is_active:
            frappe.throw(_("الخزينة {0} غير نشطة").format(self.cashbox))
        
        # التحقق من حد الصرف اليومي
        if self.transaction_type == "صرف":
            daily_spent = self.get_daily_spent()
            if flt(daily_spent) + flt(self.amount) > flt(cashbox.daily_limit):
                frappe.throw(_("تجاوز الحد اليومي للصرف. المتاح: {0}").format(
                    flt(cashbox.daily_limit) - flt(daily_spent)))
            
            # التحقق من موافقة المبالغ الكبيرة
            if flt(self.amount) > flt(cashbox.requires_approval_above):
                frappe.msgprint(_("هذا المبلغ يتطلب موافقة إدارية"), alert=True)
    
    def get_daily_spent(self):
        """حساب إجمالي الصرف اليومي"""
        return frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0)
            FROM `tabCash Transaction`
            WHERE cashbox = %s
                AND transaction_type = 'صرف'
                AND posting_date = %s
                AND docstatus = 1
                AND name != %s
        """, (self.cashbox, self.posting_date, self.name or ""))[0][0] or 0
    
    def set_party_name(self):
        """تحديد اسم الطرف"""
        if self.party_type and self.party:
            if self.party_type == "عميل":
                self.party_name = frappe.db.get_value("Pharma Customer", self.party, "legal_name")
            elif self.party_type == "مورد":
                self.party_name = frappe.db.get_value("Supplier", self.party, "supplier_name")
            elif self.party_type == "موظف":
                self.party_name = frappe.db.get_value("Employee", self.party, "employee_name")
    
    def set_balance_before(self):
        """تسجيل الرصيد قبل الحركة"""
        self.balance_before = frappe.db.get_value("Cashbox", self.cashbox, "current_balance") or 0
    
    def on_submit(self):
        """عند الاعتماد: تحديث الرصيد وإنشاء القيد"""
        self.update_cashbox_balance()
        self.create_journal_entry()
        self.status = "Submitted"
    
    def on_cancel(self):
        """عند الإلغاء: عكس الرصيد وإلغاء القيد"""
        self.reverse_cashbox_balance()
        self.cancel_journal_entry()
        self.status = "Cancelled"
    
    def update_cashbox_balance(self):
        """تحديث رصيد الخزينة"""
        cashbox = frappe.get_doc("Cashbox", self.cashbox)
        
        if self.transaction_type == "قبض":
            new_balance = cashbox.update_balance(self.amount, "receipt")
        else:
            new_balance = cashbox.update_balance(self.amount, "payment")
        
        self.db_set("balance_after", new_balance)
    
    def reverse_cashbox_balance(self):
        """عكس تحديث رصيد الخزينة"""
        cashbox = frappe.get_doc("Cashbox", self.cashbox)
        
        if self.transaction_type == "قبض":
            cashbox.update_balance(self.amount, "payment")  # عكس القبض = صرف
        else:
            cashbox.update_balance(self.amount, "receipt")  # عكس الصرف = قبض
    
    def create_journal_entry(self):
        """إنشاء قيد محاسبي"""
        cashbox = frappe.get_doc("Cashbox", self.cashbox)
        
        if not self.against_account:
            frappe.throw(_("يجب تحديد الحساب المقابل"))
        
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Cash Entry",
            "posting_date": self.posting_date,
            "company": cashbox.company,
            "user_remark": f"{self.transaction_type}: {self.description}",
            "accounts": []
        })
        
        if self.transaction_type == "قبض":
            # مدين: الخزينة، دائن: الحساب المقابل
            je.append("accounts", {
                "account": cashbox.erp_account,
                "debit_in_account_currency": flt(self.amount),
                "credit_in_account_currency": 0
            })
            je.append("accounts", {
                "account": self.against_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": flt(self.amount)
            })
        else:
            # مدين: الحساب المقابل، دائن: الخزينة
            je.append("accounts", {
                "account": self.against_account,
                "debit_in_account_currency": flt(self.amount),
                "credit_in_account_currency": 0
            })
            je.append("accounts", {
                "account": cashbox.erp_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": flt(self.amount)
            })
        
        je.insert(ignore_permissions=True)
        je.submit()
        
        self.db_set("journal_entry", je.name)
        frappe.msgprint(_("تم إنشاء القيد المحاسبي: {0}").format(je.name))
    
    def cancel_journal_entry(self):
        """إلغاء القيد المحاسبي"""
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()
                frappe.msgprint(_("تم إلغاء القيد المحاسبي: {0}").format(self.journal_entry))


@frappe.whitelist()
def get_cashbox_info(cashbox):
    """جلب معلومات الخزينة"""
    return frappe.db.get_value("Cashbox", cashbox, 
        ["cashbox_name", "current_balance", "daily_limit", "requires_approval_above", "erp_account"],
        as_dict=True)
