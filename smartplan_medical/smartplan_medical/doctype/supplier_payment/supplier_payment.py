# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class SupplierPayment(Document):
    def validate(self):
        self.validate_amount()
        self.calculate_totals()
    
    def validate_amount(self):
        if flt(self.paid_amount) <= 0:
            frappe.throw(_("المبلغ المدفوع يجب أن يكون أكبر من صفر"))
    
    def calculate_totals(self):
        """حساب إجمالي المبالغ الموزعة"""
        self.total_allocated = sum(flt(d.allocated_amount) for d in self.payment_references)
        self.unallocated_amount = flt(self.paid_amount) - flt(self.total_allocated)
    
    def on_submit(self):
        """إنشاء قيد الدفع في ERPNext"""
        self.create_payment_entry()
        self.update_cashbox_if_cash()
        self.status = "Submitted"
    
    def on_cancel(self):
        """إلغاء قيد الدفع"""
        self.cancel_payment_entry()
        self.reverse_cashbox_if_cash()
        self.status = "Cancelled"
    
    def create_payment_entry(self):
        """إنشاء Payment Entry في ERPNext"""
        # تحديد حساب الدفع حسب طريقة الدفع
        paid_from = self.get_payment_account()
        
        # إنشاء Payment Entry
        pe = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "party_type": "Supplier",
            "party": self.supplier,
            "posting_date": self.posting_date,
            "paid_amount": flt(self.paid_amount),
            "received_amount": flt(self.paid_amount),
            "target_exchange_rate": 1,
            "paid_from": paid_from,
            "paid_from_account_currency": "EGP",
            "reference_no": self.reference_no or self.name,
            "reference_date": self.reference_date or self.posting_date,
            "remarks": f"دفعة للمورد: {self.supplier_name}\n{self.remarks or ''}"
        })
        
        # إضافة مراجع الفواتير إن وجدت
        if self.payment_references:
            for ref in self.payment_references:
                if ref.reference_doctype and ref.reference_name and flt(ref.allocated_amount) > 0:
                    pe.append("references", {
                        "reference_doctype": ref.reference_doctype,
                        "reference_name": ref.reference_name,
                        "allocated_amount": flt(ref.allocated_amount)
                    })
        
        pe.insert(ignore_permissions=True)
        pe.submit()
        
        self.db_set("payment_entry", pe.name)
        frappe.msgprint(_("تم إنشاء قيد الدفع: {0}").format(pe.name))
    
    def get_payment_account(self):
        """تحديد حساب الدفع حسب طريقة الدفع"""
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        
        if self.mode_of_payment == "نقدي":
            if self.from_cashbox:
                account = frappe.db.get_value("Cashbox", self.from_cashbox, "erp_account")
            else:
                account = frappe.db.get_value("Account", 
                    {"account_type": "Cash", "company": company, "is_group": 0}, "name")
        elif self.mode_of_payment == "شيك" or self.mode_of_payment == "تحويل بنكي":
            if self.bank_account:
                account = frappe.db.get_value("Bank Account", self.bank_account, "account")
            else:
                account = frappe.db.get_value("Account", 
                    {"account_type": "Bank", "company": company, "is_group": 0}, "name")
        else:
            account = frappe.db.get_value("Account", 
                {"account_type": "Cash", "company": company, "is_group": 0}, "name")
        
        if not account:
            frappe.throw(_("لم يتم العثور على حساب مناسب لطريقة الدفع"))
        
        return account
    
    def update_cashbox_if_cash(self):
        """تحديث رصيد الخزينة للدفع النقدي"""
        if self.mode_of_payment == "نقدي" and self.from_cashbox:
            cashbox = frappe.get_doc("Cashbox", self.from_cashbox)
            cashbox.update_balance(self.paid_amount, "payment")
    
    def reverse_cashbox_if_cash(self):
        """عكس تحديث الخزينة"""
        if self.mode_of_payment == "نقدي" and self.from_cashbox:
            cashbox = frappe.get_doc("Cashbox", self.from_cashbox)
            cashbox.update_balance(self.paid_amount, "receipt")
    
    def cancel_payment_entry(self):
        """إلغاء قيد الدفع"""
        if self.payment_entry:
            pe = frappe.get_doc("Payment Entry", self.payment_entry)
            if pe.docstatus == 1:
                pe.cancel()
                frappe.msgprint(_("تم إلغاء قيد الدفع: {0}").format(self.payment_entry))


@frappe.whitelist()
def get_supplier_outstanding_invoices(supplier):
    """جلب الفواتير المستحقة للمورد"""
    # جلب فواتير الشراء غير المسددة
    invoices = frappe.db.sql("""
        SELECT 
            'Purchase Invoice' as reference_doctype,
            pi.name as reference_name,
            pi.posting_date,
            pi.grand_total as total_amount,
            pi.outstanding_amount
        FROM `tabPurchase Invoice` pi
        WHERE pi.supplier = %s
            AND pi.docstatus = 1
            AND pi.outstanding_amount > 0
        ORDER BY pi.posting_date ASC
    """, (supplier,), as_dict=True)
    
    return invoices


@frappe.whitelist()
def allocate_payment_to_invoices(supplier, amount):
    """توزيع المبلغ تلقائياً على الفواتير (FIFO)"""
    invoices = get_supplier_outstanding_invoices(supplier)
    
    remaining = flt(amount)
    allocations = []
    
    for inv in invoices:
        if remaining <= 0:
            break
        
        allocated = min(remaining, flt(inv.outstanding_amount))
        allocations.append({
            "reference_doctype": inv.reference_doctype,
            "reference_name": inv.reference_name,
            "total_amount": inv.total_amount,
            "outstanding_amount": inv.outstanding_amount,
            "allocated_amount": allocated
        })
        remaining -= allocated
    
    return allocations
