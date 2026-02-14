# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, add_days


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "exception_type",
            "label": _("نوع الاستثناء"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "severity",
            "label": _("الأهمية"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "count",
            "label": _("العدد"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "amount",
            "label": _("المبلغ المتأثر"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "action_required",
            "label": _("الإجراء المطلوب"),
            "fieldtype": "Data",
            "width": 200
        }
    ]


def get_data(filters):
    data = []
    
    # 1. العمليات الفاشلة
    failed_processes = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabPharma Process Log`
        WHERE status = 'Failed'
        AND creation >= %s
    """, (add_days(nowdate(), -7),))[0][0] or 0
    
    data.append({
        "exception_type": "❌ عمليات فاشلة",
        "severity": "🔴 حرج",
        "count": failed_processes,
        "amount": 0,
        "action_required": "مراجعة سجل العمليات وإعادة المحاولة"
    })
    
    # 2. العمليات القابلة لإعادة المحاولة
    retryable_processes = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabPharma Process Log`
        WHERE status = 'Failed'
        AND retry_count < 3
        AND creation >= %s
    """, (add_days(nowdate(), -7),))[0][0] or 0
    
    data.append({
        "exception_type": "🔄 قابل لإعادة المحاولة",
        "severity": "🟡 متوسط",
        "count": retryable_processes,
        "amount": 0,
        "action_required": "تشغيل إعادة المحاولة التلقائية"
    })
    
    # 3. طلبات الموافقة المعلقة
    pending_approvals = frappe.db.sql("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(amount), 0) as amount
        FROM `tabPharma Approval Request`
        WHERE workflow_state = 'Pending'
        AND docstatus < 2
    """, as_dict=True)[0]
    
    data.append({
        "exception_type": "⏳ موافقات معلقة",
        "severity": "🟡 متوسط" if pending_approvals.get("count", 0) <= 5 else "🔴 حرج",
        "count": pending_approvals.get("count", 0),
        "amount": pending_approvals.get("amount", 0),
        "action_required": "مراجعة طلبات الموافقة والبت فيها"
    })
    
    # 4. التحصيلات غير المكتملة
    incomplete_collections = frappe.db.sql("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(wd.total_amount - COALESCE(dc.collected, 0)), 0) as amount
        FROM `tabWarehouse Dispatch` wd
        LEFT JOIN (
            SELECT warehouse_dispatch, SUM(collected_amount) as collected
            FROM `tabDelivery Collection`
            WHERE docstatus = 1
            GROUP BY warehouse_dispatch
        ) dc ON wd.name = dc.warehouse_dispatch
        WHERE wd.docstatus = 1
        AND wd.posting_date >= %s
        AND (dc.collected IS NULL OR dc.collected < wd.total_amount)
    """, (add_days(nowdate(), -30),), as_dict=True)[0]
    
    data.append({
        "exception_type": "💰 تحصيلات غير مكتملة",
        "severity": "🟡 متوسط",
        "count": incomplete_collections.get("count", 0),
        "amount": incomplete_collections.get("amount", 0),
        "action_required": "متابعة المندوبين لإتمام التحصيل"
    })
    
    # 5. مخزون قرب الانتهاء (أقل من 30 يوم)
    expiring_stock = frappe.db.sql("""
        SELECT COUNT(DISTINCT b.name) as count
        FROM `tabBatch` b
        INNER JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
        WHERE b.expiry_date IS NOT NULL
        AND b.expiry_date > CURDATE()
        AND DATEDIFF(b.expiry_date, CURDATE()) <= 30
        GROUP BY b.name
        HAVING SUM(sle.actual_qty) > 0
    """)
    expiring_count = len(expiring_stock) if expiring_stock else 0
    
    data.append({
        "exception_type": "⚠️ مخزون قرب الانتهاء (<30 يوم)",
        "severity": "🟠 عالي",
        "count": expiring_count,
        "amount": 0,
        "action_required": "أولوية صرف FEFO"
    })
    
    # 6. مخزون منتهي
    expired_stock = frappe.db.sql("""
        SELECT COUNT(DISTINCT b.name) as count
        FROM `tabBatch` b
        INNER JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
        WHERE b.expiry_date IS NOT NULL
        AND b.expiry_date < CURDATE()
        GROUP BY b.name
        HAVING SUM(sle.actual_qty) > 0
    """)
    expired_count = len(expired_stock) if expired_stock else 0
    
    data.append({
        "exception_type": "🚫 مخزون منتهي الصلاحية",
        "severity": "🔴 حرج",
        "count": expired_count,
        "amount": 0,
        "action_required": "إرجاع أو إتلاف فوري"
    })
    
    # 7. خصومات تحتاج موافقة
    pending_discount_approvals = frappe.db.sql("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(discount_amount), 0) as amount
        FROM `tabTele Sales Order`
        WHERE status = 'Pending Approval'
        AND requires_approval = 1
        AND docstatus = 0
    """, as_dict=True)[0]
    
    data.append({
        "exception_type": "🏷️ خصومات تحتاج موافقة",
        "severity": "🟡 متوسط",
        "count": pending_discount_approvals.get("count", 0),
        "amount": pending_discount_approvals.get("amount", 0),
        "action_required": "مراجعة واعتماد الخصومات"
    })
    
    return sorted(data, key=lambda x: ("حرج" in x.get("severity", ""), x.get("count", 0)), reverse=True)


def get_chart(data):
    critical = sum(1 for d in data if "حرج" in d.get("severity", "") and d.get("count", 0) > 0)
    high = sum(1 for d in data if "عالي" in d.get("severity", "") and d.get("count", 0) > 0)
    medium = sum(1 for d in data if "متوسط" in d.get("severity", "") and d.get("count", 0) > 0)
    
    return {
        "data": {
            "labels": ["حرج", "عالي", "متوسط"],
            "datasets": [{
                "name": _("عدد الاستثناءات"),
                "values": [critical, high, medium]
            }]
        },
        "type": "pie",
        "colors": ["#ff5858", "#ff9800", "#ffc107"]
    }


def get_summary(data):
    total_exceptions = sum(d.get("count", 0) for d in data)
    total_amount = sum(d.get("amount", 0) for d in data)
    critical_count = sum(d.get("count", 0) for d in data if "حرج" in d.get("severity", ""))
    
    return [
        {
            "value": total_exceptions,
            "indicator": "Red" if total_exceptions > 10 else "Orange",
            "label": _("إجمالي الاستثناءات"),
            "datatype": "Int"
        },
        {
            "value": critical_count,
            "indicator": "Red",
            "label": _("استثناءات حرجة"),
            "datatype": "Int"
        },
        {
            "value": total_amount,
            "indicator": "Orange",
            "label": _("المبالغ المتأثرة"),
            "datatype": "Currency"
        }
    ]
