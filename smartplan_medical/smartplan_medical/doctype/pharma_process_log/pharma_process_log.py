# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class PharmaProcessLog(Document):
    def before_insert(self):
        self.add_audit_entry("إنشاء", None, self.status)
    
    def before_save(self):
        if self.has_value_changed("status"):
            old_status = self.get_doc_before_save().status if self.get_doc_before_save() else None
            self.add_audit_entry("تغيير الحالة", old_status, self.status)
    
    def add_audit_entry(self, action, old_value=None, new_value=None, remarks=None):
        self.append("audit_log", {
            "timestamp": now_datetime(),
            "user": frappe.session.user,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "remarks": remarks
        })
    
    @frappe.whitelist()
    def retry_process(self):
        """إعادة محاولة المعالجة"""
        if not self.can_retry:
            frappe.throw(_("هذا السجل غير قابل لإعادة المحاولة"))
        
        self.status = "Retry"
        self.retry_count = (self.retry_count or 0) + 1
        self.last_retry_date = now_datetime()
        self.add_audit_entry("إعادة محاولة", None, f"المحاولة رقم {self.retry_count}")
        self.save()
        
        # محاولة إعادة المعالجة
        try:
            self.process_document()
        except Exception as e:
            self.status = "Failed"
            self.error_message = str(e)
            self.error_traceback = frappe.get_traceback()
            self.add_audit_entry("فشل", None, str(e))
            self.save()
            frappe.throw(_("فشلت إعادة المعالجة: {0}").format(str(e)))
    
    def process_document(self):
        """معالجة المستند حسب نوعه"""
        if self.source_doctype == "Warehouse Dispatch":
            self.create_sales_invoice()
        elif self.source_doctype == "Delivery Collection":
            self.create_payment_entry()
    
    def create_sales_invoice(self):
        """إنشاء فاتورة مبيعات من إذن الصرف"""
        settings = frappe.get_single("Pharma Workflow Settings")
        if not settings.auto_create_invoice:
            return
        
        dispatch = frappe.get_doc("Warehouse Dispatch", self.source_docname)
        
        # إنشاء الفاتورة
        si = frappe.new_doc("Sales Invoice")
        si.customer = dispatch.customer
        si.posting_date = dispatch.posting_date
        si.pharma_dispatch_ref = dispatch.name
        
        for item in dispatch.items:
            si.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate,
                "batch_no": item.batch_no,
                "warehouse": item.warehouse
            })
        
        si.insert(ignore_permissions=True)
        si.submit()
        
        # تحديث سجل العمليات
        self.target_doctype = "Sales Invoice"
        self.target_docname = si.name
        self.status = "Success"
        self.process_date = now_datetime()
        self.processed_by = frappe.session.user
        self.add_audit_entry("إنشاء فاتورة", None, si.name)
        self.save()
    
    def create_payment_entry(self):
        """إنشاء قيد دفع من التحصيل"""
        settings = frappe.get_single("Pharma Workflow Settings")
        if not settings.auto_create_payment:
            return
        
        collection = frappe.get_doc("Delivery Collection", self.source_docname)
        
        # إنشاء قيد الدفع
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive"
        pe.party_type = "Customer"
        pe.party = collection.customer
        pe.paid_amount = collection.collected_amount
        pe.received_amount = collection.collected_amount
        pe.pharma_collection_ref = collection.name
        
        pe.insert(ignore_permissions=True)
        pe.submit()
        
        # تحديث سجل العمليات
        self.target_doctype = "Payment Entry"
        self.target_docname = pe.name
        self.status = "Success"
        self.process_date = now_datetime()
        self.processed_by = frappe.session.user
        self.add_audit_entry("إنشاء قيد دفع", None, pe.name)
        self.save()


def create_process_log(source_doctype, source_docname, target_doctype=None):
    """إنشاء سجل عمليات جديد"""
    log = frappe.new_doc("Pharma Process Log")
    log.source_doctype = source_doctype
    log.source_docname = source_docname
    log.target_doctype = target_doctype
    log.status = "Pending"
    log.insert(ignore_permissions=True)
    return log
