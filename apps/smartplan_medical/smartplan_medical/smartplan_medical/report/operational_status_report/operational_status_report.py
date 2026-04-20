# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "status",
            "label": _("الحالة"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "count",
            "label": _("العدد"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "total_amount",
            "label": _("إجمالي المبلغ"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "percentage",
            "label": _("النسبة %"),
            "fieldtype": "Percent",
            "width": 100
        }
    ]


def get_data(filters):
    # الحالات المختلفة لطلبات التلي سيلز
    statuses = [
        ("Draft", "مسودة", "🔵"),
        ("Pending Approval", "في انتظار الموافقة", "🟡"),
        ("Approved", "معتمد", "🟢"),
        ("Dispatched", "تم الصرف", "🟣"),
        ("Cancelled", "ملغي", "🔴")
    ]
    
    conditions = get_conditions(filters)
    
    # الحصول على إجمالي عدد الطلبات
    total_count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabTele Sales Order`
        WHERE 1=1 {conditions}
    """.format(conditions=conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date")
    })[0][0] or 1
    
    data = []
    
    for status_value, status_label, icon in statuses:
        result = frappe.db.sql("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(net_amount), 0) as total_amount
            FROM `tabTele Sales Order`
            WHERE status = %(status)s {conditions}
        """.format(conditions=conditions), {
            "status": status_value,
            "from_date": filters.get("from_date"),
            "to_date": filters.get("to_date")
        }, as_dict=True)[0]
        
        data.append({
            "status": f"{icon} {status_label}",
            "count": result.get("count", 0),
            "total_amount": result.get("total_amount", 0),
            "percentage": (result.get("count", 0) / total_count * 100) if total_count else 0
        })
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND order_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND order_date <= %(to_date)s")
    
    return " ".join(conditions)


def get_chart(data):
    labels = [d["status"] for d in data]
    values = [d["count"] for d in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [{
                "name": _("عدد الطلبات"),
                "values": values
            }]
        },
        "type": "pie",
        "colors": ["#5e64ff", "#ffb65c", "#28a745", "#9c27b0", "#ff5858"]
    }


def get_summary(data):
    total_count = sum(d.get("count", 0) for d in data)
    total_amount = sum(d.get("total_amount", 0) for d in data)
    
    # عدد المعتمدة
    approved = next((d for d in data if "معتمد" in d.get("status", "")), {})
    
    return [
        {
            "value": total_count,
            "indicator": "Blue",
            "label": _("إجمالي الطلبات"),
            "datatype": "Int"
        },
        {
            "value": total_amount,
            "indicator": "Green",
            "label": _("إجمالي المبالغ"),
            "datatype": "Currency"
        },
        {
            "value": approved.get("count", 0),
            "indicator": "Green",
            "label": _("طلبات معتمدة"),
            "datatype": "Int"
        }
    ]
