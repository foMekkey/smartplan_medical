# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PharmaApprovalMatrix(Document):
    def validate(self):
        self.validate_approval_levels()
    
    def validate_approval_levels(self):
        """التحقق من صحة مستويات الموافقة"""
        if not self.approval_levels:
            return
        
        # ترتيب المستويات
        levels = sorted(self.approval_levels, key=lambda x: x.level)
        
        prev_max = 0
        for level in levels:
            # التحقق من عدم وجود فجوات
            if level.min_amount and level.min_amount > prev_max:
                frappe.msgprint(_("تنبيه: هناك فجوة في المبالغ بين المستويات"))
            
            # التحقق من أن الحد الأدنى أقل من الأقصى
            if level.min_amount and level.max_amount:
                if level.min_amount >= level.max_amount:
                    frappe.throw(_("الحد الأدنى يجب أن يكون أقل من الحد الأقصى في المستوى {0}").format(level.level))
            
            prev_max = level.max_amount or float('inf')


def get_approver_for_amount(approval_type, amount):
    """الحصول على المعتمد المناسب للمبلغ"""
    try:
        matrix = frappe.get_doc("Pharma Approval Matrix", approval_type)
    except frappe.DoesNotExistError:
        return None
    
    if not matrix.is_active:
        return None
    
    # موافقة تلقائية
    if matrix.auto_approve_below and amount < matrix.auto_approve_below:
        return "auto"
    
    # البحث عن المستوى المناسب
    for level in sorted(matrix.approval_levels, key=lambda x: x.level):
        if level.min_amount and amount < level.min_amount:
            continue
        if level.max_amount and amount > level.max_amount:
            continue
        
        return {
            "role": level.approver_role,
            "user": level.specific_user,
            "can_reject": level.can_reject
        }
    
    return None


def check_approval_required(approval_type, amount=None, reference_doc=None):
    """التحقق مما إذا كانت الموافقة مطلوبة"""
    try:
        matrix = frappe.get_doc("Pharma Approval Matrix", approval_type)
    except frappe.DoesNotExistError:
        return False
    
    if not matrix.is_active:
        return False
    
    # موافقة تلقائية للمبالغ الصغيرة
    if amount and matrix.auto_approve_below and amount < matrix.auto_approve_below:
        return False
    
    return True
