# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, nowdate


class PharmaApprovalRequest(Document):
    def before_insert(self):
        if not self.requested_by:
            self.requested_by = frappe.session.user
        if not self.request_date:
            self.request_date = nowdate()
        self.add_audit_entry("إنشاء طلب موافقة")
    
    def validate(self):
        self.calculate_exceeded_value()
        self.validate_workflow_state()
    
    def before_submit(self):
        if self.workflow_state == "مسودة":
            self.workflow_state = "مُرسل"
        self.add_audit_entry("إرسال الطلب", "مسودة", "مُرسل")
    
    def on_submit(self):
        self.notify_approvers()
    
    def calculate_exceeded_value(self):
        """حساب قيمة التجاوز"""
        if self.current_value and self.limit_value:
            self.exceeded_value = max(0, self.current_value - self.limit_value)
    
    def validate_workflow_state(self):
        """التحقق من صحة تغيير الحالة"""
        if self.is_new():
            return
        
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        
        old_state = old_doc.workflow_state
        new_state = self.workflow_state
        
        # الحالات المسموح بها للانتقال
        allowed_transitions = {
            "مسودة": ["مُرسل"],
            "مُرسل": ["قيد المراجعة", "مُعتمد", "مرفوض"],
            "قيد المراجعة": ["مُعتمد", "مرفوض"],
            "مُعتمد": ["مُغلق"],
            "مرفوض": ["مُغلق"],
            "مُغلق": []
        }
        
        if new_state != old_state:
            if new_state not in allowed_transitions.get(old_state, []):
                frappe.throw(_("لا يمكن الانتقال من حالة '{0}' إلى '{1}'").format(old_state, new_state))
    
    def add_audit_entry(self, action, old_value=None, new_value=None, remarks=None):
        """إضافة سجل تدقيق"""
        self.append("audit_log", {
            "timestamp": now_datetime(),
            "user": frappe.session.user,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "remarks": remarks
        })
    
    @frappe.whitelist()
    def approve(self, remarks=None):
        """الموافقة على الطلب"""
        if self.workflow_state in ["مُعتمد", "مرفوض", "مُغلق"]:
            frappe.throw(_("لا يمكن تغيير حالة طلب تم البت فيه"))
        
        self.workflow_state = "مُعتمد"
        self.approved_by = frappe.session.user
        self.approval_date = now_datetime()
        self.approval_remarks = remarks
        self.add_audit_entry("موافقة", self.workflow_state, "مُعتمد", remarks)
        self.save(ignore_permissions=True)
        
        # تنفيذ الإجراء المرتبط
        self.execute_approval_action()
        
        frappe.msgprint(_("تمت الموافقة على الطلب بنجاح"))
    
    @frappe.whitelist()
    def reject(self, remarks=None):
        """رفض الطلب"""
        if self.workflow_state in ["مُعتمد", "مرفوض", "مُغلق"]:
            frappe.throw(_("لا يمكن تغيير حالة طلب تم البت فيه"))
        
        if not remarks:
            frappe.throw(_("يجب إدخال سبب الرفض"))
        
        self.workflow_state = "مرفوض"
        self.approved_by = frappe.session.user
        self.approval_date = now_datetime()
        self.approval_remarks = remarks
        self.add_audit_entry("رفض", self.workflow_state, "مرفوض", remarks)
        self.save(ignore_permissions=True)
        
        frappe.msgprint(_("تم رفض الطلب"))
    
    @frappe.whitelist()
    def set_under_review(self):
        """وضع الطلب قيد المراجعة"""
        if self.workflow_state != "مُرسل":
            frappe.throw(_("يمكن وضع الطلبات المُرسلة فقط قيد المراجعة"))
        
        self.workflow_state = "قيد المراجعة"
        self.add_audit_entry("بدء المراجعة", "مُرسل", "قيد المراجعة")
        self.save(ignore_permissions=True)
    
    def execute_approval_action(self):
        """تنفيذ الإجراء بعد الموافقة"""
        if self.reference_doctype and self.reference_docname:
            try:
                ref_doc = frappe.get_doc(self.reference_doctype, self.reference_docname)
                
                # تحديث المستند المرجعي حسب نوع الموافقة
                if self.approval_type == "تجاوز حد الخصم":
                    if hasattr(ref_doc, 'discount_approved'):
                        ref_doc.discount_approved = 1
                        ref_doc.save(ignore_permissions=True)
                
                elif self.approval_type == "تجاوز حد الائتمان":
                    if hasattr(ref_doc, 'credit_approved'):
                        ref_doc.credit_approved = 1
                        ref_doc.save(ignore_permissions=True)
                
                elif self.approval_type == "بيع لعميل محجوب":
                    if hasattr(ref_doc, 'blocked_customer_approved'):
                        ref_doc.blocked_customer_approved = 1
                        ref_doc.save(ignore_permissions=True)
                
            except Exception as e:
                frappe.log_error(f"Error executing approval action: {str(e)}")
    
    def notify_approvers(self):
        """إرسال إشعار للمعتمدين"""
        try:
            # جلب مصفوفة الموافقات
            matrix = frappe.get_doc("Pharma Approval Matrix", self.approval_type)
            if not matrix or not matrix.notify_on_request:
                return
            
            # جلب المعتمدين حسب المستوى والمبلغ
            for level in matrix.approval_levels:
                if level.min_amount and self.amount < level.min_amount:
                    continue
                if level.max_amount and self.amount > level.max_amount:
                    continue
                
                users = []
                if level.specific_user:
                    users.append(level.specific_user)
                elif level.approver_role:
                    users = frappe.get_all("Has Role", 
                        filters={"role": level.approver_role, "parenttype": "User"},
                        pluck="parent")
                
                for user in users:
                    self.send_notification(user)
                
                break  # إرسال للمستوى الأول المطابق فقط
                
        except frappe.DoesNotExistError:
            pass  # لا توجد مصفوفة موافقات
    
    def send_notification(self, user):
        """إرسال إشعار لمستخدم"""
        frappe.publish_realtime(
            event="pharma_approval_request",
            message={
                "name": self.name,
                "type": self.approval_type,
                "amount": self.amount,
                "requested_by": self.requested_by
            },
            user=user
        )


def create_approval_request(approval_type, reference_doctype, reference_docname, 
                           customer=None, amount=None, current_value=None, 
                           limit_value=None, reason=None):
    """دالة مساعدة لإنشاء طلب موافقة"""
    request = frappe.new_doc("Pharma Approval Request")
    request.approval_type = approval_type
    request.reference_doctype = reference_doctype
    request.reference_docname = reference_docname
    request.customer = customer
    request.amount = amount
    request.current_value = current_value
    request.limit_value = limit_value
    request.reason = reason or f"طلب موافقة على {approval_type}"
    request.insert(ignore_permissions=True)
    return request
