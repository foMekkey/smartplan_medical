# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate, getdate


def validate_dispatch(doc, method=None):
    """التحقق من صحة إذن الصرف"""
    settings = get_workflow_settings()
    if not settings:
        return
    
    # التحقق من المخزون
    if settings.validate_stock_on_dispatch:
        validate_stock_availability(doc)
    
    # التحقق من صلاحية التشغيلات
    if settings.check_batch_expiry:
        validate_batch_expiry(doc, settings.min_batch_expiry_days)
    
    # إلزام FEFO
    if settings.enforce_fefo:
        validate_fefo(doc)


def validate_collection(doc, method=None):
    """التحقق من صحة التحصيل"""
    settings = get_workflow_settings()
    if not settings:
        return
    
    # التحقق من مطابقة المبلغ
    if hasattr(doc, 'expected_amount') and hasattr(doc, 'collected_amount'):
        if flt(doc.collected_amount) != flt(doc.expected_amount):
            # إنشاء طلب موافقة للتحصيل غير المطابق
            from smartplan_medical.smartplan_medical.doctype.pharma_approval_request.pharma_approval_request import create_approval_request
            
            difference = abs(flt(doc.collected_amount) - flt(doc.expected_amount))
            
            create_approval_request(
                approval_type="تحصيل غير مطابق",
                reference_doctype=doc.doctype,
                reference_docname=doc.name,
                customer=doc.customer if hasattr(doc, 'customer') else None,
                amount=flt(doc.collected_amount),
                current_value=flt(doc.collected_amount),
                limit_value=flt(doc.expected_amount),
                reason=f"فرق في التحصيل بقيمة {difference}"
            )


def validate_tele_sales_order(doc, method=None):
    """التحقق من صحة طلب المبيعات الهاتفية"""
    settings = get_workflow_settings()
    if not settings:
        return
    
    # التحقق من حد الخصم
    if settings.max_discount_percent:
        validate_discount(doc, settings.max_discount_percent)
    
    # التحقق من حد الائتمان
    if settings.check_credit_limit and hasattr(doc, 'customer'):
        validate_credit_limit(doc)
    
    # التحقق من حالة العميل
    if settings.check_customer_blocked and hasattr(doc, 'customer'):
        validate_customer_status(doc)


def get_workflow_settings():
    """الحصول على إعدادات سير العمل"""
    try:
        return frappe.get_single("Pharma Workflow Settings")
    except:
        return None


def validate_stock_availability(doc):
    """التحقق من توفر المخزون"""
    if not hasattr(doc, 'items'):
        return
    
    # Get warehouse from parent document
    warehouse = None
    if doc.doctype == "Warehouse Dispatch":
        # For Warehouse Dispatch, get ERPNext warehouse from Pharma Warehouse
        if hasattr(doc, 'warehouse') and doc.warehouse:
            pharma_warehouse = frappe.get_doc("Pharma Warehouse", doc.warehouse)
            if not pharma_warehouse.erpnext_warehouse:
                frappe.throw(_("المخزن {0} غير مربوط بمخزن ERPNext").format(doc.warehouse))
            warehouse = pharma_warehouse.erpnext_warehouse
    elif hasattr(doc, 'warehouse'):
        # For other doctypes, use warehouse directly
        warehouse = doc.warehouse
    
    if not warehouse:
        return
    
    for item in doc.items:
        # Use warehouse from parent, not from item
        actual_qty = frappe.db.get_value("Bin", 
            {"item_code": item.item_code, "warehouse": warehouse},
            "actual_qty") or 0
        
        if flt(item.qty) > flt(actual_qty):
            frappe.throw(_("الكمية المطلوبة ({0}) أكبر من المتاح ({1}) للصنف {2} في مخزن {3}").format(
                item.qty, actual_qty, item.item_code, warehouse
            ))


