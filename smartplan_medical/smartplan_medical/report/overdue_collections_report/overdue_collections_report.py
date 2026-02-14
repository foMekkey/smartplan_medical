# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, date_diff, nowdate, getdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "dispatch",
            "label": _("إذن الصرف"),
            "fieldtype": "Link",
            "options": "Warehouse Dispatch",
            "width": 140
        },
        {
            "fieldname": "dispatch_date",
            "label": _("تاريخ الصرف"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "customer",
            "label": _("العميل"),
            "fieldtype": "Link",
            "options": "Pharma Customer",
            "width": 150
        },
        {
            "fieldname": "customer_name",
            "label": _("اسم العميل"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "delivery_rep",
            "label": _("مندوب التوصيل"),
            "fieldtype": "Link",
            "options": "Delivery Representative",
            "width": 130
        },
        {
            "fieldname": "dispatch_amount",
            "label": _("قيمة الصرف"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "collected_amount",
            "label": _("المبلغ المحصل"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "pending_amount",
            "label": _("المبلغ المعلق"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "days_overdue",
            "label": _("أيام التأخير"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "aging_bucket",
            "label": _("فئة التأخير"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "last_collection_date",
            "label": _("آخر تحصيل"),
            "fieldtype": "Date",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            wd.name as dispatch,
            wd.posting_date as dispatch_date,
            wd.customer,
            pc.legal_name as customer_name,
            wd.delivery_representative as delivery_rep,
            wd.total_amount as dispatch_amount,
            COALESCE((
                SELECT SUM(dc.collected_amount)
                FROM `tabDelivery Collection` dc
                WHERE dc.warehouse_dispatch = wd.name
                AND dc.docstatus = 1
            ), 0) as collected_amount,
            (
                SELECT MAX(dc.posting_date)
                FROM `tabDelivery Collection` dc
                WHERE dc.warehouse_dispatch = wd.name
                AND dc.docstatus = 1
            ) as last_collection_date
        FROM `tabWarehouse Dispatch` wd
        LEFT JOIN `tabPharma Customer` pc ON wd.customer = pc.name
        WHERE wd.docstatus = 1
            {conditions}
        HAVING (dispatch_amount - collected_amount) > 0
        ORDER BY dispatch_date ASC
    """.format(conditions=conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "customer": filters.get("customer"),
        "delivery_rep": filters.get("delivery_rep"),
        "min_days_overdue": filters.get("min_days_overdue", 0)
    }, as_dict=True)
    
    today = getdate(nowdate())
    
    for row in data:
        row["pending_amount"] = flt(row["dispatch_amount"]) - flt(row["collected_amount"])
        row["days_overdue"] = date_diff(today, row["dispatch_date"])
        
        # تصنيف فئة التأخير
        if row["days_overdue"] <= 30:
            row["aging_bucket"] = "0-30 يوم"
        elif row["days_overdue"] <= 60:
            row["aging_bucket"] = "31-60 يوم"
        elif row["days_overdue"] <= 90:
            row["aging_bucket"] = "61-90 يوم"
        else:
            row["aging_bucket"] = ">90 يوم"
    
    # تصفية حسب أيام التأخير
    if filters.get("min_days_overdue"):
        data = [d for d in data if d["days_overdue"] >= filters.get("min_days_overdue")]
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND wd.posting_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND wd.posting_date <= %(to_date)s")
    
    if filters.get("customer"):
        conditions.append("AND wd.customer = %(customer)s")
    
    if filters.get("delivery_rep"):
        conditions.append("AND wd.delivery_representative = %(delivery_rep)s")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    # تجميع حسب فئة التأخير
    buckets = {"0-30 يوم": 0, "31-60 يوم": 0, "61-90 يوم": 0, ">90 يوم": 0}
    for row in data:
        bucket = row.get("aging_bucket", "0-30 يوم")
        buckets[bucket] += flt(row.get("pending_amount", 0))
    
    return {
        "data": {
            "labels": list(buckets.keys()),
            "datasets": [{
                "name": _("المبلغ المعلق"),
                "values": list(buckets.values())
            }]
        },
        "type": "pie",
        "colors": ["#7cd6fd", "#ffb65c", "#ff5858", "#990000"]
    }


def get_summary(data):
    total_pending = sum(d.get("pending_amount", 0) for d in data)
    avg_days = sum(d.get("days_overdue", 0) for d in data) / len(data) if data else 0
    critical = sum(1 for d in data if d.get("days_overdue", 0) > 90)
    
    return [
        {
            "value": len(data),
            "indicator": "Orange",
            "label": _("عدد التحصيلات المتأخرة"),
            "datatype": "Int"
        },
        {
            "value": total_pending,
            "indicator": "Red",
            "label": _("إجمالي المبلغ المعلق"),
            "datatype": "Currency"
        },
        {
            "value": int(avg_days),
            "indicator": "Orange",
            "label": _("متوسط أيام التأخير"),
            "datatype": "Int"
        },
        {
            "value": critical,
            "indicator": "Red",
            "label": _("تحصيلات حرجة (>90 يوم)"),
            "datatype": "Int"
        }
    ]
