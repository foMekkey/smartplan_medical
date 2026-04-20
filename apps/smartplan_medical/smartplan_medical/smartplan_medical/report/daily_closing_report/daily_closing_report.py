# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate, getdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data, filters)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "metric",
            "label": _("البند"),
            "fieldtype": "Data",
            "width": 250
        },
        {
            "fieldname": "count",
            "label": _("العدد"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "amount",
            "label": _("المبلغ"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "status",
            "label": _("الحالة"),
            "fieldtype": "Data",
            "width": 100
        }
    ]


def get_data(filters):
    report_date = filters.get("report_date") or nowdate()
    
    data = []
    
    # 1. طلبات التلي سيلز
    tso_data = frappe.db.sql("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(net_amount), 0) as amount
        FROM `tabTele Sales Order`
        WHERE docstatus = 1 AND order_date = %s
    """, (report_date,), as_dict=True)[0]
    
    data.append({
        "metric": "📋 طلبات التلي سيلز المعتمدة",
        "count": tso_data.get("count", 0),
        "amount": tso_data.get("amount", 0),
        "status": "✅" if tso_data.get("count", 0) > 0 else "⚪"
    })
    
    # 2. عمليات الصرف
    dispatch_data = frappe.db.sql("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(total_amount), 0) as amount
        FROM `tabWarehouse Dispatch`
        WHERE docstatus = 1 AND posting_date = %s
    """, (report_date,), as_dict=True)[0]
    
    data.append({
        "metric": "📦 عمليات الصرف",
        "count": dispatch_data.get("count", 0),
        "amount": dispatch_data.get("amount", 0),
        "status": "✅" if dispatch_data.get("count", 0) > 0 else "⚪"
    })
    
    # 3. عمليات التحصيل
    collection_data = frappe.db.sql("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(collected_amount), 0) as amount
        FROM `tabDelivery Collection`
        WHERE docstatus = 1 AND posting_date = %s
    """, (report_date,), as_dict=True)[0]
    
    data.append({
        "metric": "💰 عمليات التحصيل",
        "count": collection_data.get("count", 0),
        "amount": collection_data.get("amount", 0),
        "status": "✅" if collection_data.get("count", 0) > 0 else "⚪"
    })
    
    # 4. الفرق بين الصرف والتحصيل
    diff = flt(dispatch_data.get("amount", 0)) - flt(collection_data.get("amount", 0))
    diff_status = "🟢" if diff <= 0 else ("🟡" if diff < 10000 else "🔴")
    
    data.append({
        "metric": "📊 الفرق (الصرف - التحصيل)",
        "count": 0,
        "amount": diff,
        "status": diff_status
    })
    
    # 5. نسبة التحصيل
    collection_rate = (flt(collection_data.get("amount", 0)) / flt(dispatch_data.get("amount", 0)) * 100) if dispatch_data.get("amount", 0) else 0
    
    data.append({
        "metric": "📈 نسبة التحصيل",
        "count": int(collection_rate),
        "amount": 0,
        "status": "🟢" if collection_rate >= 80 else ("🟡" if collection_rate >= 50 else "🔴")
    })
    
    # 6. طلبات الموافقة المعلقة
    pending_approvals = frappe.db.count("Pharma Approval Request", {
        "workflow_state": "Pending",
        "docstatus": ["<", 2]
    })
    
    data.append({
        "metric": "⏳ طلبات موافقة معلقة",
        "count": pending_approvals,
        "amount": 0,
        "status": "🔴" if pending_approvals > 5 else ("🟡" if pending_approvals > 0 else "🟢")
    })
    
    # 7. العمليات الفاشلة
    failed_processes = frappe.db.count("Pharma Process Log", {
        "status": "Failed",
        "process_date": report_date
    })
    
    data.append({
        "metric": "❌ عمليات فاشلة",
        "count": failed_processes,
        "amount": 0,
        "status": "🔴" if failed_processes > 0 else "🟢"
    })
    
    return data


def get_chart(data):
    # Chart للصرف vs التحصيل
    dispatch_amount = 0
    collection_amount = 0
    
    for row in data:
        if "الصرف" in row.get("metric", "") and "الفرق" not in row.get("metric", ""):
            dispatch_amount = row.get("amount", 0)
        if "التحصيل" in row.get("metric", "") and "نسبة" not in row.get("metric", ""):
            collection_amount = row.get("amount", 0)
    
    return {
        "data": {
            "labels": ["الصرف", "التحصيل"],
            "datasets": [{
                "name": _("المبلغ"),
                "values": [dispatch_amount, collection_amount]
            }]
        },
        "type": "bar",
        "colors": ["#ff5858", "#5e64ff"]
    }


def get_summary(data, filters):
    report_date = filters.get("report_date") or nowdate()
    
    # إجمالي الصرف
    total_dispatch = 0
    total_collection = 0
    total_operations = 0
    
    for row in data:
        if "الصرف" in row.get("metric", "") and "الفرق" not in row.get("metric", ""):
            total_dispatch = row.get("amount", 0)
            total_operations += row.get("count", 0)
        if "التحصيل" in row.get("metric", "") and "نسبة" not in row.get("metric", ""):
            total_collection = row.get("amount", 0)
            total_operations += row.get("count", 0)
    
    return [
        {
            "value": total_dispatch,
            "indicator": "Blue",
            "label": _("إجمالي الصرف"),
            "datatype": "Currency"
        },
        {
            "value": total_collection,
            "indicator": "Green",
            "label": _("إجمالي التحصيل"),
            "datatype": "Currency"
        },
        {
            "value": total_dispatch - total_collection,
            "indicator": "Orange" if total_dispatch > total_collection else "Green",
            "label": _("الفرق"),
            "datatype": "Currency"
        },
        {
            "value": total_operations,
            "indicator": "Blue",
            "label": _("إجمالي العمليات"),
            "datatype": "Int"
        }
    ]
