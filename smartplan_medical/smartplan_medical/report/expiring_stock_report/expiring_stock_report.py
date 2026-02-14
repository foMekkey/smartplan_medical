# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    
    return columns, data, None, chart


def get_columns():
    return [
        {
            "fieldname": "item_code",
            "label": _("كود الصنف"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "fieldname": "item_name",
            "label": _("اسم الصنف"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "batch_no",
            "label": _("رقم التشغيلة"),
            "fieldtype": "Link",
            "options": "Batch",
            "width": 120
        },
        {
            "fieldname": "warehouse",
            "label": _("المخزن"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150
        },
        {
            "fieldname": "expiry_date",
            "label": _("تاريخ الانتهاء"),
            "fieldtype": "Date",
            "width": 110
        },
        {
            "fieldname": "days_to_expiry",
            "label": _("أيام للانتهاء"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "qty",
            "label": _("الكمية"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "valuation_rate",
            "label": _("سعر التكلفة"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_value",
            "label": _("القيمة الإجمالية"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "status",
            "label": _("الحالة"),
            "fieldtype": "Data",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            sle.item_code,
            i.item_name,
            sle.batch_no,
            sle.warehouse,
            b.expiry_date,
            DATEDIFF(b.expiry_date, CURDATE()) as days_to_expiry,
            SUM(sle.actual_qty) as qty,
            AVG(sle.valuation_rate) as valuation_rate
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabBatch` b ON sle.batch_no = b.name
        INNER JOIN `tabItem` i ON sle.item_code = i.name
        WHERE sle.batch_no IS NOT NULL
            AND b.expiry_date IS NOT NULL
            AND b.expiry_date > CURDATE()
            AND DATEDIFF(b.expiry_date, CURDATE()) <= %(warning_days)s
            {conditions}
        GROUP BY sle.item_code, sle.batch_no, sle.warehouse
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY days_to_expiry ASC
    """.format(conditions=conditions), {
        "warning_days": filters.get("warning_days", 90),
        "warehouse": filters.get("warehouse"),
        "item_code": filters.get("item_code")
    }, as_dict=True)
    
    for row in data:
        row["total_value"] = (row["qty"] or 0) * (row["valuation_rate"] or 0)
        
        if row["days_to_expiry"] <= 30:
            row["status"] = "خطر"
        elif row["days_to_expiry"] <= 60:
            row["status"] = "تحذير"
        else:
            row["status"] = "قريب"
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("warehouse"):
        conditions.append("AND sle.warehouse = %(warehouse)s")
    
    if filters.get("item_code"):
        conditions.append("AND sle.item_code = %(item_code)s")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    danger = sum(1 for d in data if d.get("days_to_expiry", 0) <= 30)
    warning = sum(1 for d in data if 30 < d.get("days_to_expiry", 0) <= 60)
    near = sum(1 for d in data if d.get("days_to_expiry", 0) > 60)
    
    return {
        "data": {
            "labels": ["خطر (≤30 يوم)", "تحذير (31-60 يوم)", "قريب (>60 يوم)"],
            "datasets": [{
                "name": _("عدد التشغيلات"),
                "values": [danger, warning, near]
            }]
        },
        "type": "donut",
        "colors": ["#ff5858", "#ffb65c", "#7cd6fd"]
    }
