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
            "fieldname": "supplier",
            "label": _("المورد"),
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 150
        },
        {
            "fieldname": "supplier_name",
            "label": _("اسم المورد"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "supplier_group",
            "label": _("المجموعة"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "total_purchases",
            "label": _("إجمالي المشتريات"),
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
    
    # جلب بيانات الموردين من ERPNext Supplier
    data = frappe.db.sql("""
        SELECT * FROM (
            SELECT 
                s.name as supplier,
                s.supplier_name,
                s.supplier_group,
                COALESCE(purchases.total_purchases, 0) as total_purchases,
                COALESCE(payments.total_paid, 0) as total_paid,
                COALESCE(purchases.total_purchases, 0) - COALESCE(payments.total_paid, 0) as outstanding
            FROM `tabSupplier` s
            LEFT JOIN (
                SELECT 
                    supplier,
                    SUM(grand_total) as total_purchases
                FROM `tabPurchase Invoice`
                WHERE docstatus = 1
                    {date_conditions_purchases}
                GROUP BY supplier
            ) purchases ON s.name = purchases.supplier
            LEFT JOIN (
                SELECT 
                    party as supplier,
                    SUM(paid_amount) as total_paid
                FROM `tabPayment Entry`
                WHERE docstatus = 1 
                    AND party_type = 'Supplier'
                    {date_conditions_payments}
                GROUP BY party
            ) payments ON s.name = payments.supplier
            WHERE s.disabled = 0
                {supplier_conditions}
        ) AS supplier_data
        WHERE outstanding > 0 OR total_purchases > 0
        ORDER BY outstanding DESC
    """.format(
        date_conditions_purchases=conditions.get("date_conditions_purchases", ""),
        date_conditions_payments=conditions.get("date_conditions_payments", ""),
        supplier_conditions=conditions.get("supplier_conditions", "")
    ), as_dict=True)
    
    # حساب أعمار الديون
    today = getdate(nowdate())
    
    for row in data:
        aging = get_supplier_aging(row.supplier, today, filters)
        row.update(aging)
        
        # آخر دفعة
        row["last_payment_date"] = frappe.db.get_value(
            "Payment Entry",
            {"party_type": "Supplier", "party": row.supplier, "docstatus": 1},
            "posting_date",
            order_by="posting_date desc"
        )
    
    return data


def get_supplier_aging(supplier, today, filters):
    """حساب أعمار الديون للمورد"""
    # جلب الفواتير غير المسددة من ERPNext Purchase Invoice
    invoices = frappe.db.sql("""
        SELECT 
            posting_date,
            grand_total,
            outstanding_amount
        FROM `tabPurchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (supplier,), as_dict=True)
    
    aging = {"age_0_30": 0, "age_31_60": 0, "age_61_90": 0, "age_90_plus": 0}
    
    for inv in invoices:
        outstanding = flt(inv.outstanding_amount)
        days = date_diff(today, inv.posting_date)
        
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
    date_conditions_purchases = []
    date_conditions_payments = []
    supplier_conditions = []
    
    if filters.get("from_date"):
        date_conditions_purchases.append(f"AND posting_date >= '{filters.get('from_date')}'")
        date_conditions_payments.append(f"AND posting_date >= '{filters.get('from_date')}'")
    
    if filters.get("to_date"):
        date_conditions_purchases.append(f"AND posting_date <= '{filters.get('to_date')}'")
        date_conditions_payments.append(f"AND posting_date <= '{filters.get('to_date')}'")
    
    if filters.get("supplier"):
        supplier_conditions.append(f"AND s.name = '{filters.get('supplier')}'")
    
    if filters.get("supplier_group"):
        supplier_conditions.append(f"AND s.supplier_group = '{filters.get('supplier_group')}'")
    
    return {
        "date_conditions_purchases": " ".join(date_conditions_purchases),
        "date_conditions_payments": " ".join(date_conditions_payments),
        "supplier_conditions": " ".join(supplier_conditions)
    }


def get_chart(data):
    if not data:
        return None
    
    # أكبر 10 موردين بالمستحقات
    top_suppliers = sorted(data, key=lambda x: x.get("outstanding", 0), reverse=True)[:10]
    
    return {
        "data": {
            "labels": [d.get("supplier_name", "")[:15] for d in top_suppliers],
            "datasets": [{
                "name": _("المستحق"),
                "values": [d.get("outstanding", 0) for d in top_suppliers]
            }]
        },
        "type": "bar",
        "colors": ["#5e64ff"]
    }


def get_summary(data):
    total_purchases = sum(d.get("total_purchases", 0) for d in data)
    total_paid = sum(d.get("total_paid", 0) for d in data)
    total_outstanding = sum(d.get("outstanding", 0) for d in data)
    total_overdue = sum(d.get("age_31_60", 0) + d.get("age_61_90", 0) + d.get("age_90_plus", 0) for d in data)
    
    return [
        {
            "value": total_purchases,
            "indicator": "Blue",
            "label": _("إجمالي المشتريات"),
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
