# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, now_datetime, date_diff


def check_expiring_batches():
    """فحص التشغيلات قريبة الانتهاء وإرسال إشعارات"""
    try:
        settings = frappe.get_single("Pharma Workflow Settings")
        warning_days = settings.batch_expiry_warning_days or 90
    except:
        warning_days = 90
    
    warning_date = add_days(nowdate(), warning_days)
    
    expiring_batches = frappe.db.sql("""
        SELECT 
            sle.item_code,
            i.item_name,
            sle.batch_no,
            sle.warehouse,
            b.expiry_date,
            SUM(sle.actual_qty) as qty
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabBatch` b ON sle.batch_no = b.name
        INNER JOIN `tabItem` i ON sle.item_code = i.name
        WHERE sle.batch_no IS NOT NULL
            AND b.expiry_date IS NOT NULL
            AND b.expiry_date <= %s
            AND b.expiry_date > CURDATE()
        GROUP BY sle.item_code, sle.batch_no, sle.warehouse
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY b.expiry_date ASC
        LIMIT 100
    """, (warning_date,), as_dict=True)
    
    if expiring_batches:
        # إرسال إشعار لمديري المخزن
        stock_managers = frappe.get_all("Has Role", 
            filters={"role": "Stock Manager", "parenttype": "User"},
            pluck="parent")
        
        for user in stock_managers:
            frappe.publish_realtime(
                event="pharma_expiring_batches",
                message={
                    "count": len(expiring_batches),
                    "warning_days": warning_days
                },
                user=user
            )
        
        frappe.log_error(
            message=f"Found {len(expiring_batches)} batches expiring within {warning_days} days",
            title="Expiring Batches Alert"
        )


def escalate_pending_approvals():
    """تصعيد طلبات الموافقة المعلقة"""
    # جلب طلبات الموافقة المعلقة
    pending_requests = frappe.get_all("Pharma Approval Request",
        filters={
            "workflow_state": ["in", ["مُرسل", "قيد المراجعة"]],
            "docstatus": 1
        },
        fields=["name", "approval_type", "request_date", "amount", "requested_by"]
    )
    
    for request in pending_requests:
        try:
            matrix = frappe.get_doc("Pharma Approval Matrix", request.approval_type)
            escalation_hours = matrix.escalation_hours or 24
            
            # حساب الوقت منذ الطلب
            hours_since_request = date_diff(nowdate(), request.request_date) * 24
            
            if hours_since_request >= escalation_hours:
                # تصعيد للدور المحدد
                if matrix.escalation_role:
                    escalation_users = frappe.get_all("Has Role",
                        filters={"role": matrix.escalation_role, "parenttype": "User"},
                        pluck="parent")
                    
                    for user in escalation_users:
                        frappe.publish_realtime(
                            event="pharma_approval_escalation",
                            message={
                                "request": request.name,
                                "type": request.approval_type,
                                "hours_pending": hours_since_request
                            },
                            user=user
                        )
        except:
            pass


def retry_failed_processes():
    """إعادة محاولة العمليات الفاشلة"""
    try:
        settings = frappe.get_single("Pharma Workflow Settings")
        if not settings.retry_failed_on_schedule:
            return
        
        max_attempts = settings.max_retry_attempts or 3
    except:
        return
    
    # جلب العمليات الفاشلة القابلة لإعادة المحاولة
    failed_processes = frappe.get_all("Pharma Process Log",
        filters={
            "status": "Failed",
            "can_retry": 1,
            "retry_count": ["<", max_attempts]
        },
        fields=["name"]
    )
    
    for process in failed_processes:
        try:
            doc = frappe.get_doc("Pharma Process Log", process.name)
            doc.retry_process()
        except Exception as e:
            frappe.log_error(
                message=str(e),
                title=f"Failed to retry process {process.name}"
            )
