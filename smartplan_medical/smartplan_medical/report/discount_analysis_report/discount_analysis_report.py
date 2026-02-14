# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "sales_order",
            "label": _("طلب المبيعات"),
            "fieldtype": "Link",
            "options": "Tele Sales Order",
            "width": 140
        },
        {
            "fieldname": "transaction_date",
            "label": _("التاريخ"),
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
            "fieldname": "sales_person",
            "label": _("موظف المبيعات"),
            "fieldtype": "Link",
            "options": "Tele Sales Team",
            "width": 130
        },
        {
            "fieldname": "gross_amount",
            "label": _("المبلغ قبل الخصم"),
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
            "fieldname": "discount_amount",
            "label": _("مبلغ الخصم"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "net_amount",
            "label": _("المبلغ بعد الخصم"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "discount_reason",
            "label": _("سبب الخصم"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "approved",
            "label": _("معتمد"),
            "fieldtype": "Check",
            "width": 80
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            tso.name as sales_order,
            tso.order_date as transaction_date,
            tso.customer,
            tso.tele_sales_employee as sales_person,
            tso.total_amount as gross_amount,
            COALESCE(tso.total_discount_percent, 0) as discount_percent,
            COALESCE(tso.discount_amount, 0) as discount_amount,
            tso.net_amount,
            tso.approval_reason as discount_reason,
            CASE WHEN tso.approved_by IS NOT NULL THEN 1 ELSE 0 END as approved
        FROM `tabTele Sales Order` tso
        WHERE tso.docstatus = 1
            AND COALESCE(tso.discount_amount, 0) > 0
            {conditions}
        ORDER BY tso.discount_amount DESC
    """.format(conditions=conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "sales_person": filters.get("sales_person"),
        "min_discount_percent": filters.get("min_discount_percent", 0)
    }, as_dict=True)
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND tso.order_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND tso.order_date <= %(to_date)s")
    
    if filters.get("sales_person"):
        conditions.append("AND tso.tele_sales_employee = %(sales_person)s")
    
    if filters.get("min_discount_percent"):
        conditions.append("AND COALESCE(tso.total_discount_percent, 0) >= %(min_discount_percent)s")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    # تجميع الخصومات حسب الموظف
    by_employee = {}
    for row in data:
        emp = row.get("sales_person", "غير محدد")
        if emp not in by_employee:
            by_employee[emp] = 0
        by_employee[emp] += flt(row.get("discount_amount", 0))
    
    sorted_emp = sorted(by_employee.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "data": {
            "labels": [e[0] for e in sorted_emp],
            "datasets": [{
                "name": _("مبلغ الخصم"),
                "values": [e[1] for e in sorted_emp]
            }]
        },
        "type": "bar",
        "colors": ["#ff5858"]
    }


def get_summary(data):
    total_gross = sum(d.get("gross_amount", 0) for d in data)
    total_discount = sum(d.get("discount_amount", 0) for d in data)
    total_net = sum(d.get("net_amount", 0) for d in data)
    avg_discount_percent = (total_discount / total_gross * 100) if total_gross else 0
    
    return [
        {
            "value": len(data),
            "indicator": "Blue",
            "label": _("عدد الطلبات بخصم"),
            "datatype": "Int"
        },
        {
            "value": total_gross,
            "indicator": "Blue",
            "label": _("إجمالي قبل الخصم"),
            "datatype": "Currency"
        },
        {
            "value": total_discount,
            "indicator": "Red",
            "label": _("إجمالي الخصومات"),
            "datatype": "Currency"
        },
        {
            "value": avg_discount_percent,
            "indicator": "Orange",
            "label": _("متوسط نسبة الخصم"),
            "datatype": "Percent"
        }
    ]