def validate_batch_expiry(doc, min_days=30):
    """التحقق من صلاحية التشغيلات"""
    if not hasattr(doc, 'items'):
        return
    
    for item in doc.items:
        if not item.batch_no:
            continue
        
        expiry_date = frappe.db.get_value("Batch", item.batch_no, "expiry_date")
        if not expiry_date:
            continue
        
        days_to_expiry = (getdate(expiry_date) - getdate(nowdate())).days
        
        if days_to_expiry <= 0:
            frappe.throw(_("التشغيلة {0} منتهية الصلاحية").format(item.batch_no))
        
        if days_to_expiry < min_days:
            frappe.throw(_("التشغيلة {0} ستنتهي صلاحيتها خلال {1} يوم فقط (الحد الأدنى {2} يوم)").format(
                item.batch_no, days_to_expiry, min_days
            ))


def validate_fefo(doc):
    """التحقق من التزام FEFO - الأقرب انتهاءً أولاً"""
    if not hasattr(doc, 'items'):
        return
    
    for item in doc.items:
        if not item.batch_no:
            continue
        
        # البحث عن تشغيلة أقرب انتهاءً
        earlier_batch = frappe.db.sql("""
            SELECT b.name, b.expiry_date
            FROM `tabBatch` b
            INNER JOIN `tabStock Ledger Entry` sle ON b.name = sle.batch_no
            WHERE sle.item_code = %s
                AND sle.warehouse = %s
                AND b.expiry_date IS NOT NULL
                AND b.expiry_date > CURDATE()
                AND b.name != %s
            GROUP BY b.name
            HAVING SUM(sle.actual_qty) > 0
            ORDER BY b.expiry_date ASC
            LIMIT 1
        """, (item.item_code, item.warehouse, item.batch_no), as_dict=True)
        
        if earlier_batch:
            current_expiry = frappe.db.get_value("Batch", item.batch_no, "expiry_date")
            if getdate(earlier_batch[0].expiry_date) < getdate(current_expiry):
                frappe.msgprint(_("تنبيه FEFO: هناك تشغيلة ({0}) تنتهي قبل التشغيلة المحددة ({1}) للصنف {2}").format(
                    earlier_batch[0].name, item.batch_no, item.item_code
                ), indicator="orange", alert=True)


def validate_discount(doc, max_discount_percent):
    """التحقق من حد الخصم"""
    if not hasattr(doc, 'discount_percent'):
        return
    
    if flt(doc.discount_percent) > flt(max_discount_percent):
        # التحقق من وجود موافقة مسبقة
        if hasattr(doc, 'discount_approved') and doc.discount_approved:
            return
        
        # إنشاء طلب موافقة
        from smartplan_medical.smartplan_medical.doctype.pharma_approval_request.pharma_approval_request import create_approval_request
        
        request = create_approval_request(
            approval_type="تجاوز حد الخصم",
            reference_doctype=doc.doctype,
            reference_docname=doc.name,
            customer=doc.customer if hasattr(doc, 'customer') else None,
            amount=flt(doc.discount_amount) if hasattr(doc, 'discount_amount') else 0,
            current_value=flt(doc.discount_percent),
            limit_value=flt(max_discount_percent),
            reason=f"نسبة خصم {doc.discount_percent}% تتجاوز الحد المسموح {max_discount_percent}%"
        )
        
        frappe.throw(_("نسبة الخصم ({0}%) تتجاوز الحد المسموح ({1}%). تم إنشاء طلب موافقة رقم {2}").format(
            doc.discount_percent, max_discount_percent, request.name
        ))


