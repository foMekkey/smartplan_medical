# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PharmaWorkflowSettings(Document):
    pass


def get_settings():
    """الحصول على إعدادات سير العمل"""
    return frappe.get_single("Pharma Workflow Settings")


def is_workflow_enabled():
    """التحقق من تفعيل سير العمل"""
    settings = get_settings()
    return settings.enable_workflow if settings else False


def should_auto_create_invoice():
    """التحقق من إعداد الإنشاء التلقائي للفواتير"""
    settings = get_settings()
    return settings.auto_create_invoice if settings else False


def should_auto_create_payment():
    """التحقق من إعداد الإنشاء التلقائي لقيود الدفع"""
    settings = get_settings()
    return settings.auto_create_payment if settings else False


def get_max_discount_percent():
    """الحصول على أقصى نسبة خصم مسموحة"""
    settings = get_settings()
    return settings.max_discount_percent if settings else 10


def get_batch_expiry_warning_days():
    """الحصول على أيام تحذير الصلاحية"""
    settings = get_settings()
    return settings.batch_expiry_warning_days if settings else 90


def should_check_credit_limit():
    """التحقق من إعداد فحص حد الائتمان"""
    settings = get_settings()
    return settings.check_credit_limit if settings else True


def should_enforce_fefo():
    """التحقق من إعداد FEFO"""
    settings = get_settings()
    return settings.enforce_fefo if settings else True
