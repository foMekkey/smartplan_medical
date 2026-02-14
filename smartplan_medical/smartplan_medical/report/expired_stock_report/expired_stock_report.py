# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


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
            "fieldname": "days_expired",
            "label": _("أيام منذ الانتهاء"),
            "fieldtype": "Int",
            "width": 120
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
            "label": _("قيمة الخسارة"),
            "fieldtype": "Currency",
            "width": 130
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
            DATEDIFF(CURDATE(), b.expiry_date) as days_expired,
            SUM(sle.actual_qty) as qty,
            AVG(sle.valuation_rate) as valuation_rate
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabBatch` b ON sle.batch_no = b.name
        INNER JOIN `tabItem` i ON sle.item_code = i.name
        WHERE sle.batch_no IS NOT NULL
            AND b.expiry_date IS NOT NULL
            AND b.expiry_date < CURDATE()
            {conditions}
        GROUP BY sle.item_code, sle.batch_no, sle.warehouse
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY days_expired DESC
    """.format(conditions=conditions), {
        "warehouse": filters.get("warehouse"),
        "item_code": filters.get("item_code"),
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date")
    }, as_dict=True)
    
    for row in data:
        row["total_value"] = (row["qty"] or 0) * (row["valuation_rate"] or 0)
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("warehouse"):
        conditions.append("AND sle.warehouse = %(warehouse)s")
    
    if filters.get("item_code"):
        conditions.append("AND sle.item_code = %(item_code)s")
    
    if filters.get("from_date"):
        conditions.append("AND b.expiry_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND b.expiry_date <= %(to_date)s")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    # تجميع حسب الشهر
    monthly_data = {}
    for row in data:
        if row.get("expiry_date"):
            month_key = row["expiry_date"].strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += row.get("total_value", 0)
    
    sorted_months = sorted(monthly_data.keys())[-12:]  # آخر 12 شهر
    
    return {
        "data": {
            "labels": sorted_months,
            "datasets": [{
                "name": _("قيمة المخزون المنتهي"),
                "values": [monthly_data[m] for m in sorted_months]
            }]
        },
        "type": "bar",
        "colors": ["#ff5858"]
    }


def get_summary(data):
    total_qty = sum(d.get("qty", 0) for d in data)
    total_value = sum(d.get("total_value", 0) for d in data)
    batch_count = len(data)
    
    return [
        {
            "value": batch_count,
            "indicator": "Red",
            "label": _("عدد التشغيلات المنتهية"),
            "datatype": "Int"
        },
        {
            "value": total_qty,
            "indicator": "Red",
            "label": _("إجمالي الكمية"),
            "datatype": "Float"
        },
        {
            "value": total_value,
            "indicator": "Red",
            "label": _("إجمالي الخسارة"),
            "datatype": "Currency"
        }
    ]
