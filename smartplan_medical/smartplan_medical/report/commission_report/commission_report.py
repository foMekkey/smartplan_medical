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
            "fieldname": "employee",
            "label": _("الموظف"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "employee_type",
            "label": _("النوع"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "total_sales",
            "label": _("إجمالي المبيعات"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "total_collections",
            "label": _("إجمالي التحصيلات"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "commission_base",
            "label": _("أساس العمولة"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "commission_rate",
            "label": _("نسبة العمولة %"),
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "fieldname": "earned_commission",
            "label": _("العمولة المستحقة"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "paid_commission",
            "label": _("العمولة المصروفة"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "pending_commission",
            "label": _("العمولة المعلقة"),
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
    
    # عمولات موظفي التلي سيلز
    data = frappe.db.sql("""
        SELECT 
            cc.tele_sales_employee as employee,
            cc.employee_name,
            'تلي سيلز' as employee_type,
            cc.total_net_sales as total_sales,
            0 as total_collections,
            cc.total_net_sales as commission_base,
            cc.commission_rate,
            cc.total_commission as earned_commission,
            0 as paid_commission,
            cc.total_commission as pending_commission,
            cc.status
        FROM `tabCommission Calculation` cc
        WHERE cc.docstatus = 1
            {conditions}
    """.format(conditions=conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "employee": filters.get("employee")
    }, as_dict=True)
    
    # تحديث اسم الموظف
    for row in data:
        if row.get("employee_name"):
            row["employee"] = row.get("employee_name")
    
    return sorted(data, key=lambda x: x.get("pending_commission", 0), reverse=True)


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND cc.from_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND cc.to_date <= %(to_date)s")
    
    if filters.get("employee"):
        conditions.append("AND cc.tele_sales_employee = %(employee)s")
    
    if filters.get("status"):
        conditions.append("AND cc.status = %(status)s")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    # تجميع حسب الموظف
    labels = [d.get("employee", "")[:20] for d in data[:10]]
    earned = [d.get("earned_commission", 0) for d in data[:10]]
    paid = [d.get("paid_commission", 0) for d in data[:10]]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("المستحقة"), "values": earned},
                {"name": _("المصروفة"), "values": paid}
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff", "#5cb85c"]
    }


def get_summary(data):
    total_earned = sum(d.get("earned_commission", 0) for d in data)
    total_paid = sum(d.get("paid_commission", 0) for d in data)
    total_pending = sum(d.get("pending_commission", 0) for d in data)
    
    tele_sales_pending = sum(d.get("pending_commission", 0) for d in data if d.get("employee_type") == "تلي سيلز")
    delivery_pending = sum(d.get("pending_commission", 0) for d in data if d.get("employee_type") == "مندوب توصيل")
    
    return [
        {
            "value": total_earned,
            "indicator": "Blue",
            "label": _("إجمالي العمولات المستحقة"),
            "datatype": "Currency"
        },
        {
            "value": total_paid,
            "indicator": "Green",
            "label": _("إجمالي العمولات المصروفة"),
            "datatype": "Currency"
        },
        {
            "value": total_pending,
            "indicator": "Orange",
            "label": _("إجمالي العمولات المعلقة"),
            "datatype": "Currency"
        },
        {
            "value": tele_sales_pending,
            "indicator": "Orange",
            "label": _("معلق - تلي سيلز"),
            "datatype": "Currency"
        },
        {
            "value": delivery_pending,
            "indicator": "Orange",
            "label": _("معلق - مندوبي التوصيل"),
            "datatype": "Currency"
        }
    ]
