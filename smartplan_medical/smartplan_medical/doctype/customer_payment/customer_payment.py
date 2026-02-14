# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate


class CustomerPayment(Document):
    def validate(self):
        self.validate_amount()
        self.calculate_totals()
        self.get_or_create_erp_customer()
    
    def validate_amount(self):
        if flt(self.paid_amount) <= 0:
            frappe.throw(_("المبلغ المدفوع يجب أن يكون أكبر من صفر"))
    
    def calculate_totals(self):
        """حساب إجمالي المبالغ الموزعة"""
        self.total_allocated = sum(flt(d.allocated_amount) for d in self.payment_references)
        self.unallocated_amount = flt(self.paid_amount) - flt(self.total_allocated)
    
    def get_or_create_erp_customer(self):
        """ربط أو إنشاء عميل في ERPNext Core"""
        if not self.customer:
            return
        
        pharma_customer = frappe.get_doc("Pharma Customer", self.customer)
        
        # البحث عن عميل ERPNext مرتبط
        erp_customer = frappe.db.get_value("Customer", 
            {"custom_pharma_customer": self.customer}, "name")
        
        if not erp_customer:
            # إنشاء عميل جديد في ERPNext
            new_customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": pharma_customer.legal_name,
                "customer_type": "Company",
                "customer_group": "Commercial",
                "territory": "Egypt",
                "custom_pharma_customer": self.customer,
                "tax_id": pharma_customer.tax_card or ""
            })
            new_customer.insert(ignore_permissions=True)
            erp_customer = new_customer.name
            frappe.msgprint(_("تم إنشاء عميل ERPNext: {0}").format(erp_customer))
        
        self.erp_customer = erp_customer
    
    def on_submit(self):
        """إنشاء قيد التحصيل في ERPNext"""
        self.create_payment_entry()
        self.status = "Submitted"
    
    def on_cancel(self):
        """إلغاء قيد التحصيل"""
        self.cancel_payment_entry()
        self.status = "Cancelled"
    
    def create_payment_entry(self):
        """إنشاء Payment Entry في ERPNext"""
        if not self.erp_customer:
            frappe.throw(_("يجب ربط العميل بعميل ERPNext أولاً"))
        
        # تحديد حساب الدفع حسب طريقة الدفع
        paid_to = self.get_payment_account()
        
        # إنشاء Payment Entry
        pe = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": self.erp_customer,
            "posting_date": self.posting_date,
            "paid_amount": flt(self.paid_amount),
            "received_amount": flt(self.paid_amount),
            "target_exchange_rate": 1,
            "paid_to": paid_to,
            "paid_to_account_currency": "EGP",
            "reference_no": self.reference_no or self.name,
            "reference_date": self.reference_date or self.posting_date,
            "remarks": f"تحصيل من عميل: {self.customer_name}\n{self.remarks or ''}"
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
        frappe.msgprint(_("تم إنشاء قيد التحصيل: {0}").format(pe.name))
    
    def get_payment_account(self):
        """تحديد حساب الدفع حسب طريقة الدفع"""
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        
        if self.mode_of_payment == "نقدي":
            # حساب الخزينة
            account = frappe.db.get_value("Mode of Payment Account", 
                {"parent": "Cash", "company": company}, "default_account")
            if not account:
                account = frappe.db.get_value("Account", 
                    {"account_type": "Cash", "company": company, "is_group": 0}, "name")
        elif self.mode_of_payment == "شيك":
            # حساب الشيكات تحت التحصيل
            account = frappe.db.get_value("Account", 
                {"account_name": ["like", "%شيك%"], "company": company, "is_group": 0}, "name")
            if not account:
                account = frappe.db.get_value("Account", 
                    {"account_type": "Receivable", "company": company, "is_group": 0}, "name")
        else:
            # حساب البنك
            if self.bank_account:
                account = frappe.db.get_value("Bank Account", self.bank_account, "account")
            else:
                account = frappe.db.get_value("Account", 
                    {"account_type": "Bank", "company": company, "is_group": 0}, "name")
        
        if not account:
            frappe.throw(_("لم يتم العثور على حساب مناسب لطريقة الدفع"))
        
        return account
    
    def cancel_payment_entry(self):
        """إلغاء قيد التحصيل"""
        if self.payment_entry:
            pe = frappe.get_doc("Payment Entry", self.payment_entry)
            if pe.docstatus == 1:
                pe.cancel()
                frappe.msgprint(_("تم إلغاء قيد التحصيل: {0}").format(self.payment_entry))


@frappe.whitelist()
def get_customer_outstanding_invoices(customer):
    """جلب الفواتير المستحقة للعميل"""
    pharma_customer = frappe.get_doc("Pharma Customer", customer)
    
    erp_customer = frappe.db.get_value("Customer", 
        {"custom_pharma_customer": customer}, "name")
    
    if not erp_customer:
        return []
    
    # جلب فواتير المبيعات غير المسددة
    invoices = frappe.db.sql("""
        SELECT 
            'Sales Invoice' as reference_doctype,
            si.name as reference_name,
            si.posting_date,
            si.grand_total as total_amount,
            si.outstanding_amount
        FROM `tabSales Invoice` si
        WHERE si.customer = %s
            AND si.docstatus = 1
            AND si.outstanding_amount > 0
        ORDER BY si.posting_date ASC
    """, (erp_customer,), as_dict=True)
    
    return invoices


@frappe.whitelist()
def allocate_payment_to_invoices(customer, amount):
    """توزيع المبلغ تلقائياً على الفواتير (FIFO)"""
    invoices = get_customer_outstanding_invoices(customer)
    
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
