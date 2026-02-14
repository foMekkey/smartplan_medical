# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, now, getdate


class DailyClosing(Document):
    def validate(self):
        self.check_duplicate_closing()
        self.load_transactions()
        self.calculate_balances()
        self.calculate_denominations_total()
    
    def check_duplicate_closing(self):
        """التحقق من عدم وجود إغلاق مكرر"""
        existing = frappe.db.exists("Daily Closing", {
            "cashbox": self.cashbox,
            "closing_date": self.closing_date,
            "docstatus": ["!=", 2],
            "name": ["!=", self.name]
        })
        if existing:
            frappe.throw(_("يوجد إغلاق يومي لهذه الخزينة في نفس التاريخ"))
    
    def load_transactions(self):
        """تحميل حركات اليوم"""
        self.transactions = []
        
        transactions = frappe.get_all("Cash Transaction",
            filters={
                "cashbox": self.cashbox,
                "posting_date": self.closing_date,
                "docstatus": 1
            },
            fields=["name", "transaction_type", "amount", "description", "party_name", "posting_time"],
            order_by="posting_time"
        )
        
        for t in transactions:
            self.append("transactions", {
                "transaction": t.name,
                "transaction_type": t.transaction_type,
                "amount": t.amount,
                "description": t.description,
                "party_name": t.party_name
            })
    
    def calculate_balances(self):
        """حساب الأرصدة"""
        # رصيد أول اليوم
        prev_closing = frappe.db.get_value("Daily Closing",
            {
                "cashbox": self.cashbox,
                "closing_date": ["<", self.closing_date],
                "docstatus": 1
            },
            "actual_balance",
            order_by="closing_date desc"
        )
        
        if prev_closing:
            self.opening_balance = flt(prev_closing)
        else:
            # أول إغلاق - استخدم الرصيد الافتتاحي للخزينة
            self.opening_balance = frappe.db.get_value("Cashbox", self.cashbox, "opening_balance") or 0
        
        # حساب المقبوضات والمصروفات
        self.total_receipts = sum(flt(t.amount) for t in self.transactions if t.transaction_type == "قبض")
        self.total_payments = sum(flt(t.amount) for t in self.transactions if t.transaction_type == "صرف")
        
        # الرصيد المتوقع
        self.expected_balance = flt(self.opening_balance) + flt(self.total_receipts) - flt(self.total_payments)
        
        # حساب الفرق
        self.difference = flt(self.actual_balance) - flt(self.expected_balance)
    
    def calculate_denominations_total(self):
        """حساب إجمالي فئات النقدية"""
        self.total_denominations = sum(flt(d.denomination_value) * flt(d.count) for d in self.denominations)
        
        # التحقق من تطابق الفئات مع الرصيد الفعلي
        if self.denominations and flt(self.total_denominations) != flt(self.actual_balance):
            frappe.msgprint(_("تنبيه: إجمالي الفئات ({0}) لا يساوي الرصيد الفعلي ({1})").format(
                self.total_denominations, self.actual_balance), alert=True)
    
    def on_submit(self):
        """عند الاعتماد"""
        self.handle_difference()
        self.update_cashbox_balance()
        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_at = now()
    
    def handle_difference(self):
        """معالجة فرق الخزينة"""
        if flt(self.difference) != 0:
            # إنشاء حركة تسوية
            self.create_difference_transaction()
    
    def create_difference_transaction(self):
        """إنشاء حركة فرق الخزينة"""
        cashbox = frappe.get_doc("Cashbox", self.cashbox)
        
        # تحديد نوع الحركة
        if flt(self.difference) > 0:
            transaction_type = "قبض"
            description = f"فرق زيادة - إغلاق يومي {self.closing_date}"
        else:
            transaction_type = "صرف"
            description = f"فرق نقص - إغلاق يومي {self.closing_date}"
        
        # حساب الفروقات (يجب إنشاؤه في شجرة الحسابات)
        difference_account = frappe.db.get_value("Account", 
            {"account_name": ["like", "%فروقات%"], "company": cashbox.company}, "name")
        
        if not difference_account:
            frappe.throw(_("يرجى إنشاء حساب 'فروقات الخزينة' في شجرة الحسابات"))
        
        ct = frappe.get_doc({
            "doctype": "Cash Transaction",
            "transaction_type": transaction_type,
            "cashbox": self.cashbox,
            "posting_date": self.closing_date,
            "amount": abs(flt(self.difference)),
            "description": description,
            "against_account": difference_account,
            "reference_type": "Daily Closing",
            "reference_name": self.name
        })
        ct.insert(ignore_permissions=True)
        ct.submit()
        
        frappe.msgprint(_("تم إنشاء حركة فرق الخزينة: {0}").format(ct.name))
    
    def update_cashbox_balance(self):
        """تحديث رصيد الخزينة"""
        frappe.db.set_value("Cashbox", self.cashbox, "current_balance", self.actual_balance)


@frappe.whitelist()
def get_closing_data(cashbox, closing_date):
    """جلب بيانات الإغلاق اليومي"""
    # رصيد أول اليوم
    prev_closing = frappe.db.get_value("Daily Closing",
        {
            "cashbox": cashbox,
            "closing_date": ["<", closing_date],
            "docstatus": 1
        },
        "actual_balance",
        order_by="closing_date desc"
    )
    
    if prev_closing:
        opening_balance = flt(prev_closing)
    else:
        opening_balance = frappe.db.get_value("Cashbox", cashbox, "opening_balance") or 0
    
    # حركات اليوم
    receipts = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabCash Transaction`
        WHERE cashbox = %s AND posting_date = %s AND transaction_type = 'قبض' AND docstatus = 1
    """, (cashbox, closing_date))[0][0] or 0
    
    payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabCash Transaction`
        WHERE cashbox = %s AND posting_date = %s AND transaction_type = 'صرف' AND docstatus = 1
    """, (cashbox, closing_date))[0][0] or 0
    
    expected_balance = flt(opening_balance) + flt(receipts) - flt(payments)
    
    return {
        "opening_balance": opening_balance,
        "total_receipts": receipts,
        "total_payments": payments,
        "expected_balance": expected_balance
    }
