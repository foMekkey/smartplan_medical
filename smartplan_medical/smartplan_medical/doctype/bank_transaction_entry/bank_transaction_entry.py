# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, now


class BankTransactionEntry(Document):
    def validate(self):
        self.validate_amount()
        self.set_party_name()
        self.set_balance_before()
    
    def validate_amount(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("المبلغ يجب أن يكون أكبر من صفر"))
    
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
        """تسجيل رصيد البنك قبل العملية"""
        bank_account = frappe.db.get_value("Bank Account", self.bank_account, "account")
        if bank_account:
            company = frappe.db.get_value("Bank Account", self.bank_account, "company")
            balance = frappe.db.sql("""
                SELECT SUM(debit - credit)
                FROM `tabGL Entry`
                WHERE account = %s AND company = %s AND is_cancelled = 0
            """, (bank_account, company))[0][0] or 0
            self.balance_before = balance
    
    def on_submit(self):
        """عند الاعتماد"""
        self.create_journal_entry()
        self.handle_cashbox_link()
        self.set_balance_after()
        self.status = "Submitted"
    
    def on_cancel(self):
        """عند الإلغاء"""
        self.cancel_journal_entry()
        self.reverse_cashbox_link()
        self.status = "Cancelled"
    
    def create_journal_entry(self):
        """إنشاء قيد محاسبي"""
        bank_account_doc = frappe.get_doc("Bank Account", self.bank_account)
        erp_account = bank_account_doc.account
        company = bank_account_doc.company
        
        if not erp_account:
            frappe.throw(_("الحساب البنكي غير مرتبط بحساب محاسبي"))
        
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Bank Entry",
            "posting_date": self.posting_date,
            "company": company,
            "cheque_no": self.reference_no,
            "cheque_date": self.posting_date,
            "user_remark": f"{self.transaction_type}: {self.description}",
            "accounts": []
        })
        
        # تحديد الحساب المقابل
        against_account = self.get_against_account(company)
        
        if self.transaction_type in ["إيداع نقدي", "تحويل وارد", "فوائد"]:
            # زيادة رصيد البنك
            je.append("accounts", {
                "account": erp_account,
                "debit_in_account_currency": flt(self.amount),
                "credit_in_account_currency": 0
            })
            je.append("accounts", {
                "account": against_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": flt(self.amount)
            })
        else:
            # نقص رصيد البنك
            je.append("accounts", {
                "account": against_account,
                "debit_in_account_currency": flt(self.amount),
                "credit_in_account_currency": 0
            })
            je.append("accounts", {
                "account": erp_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": flt(self.amount)
            })
        
        je.insert(ignore_permissions=True)
        je.submit()
        
        self.db_set("journal_entry", je.name)
        frappe.msgprint(_("تم إنشاء القيد المحاسبي: {0}").format(je.name))
    
    def get_against_account(self, company):
        """تحديد الحساب المقابل"""
        if self.transaction_type == "إيداع نقدي" and self.from_cashbox:
            return frappe.db.get_value("Cashbox", self.from_cashbox, "erp_account")
        elif self.transaction_type == "سحب نقدي" and self.to_cashbox:
            return frappe.db.get_value("Cashbox", self.to_cashbox, "erp_account")
        elif self.transaction_type == "رسوم بنكية":
            return frappe.db.get_value("Account", 
                {"account_name": ["like", "%مصاريف بنكية%"], "company": company}, "name") or \
                frappe.db.get_value("Account", 
                {"account_type": "Expense Account", "company": company, "is_group": 0}, "name")
        elif self.transaction_type == "فوائد":
            return frappe.db.get_value("Account", 
                {"account_name": ["like", "%إيرادات فوائد%"], "company": company}, "name") or \
                frappe.db.get_value("Account", 
                {"account_type": "Income Account", "company": company, "is_group": 0}, "name")
        else:
            # حساب تحويلات عام
            return frappe.db.get_value("Account", 
                {"account_type": "Bank", "company": company, "is_group": 0, 
                 "name": ["!=", frappe.db.get_value("Bank Account", self.bank_account, "account")]}, "name")
    
    def handle_cashbox_link(self):
        """معالجة ربط الخزينة"""
        if self.transaction_type == "إيداع نقدي" and self.from_cashbox:
            # خصم من الخزينة
            cashbox = frappe.get_doc("Cashbox", self.from_cashbox)
            cashbox.update_balance(self.amount, "payment")
        elif self.transaction_type == "سحب نقدي" and self.to_cashbox:
            # إضافة للخزينة
            cashbox = frappe.get_doc("Cashbox", self.to_cashbox)
            cashbox.update_balance(self.amount, "receipt")
    
    def reverse_cashbox_link(self):
        """عكس ربط الخزينة"""
        if self.transaction_type == "إيداع نقدي" and self.from_cashbox:
            cashbox = frappe.get_doc("Cashbox", self.from_cashbox)
            cashbox.update_balance(self.amount, "receipt")
        elif self.transaction_type == "سحب نقدي" and self.to_cashbox:
            cashbox = frappe.get_doc("Cashbox", self.to_cashbox)
            cashbox.update_balance(self.amount, "payment")
    
    def set_balance_after(self):
        """تسجيل رصيد البنك بعد العملية"""
        bank_account = frappe.db.get_value("Bank Account", self.bank_account, "account")
        if bank_account:
            company = frappe.db.get_value("Bank Account", self.bank_account, "company")
            balance = frappe.db.sql("""
                SELECT SUM(debit - credit)
                FROM `tabGL Entry`
                WHERE account = %s AND company = %s AND is_cancelled = 0
            """, (bank_account, company))[0][0] or 0
            self.db_set("balance_after", balance)
    
    def cancel_journal_entry(self):
        """إلغاء القيد المحاسبي"""
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()
                frappe.msgprint(_("تم إلغاء القيد المحاسبي: {0}").format(self.journal_entry))


@frappe.whitelist()
def get_bank_balance(bank_account):
    """جلب رصيد الحساب البنكي"""
    account = frappe.db.get_value("Bank Account", bank_account, "account")
    company = frappe.db.get_value("Bank Account", bank_account, "company")
    
    if not account:
        return 0
    
    balance = frappe.db.sql("""
        SELECT SUM(debit - credit)
        FROM `tabGL Entry`
        WHERE account = %s AND company = %s AND is_cancelled = 0
    """, (account, company))[0][0] or 0
    
    return balance
