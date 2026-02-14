# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, nowdate, flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "employee",
            "label": _("موظف المبيعات"),
            "fieldtype": "Link",
            "options": "Tele Sales Team",
            "width": 150
        },
        {
            "fieldname": "employee_name",
            "label": _("اسم الموظف"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "total_orders",
            "label": _("عدد الطلبات"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "total_items",
            "label": _("عدد الأصناف"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "gross_amount",
            "label": _("المبيعات الإجمالية"),
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "fieldname": "total_discount",
            "label": _("إجمالي الخصومات"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "discount_percent",
            "label": _("نسبة الخصم %"),
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "fieldname": "net_amount",
            "label": _("صافي المبيعات"),
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "fieldname": "collected_amount",
            "label": _("المبلغ المحصل"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "collection_rate",
            "label": _("نسبة التحصيل %"),
            "fieldtype": "Percent",
            "width": 110
        },
        {
            "fieldname": "avg_order_value",
            "label": _("متوسط قيمة الطلب"),
            "fieldtype": "Currency",
            "width": 130
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            tso.tele_sales_employee as employee,
            tst.employee_name as employee_name,
            COUNT(DISTINCT tso.name) as total_orders,
            COUNT(tsoi.name) as total_items,
            SUM(tso.total_amount) as gross_amount,
            SUM(COALESCE(tso.discount_amount, 0)) as total_discount,
            SUM(tso.net_amount) as net_amount
        FROM `tabTele Sales Order` tso
        LEFT JOIN `tabTele Sales Team` tst ON tso.tele_sales_employee = tst.name
        LEFT JOIN `tabTele Sales Order Item` tsoi ON tsoi.parent = tso.name
        WHERE tso.docstatus = 1
            {conditions}
        GROUP BY tso.tele_sales_employee
        ORDER BY net_amount DESC
    """.format(conditions=conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "sales_person": filters.get("sales_person")
    }, as_dict=True)
    
    # حساب التحصيلات لكل موظف
    for row in data:
        collected = frappe.db.sql("""
            SELECT COALESCE(SUM(dc.collected_amount), 0) as collected
            FROM `tabDelivery Collection` dc
            INNER JOIN `tabTele Sales Order` tso ON dc.sales_order = tso.name
            WHERE dc.docstatus = 1 
                AND tso.tele_sales_employee = %s
                AND dc.collection_date BETWEEN %s AND %s
        """, (row.employee, filters.get("from_date"), filters.get("to_date")))
        
        row["collected_amount"] = flt(collected[0][0]) if collected else 0
        
        # حسابات إضافية
        row["discount_percent"] = (flt(row["total_discount"]) / flt(row["gross_amount"]) * 100) if row["gross_amount"] else 0
        row["collection_rate"] = (flt(row["collected_amount"]) / flt(row["net_amount"]) * 100) if row["net_amount"] else 0
        row["avg_order_value"] = flt(row["net_amount"]) / flt(row["total_orders"]) if row["total_orders"] else 0
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND tso.order_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND tso.order_date <= %(to_date)s")
    
    if filters.get("sales_person"):
        conditions.append("AND tso.tele_sales_employee = %(sales_person)s")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    labels = [d.get("employee_name", d.get("employee", "")) for d in data[:10]]
    net_values = [d.get("net_amount", 0) for d in data[:10]]
    collected_values = [d.get("collected_amount", 0) for d in data[:10]]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("صافي المبيعات"), "values": net_values},
                {"name": _("المحصل"), "values": collected_values}
            ]
        },
        "type": "bar",
        "colors": ["#7cd6fd", "#5e64ff"]
    }


def get_summary(data):
    total_orders = sum(d.get("total_orders", 0) for d in data)
    total_net = sum(d.get("net_amount", 0) for d in data)
    total_collected = sum(d.get("collected_amount", 0) for d in data)
    total_discount = sum(d.get("total_discount", 0) for d in data)
    
    return [
        {
            "value": len(data),
            "indicator": "Blue",
            "label": _("عدد الموظفين"),
            "datatype": "Int"
        },
        {
            "value": total_orders,
            "indicator": "Blue",
            "label": _("إجمالي الطلبات"),
            "datatype": "Int"
        },
        {
            "value": total_net,
            "indicator": "Green",
            "label": _("صافي المبيعات"),
            "datatype": "Currency"
        },
        {
            "value": total_collected,
            "indicator": "Green",
            "label": _("إجمالي التحصيل"),
            "datatype": "Currency"
        },
        {
            "value": total_discount,
            "indicator": "Orange",
            "label": _("إجمالي الخصومات"),
            "datatype": "Currency"
        }
    ]
