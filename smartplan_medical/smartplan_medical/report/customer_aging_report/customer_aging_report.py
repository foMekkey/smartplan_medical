# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate, date_diff


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
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
            "width": 180
        },
        {
            "fieldname": "customer_category",
            "label": _("الفئة"),
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
            "fieldname": "total_paid",
            "label": _("إجمالي المدفوع"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "outstanding",
            "label": _("المستحق"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "age_0_30",
            "label": _("0-30 يوم"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "age_31_60",
            "label": _("31-60 يوم"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "age_61_90",
            "label": _("61-90 يوم"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "age_90_plus",
            "label": _(">90 يوم"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "last_payment_date",
            "label": _("آخر دفعة"),
            "fieldtype": "Date",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    # جلب بيانات العملاء
    data = frappe.db.sql("""
        SELECT * FROM (
            SELECT 
                pc.name as customer,
                pc.legal_name as customer_name,
                pc.customer_category,
                COALESCE(sales.total_sales, 0) as total_sales,
                COALESCE(payments.total_paid, 0) as total_paid,
                COALESCE(sales.total_sales, 0) - COALESCE(payments.total_paid, 0) as outstanding
            FROM `tabPharma Customer` pc
            LEFT JOIN (
                SELECT 
                    customer,
                    SUM(net_amount) as total_sales
                FROM `tabTele Sales Order`
                WHERE docstatus = 1
                    {date_conditions_sales}
                GROUP BY customer
            ) sales ON pc.name = sales.customer
            LEFT JOIN (
                SELECT 
                    customer,
                    SUM(paid_amount) as total_paid
                FROM `tabCustomer Payment`
                WHERE docstatus = 1
                    {date_conditions_payments}
                GROUP BY customer
            ) payments ON pc.name = payments.customer
            WHERE pc.is_active = 1
                {customer_conditions}
        ) AS customer_data
        WHERE outstanding > 0 OR total_sales > 0
        ORDER BY outstanding DESC
    """.format(
        date_conditions_sales=conditions.get("date_conditions_sales", ""),
        date_conditions_payments=conditions.get("date_conditions_payments", ""),
        customer_conditions=conditions.get("customer_conditions", "")
    ), as_dict=True)
    
    # حساب أعمار الديون
    today = getdate(nowdate())
    
    for row in data:
        aging = get_customer_aging(row.customer, today, filters)
        row.update(aging)
        
        # آخر دفعة
        row["last_payment_date"] = frappe.db.get_value(
            "Customer Payment",
            {"customer": row.customer, "docstatus": 1},
            "posting_date",
            order_by="posting_date desc"
        )
    
    return data


def get_customer_aging(customer, today, filters):
    """حساب أعمار الديون للعميل"""
    # جلب الفواتير غير المسددة
    invoices = frappe.db.sql("""
        SELECT 
            order_date,
            net_amount,
            COALESCE(
                (SELECT SUM(cp.paid_amount) 
                 FROM `tabCustomer Payment` cp 
                 INNER JOIN `tabCustomer Payment Reference` cpr ON cp.name = cpr.parent
                 WHERE cpr.reference_name = tso.name AND cp.docstatus = 1), 
                0
            ) as paid
        FROM `tabTele Sales Order` tso
        WHERE customer = %s AND docstatus = 1
        HAVING (net_amount - paid) > 0
    """, (customer,), as_dict=True)
    
    aging = {"age_0_30": 0, "age_31_60": 0, "age_61_90": 0, "age_90_plus": 0}
    
    for inv in invoices:
        outstanding = flt(inv.net_amount) - flt(inv.paid)
        days = date_diff(today, inv.order_date)
        
        if days <= 30:
            aging["age_0_30"] += outstanding
        elif days <= 60:
            aging["age_31_60"] += outstanding
        elif days <= 90:
            aging["age_61_90"] += outstanding
        else:
            aging["age_90_plus"] += outstanding
    
    return aging


def get_conditions(filters):
    date_conditions_sales = []
    date_conditions_payments = []
    customer_conditions = []
    
    if filters.get("from_date"):
        date_conditions_sales.append(f"AND order_date >= '{filters.get('from_date')}'")
        date_conditions_payments.append(f"AND posting_date >= '{filters.get('from_date')}'")
    
    if filters.get("to_date"):
        date_conditions_sales.append(f"AND order_date <= '{filters.get('to_date')}'")
        date_conditions_payments.append(f"AND posting_date <= '{filters.get('to_date')}'")
    
    if filters.get("customer"):
        customer_conditions.append(f"AND pc.name = '{filters.get('customer')}'")
    
    if filters.get("customer_category"):
        customer_conditions.append(f"AND pc.customer_category = '{filters.get('customer_category')}'")
    
    return {
        "date_conditions_sales": " ".join(date_conditions_sales),
        "date_conditions_payments": " ".join(date_conditions_payments),
        "customer_conditions": " ".join(customer_conditions)
    }


def get_chart(data):
    if not data:
        return None
    
    # أكبر 10 عملاء بالمستحقات
    top_customers = sorted(data, key=lambda x: x.get("outstanding", 0), reverse=True)[:10]
    
    return {
        "data": {
            "labels": [d.get("customer_name", "")[:15] for d in top_customers],
            "datasets": [{
                "name": _("المستحق"),
                "values": [d.get("outstanding", 0) for d in top_customers]
            }]
        },
        "type": "bar",
        "colors": ["#ff5858"]
    }


def get_summary(data):
    total_sales = sum(d.get("total_sales", 0) for d in data)
    total_paid = sum(d.get("total_paid", 0) for d in data)
    total_outstanding = sum(d.get("outstanding", 0) for d in data)
    total_overdue = sum(d.get("age_31_60", 0) + d.get("age_61_90", 0) + d.get("age_90_plus", 0) for d in data)
    
    return [
        {
            "value": total_sales,
            "indicator": "Blue",
            "label": _("إجمالي المبيعات"),
            "datatype": "Currency"
        },
        {
            "value": total_paid,
            "indicator": "Green",
            "label": _("إجمالي المدفوع"),
            "datatype": "Currency"
        },
        {
            "value": total_outstanding,
            "indicator": "Orange",
            "label": _("إجمالي المستحق"),
            "datatype": "Currency"
        },
        {
            "value": total_overdue,
            "indicator": "Red",
            "label": _("المتأخر (>30 يوم)"),
            "datatype": "Currency"
        }
    ]