def validate_credit_limit(doc):
    """التحقق من حد الائتمان"""
    if not doc.customer:
        return
    
    # جلب حد الائتمان من العميل
    customer = frappe.get_doc("Pharma Customer", doc.customer) if frappe.db.exists("Pharma Customer", doc.customer) else None
    if not customer:
        return
    
    credit_limit = flt(customer.credit_limit) if hasattr(customer, 'credit_limit') else 0
    if not credit_limit:
        return
    
    # حساب الرصيد المستحق
    outstanding = get_customer_outstanding(doc.customer)
    order_amount = flt(doc.net_amount) if hasattr(doc, 'net_amount') else flt(doc.total_amount) if hasattr(doc, 'total_amount') else 0
    
    if flt(outstanding) + flt(order_amount) > credit_limit:
        # التحقق من وجود موافقة
        if hasattr(doc, 'credit_approved') and doc.credit_approved:
            return
        
        # إنشاء طلب موافقة
        from smartplan_medical.smartplan_medical.doctype.pharma_approval_request.pharma_approval_request import create_approval_request
        
        request = create_approval_request(
            approval_type="تجاوز حد الائتمان",
            reference_doctype=doc.doctype,
            reference_docname=doc.name,
            customer=doc.customer,
            amount=order_amount,
            current_value=flt(outstanding) + flt(order_amount),
            limit_value=credit_limit,
            reason=f"تجاوز حد الائتمان للعميل"
        )
        
        frappe.throw(_("العميل تجاوز حد الائتمان ({0}). الرصيد المستحق: {1}. تم إنشاء طلب موافقة رقم {2}").format(
            credit_limit, outstanding, request.name
        ))


def validate_customer_status(doc):
    """التحقق من حالة العميل"""
    if not doc.customer:
        return
    
    customer = frappe.get_doc("Pharma Customer", doc.customer) if frappe.db.exists("Pharma Customer", doc.customer) else None
    if not customer:
        return
    
    is_blocked = customer.is_blocked if hasattr(customer, 'is_blocked') else 0
    
    if is_blocked:
        # التحقق من وجود موافقة
        if hasattr(doc, 'blocked_customer_approved') and doc.blocked_customer_approved:
            return
        
        # إنشاء طلب موافقة
        from smartplan_medical.smartplan_medical.doctype.pharma_approval_request.pharma_approval_request import create_approval_request
        
        request = create_approval_request(
            approval_type="بيع لعميل محجوب",
            reference_doctype=doc.doctype,
            reference_docname=doc.name,
            customer=doc.customer,
            reason="العميل محجوب عن البيع"
        )
        
        frappe.throw(_("العميل محجوب عن البيع. تم إنشاء طلب موافقة رقم {0}").format(request.name))


def get_customer_outstanding(customer):
    """حساب الرصيد المستحق للعميل"""
    # من الفواتير غير المسددة
    outstanding = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) as outstanding
        FROM `tabSales Invoice`
        WHERE customer = %s
            AND docstatus = 1
            AND outstanding_amount > 0
    """, (customer,))
    
    return flt(outstanding[0][0]) if outstanding else 0


def create_process_log_on_dispatch(doc, method=None):
    """إنشاء سجل عمليات عند صرف المخزن"""
    settings = get_workflow_settings()
    if not settings or not settings.log_all_processes:
        return
    
    from smartplan_medical.smartplan_medical.doctype.pharma_process_log.pharma_process_log import create_process_log
    
    log = create_process_log(
        source_doctype="Warehouse Dispatch",
        source_docname=doc.name,
        target_doctype="Sales Invoice" if settings.auto_create_invoice else None
    )
    
    if settings.auto_create_invoice:
        try:
            log.process_document()
        except Exception as e:
            frappe.log_error(message=str(e), title="Auto Invoice Creation Failed")


def create_process_log_on_collection(doc, method=None):
    """إنشاء سجل عمليات عند التحصيل"""
    settings = get_workflow_settings()
    if not settings or not settings.log_all_processes:
        return
    
    from smartplan_medical.smartplan_medical.doctype.pharma_process_log.pharma_process_log import create_process_log
    
    log = create_process_log(
        source_doctype="Delivery Collection",
        source_docname=doc.name,
        target_doctype="Payment Entry" if settings.auto_create_payment else None
    )
    
    if settings.auto_create_payment:
        try:
            log.process_document()
        except Exception as e:
            frappe.log_error(message=str(e), title="Auto Payment Entry Creation Failed")
