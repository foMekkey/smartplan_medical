# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


def execute(filters=None):
    validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("يجب تحديد الفترة"))


def get_columns():
    return [
        {
            "fieldname": "cashbox",
            "label": _("الصندوق"),
            "fieldtype": "Link",
            "options": "Cashbox",
            "width": 150
        },
        {
            "fieldname": "cashbox_name",
            "label": _("اسم الصندوق"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "cashbox_type",
            "label": _("نوع الصندوق"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "custodian",
            "label": _("أمين الصندوق"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "opening_balance",
            "label": _("الرصيد الافتتاحي"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_receipts",
            "label": _("إجمالي الوارد"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_payments",
            "label": _("إجمالي الصادر"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "calculated_balance",
            "label": _("الرصيد المحسوب"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "current_balance",
            "label": _("الرصيد الفعلي"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "variance",
            "label": _("الفرق"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "status",
            "label": _("الحالة"),
            "fieldtype": "Data",
            "width": 80
        }
    ]


def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    conditions = ""
    if filters.get("cashbox"):
        conditions += f" AND cb.name = '{filters.get('cashbox')}'"
    if filters.get("cashbox_type"):
        conditions += f" AND cb.cashbox_type = '{filters.get('cashbox_type')}'"
    
    # جلب بيانات الصناديق
    cashboxes = frappe.db.sql("""
        SELECT 
            cb.name as cashbox,
            cb.cashbox_name,
            cb.cashbox_type,
            cb.custodian,
            cb.custodian_name,
            cb.opening_balance,
            cb.current_balance,
            cb.is_active
        FROM `tabCashbox` cb
        WHERE cb.is_active = 1 {conditions}
        ORDER BY cb.cashbox_type, cb.cashbox_name
    """.format(conditions=conditions), as_dict=True)
    
    data = []
    for cb in cashboxes:
        # حساب الواردات
        total_receipts = get_total_receipts(cb.cashbox, from_date, to_date)
        
        # حساب المصروفات
        total_payments = get_total_payments(cb.cashbox, from_date, to_date)
        
        # الرصيد المحسوب
        calculated_balance = flt(cb.opening_balance) + flt(total_receipts) - flt(total_payments)
        
        # الفرق
        variance = flt(cb.current_balance) - calculated_balance
        
        data.append({
            "cashbox": cb.cashbox,
            "cashbox_name": cb.cashbox_name,
            "cashbox_type": cb.cashbox_type,
            "custodian": cb.custodian_name or cb.custodian,
            "opening_balance": cb.opening_balance,
            "total_receipts": total_receipts,
            "total_payments": total_payments,
            "calculated_balance": calculated_balance,
            "current_balance": cb.current_balance,
            "variance": variance,
            "status": "متوازن" if abs(variance) < 0.01 else "يوجد فرق"
        })
    
    return data


def get_total_receipts(cashbox, from_date, to_date):
    """حساب إجمالي الواردات"""
    # حركات القبض
    cash_receipts = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabCash Transaction`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'قبض'
            AND posting_date BETWEEN %s AND %s
    """, (cashbox, from_date, to_date))[0][0] or 0
    
    # سحب من البنك
    bank_withdrawals = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabBank Transaction Entry`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'سحب نقدي'
            AND posting_date BETWEEN %s AND %s
    """, (cashbox, from_date, to_date))[0][0] or 0
    
    # تحصيلات العملاء نقداً
    customer_receipts = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabCustomer Payment`
        WHERE cashbox = %s AND docstatus = 1 AND payment_mode = 'نقدي'
            AND posting_date BETWEEN %s AND %s
    """, (cashbox, from_date, to_date))[0][0] or 0
    
    return flt(cash_receipts) + flt(bank_withdrawals) + flt(customer_receipts)


def get_total_payments(cashbox, from_date, to_date):
    """حساب إجمالي المصروفات"""
    # حركات الصرف
    cash_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabCash Transaction`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'صرف'
            AND posting_date BETWEEN %s AND %s
    """, (cashbox, from_date, to_date))[0][0] or 0
    
    # إيداع بالبنك
    bank_deposits = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabBank Transaction Entry`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'إيداع نقدي'
            AND posting_date BETWEEN %s AND %s
    """, (cashbox, from_date, to_date))[0][0] or 0
    
    # مدفوعات الموردين نقداً
    supplier_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabSupplier Payment`
        WHERE cashbox = %s AND docstatus = 1 AND payment_mode = 'نقدي'
            AND posting_date BETWEEN %s AND %s
    """, (cashbox, from_date, to_date))[0][0] or 0
    
    return flt(cash_payments) + flt(bank_deposits) + flt(supplier_payments)


def get_chart(data):
    if not data:
        return None
    
    return {
        "data": {
            "labels": [d.get("cashbox_name", "")[:15] for d in data],
            "datasets": [
                {"name": _("الوارد"), "values": [d.get("total_receipts", 0) for d in data]},
                {"name": _("الصادر"), "values": [d.get("total_payments", 0) for d in data]}
            ]
        },
        "type": "bar",
        "colors": ["#28a745", "#dc3545"]
    }


def get_summary(data):
    if not data:
        return []
    
    total_receipts = sum(d.get("total_receipts", 0) for d in data)
    total_payments = sum(d.get("total_payments", 0) for d in data)
    total_balance = sum(d.get("current_balance", 0) for d in data)
    total_variance = sum(d.get("variance", 0) for d in data)
    
    return [
        {
            "value": total_receipts,
            "indicator": "Green",
            "label": _("إجمالي الوارد"),
            "datatype": "Currency"
        },
        {
            "value": total_payments,
            "indicator": "Red",
            "label": _("إجمالي الصادر"),
            "datatype": "Currency"
        },
        {
            "value": total_balance,
            "indicator": "Blue",
            "label": _("إجمالي الأرصدة"),
            "datatype": "Currency"
        },
        {
            "value": abs(total_variance),
            "indicator": "Orange" if abs(total_variance) > 0.01 else "Green",
            "label": _("إجمالي الفروقات"),
            "datatype": "Currency"
        }
    ]
