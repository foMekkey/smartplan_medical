# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(data)
    
    return columns, data, None, None, summary


def validate_filters(filters):
    if not filters.get("customer"):
        frappe.throw(_("يجب اختيار العميل"))
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("يجب تحديد الفترة"))


def get_columns():
    return [
        {
            "fieldname": "posting_date",
            "label": _("التاريخ"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "voucher_type",
            "label": _("نوع المستند"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "voucher_no",
            "label": _("رقم المستند"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 150
        },
        {
            "fieldname": "description",
            "label": _("البيان"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "debit",
            "label": _("مدين"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "credit",
            "label": _("دائن"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "balance",
            "label": _("الرصيد"),
            "fieldtype": "Currency",
            "width": 130
        }
    ]


def get_data(filters):
    data = []
    customer = filters.get("customer")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    # رصيد أول المدة
    opening_balance = get_opening_balance(customer, from_date)
    
    if opening_balance != 0:
        data.append({
            "posting_date": from_date,
            "voucher_type": "",
            "voucher_no": "",
            "description": _("رصيد أول المدة"),
            "debit": opening_balance if opening_balance > 0 else 0,
            "credit": abs(opening_balance) if opening_balance < 0 else 0,
            "balance": opening_balance
        })
    
    running_balance = opening_balance
    
    # جلب حركات المبيعات
    sales = frappe.db.sql("""
        SELECT 
            order_date as posting_date,
            'Tele Sales Order' as voucher_type,
            name as voucher_no,
            CONCAT('فاتورة مبيعات - ', COALESCE(notes, '')) as description,
            net_amount as debit,
            0 as credit
        FROM `tabTele Sales Order`
        WHERE customer = %s AND docstatus = 1
            AND order_date BETWEEN %s AND %s
    """, (customer, from_date, to_date), as_dict=True)
    
    # جلب حركات التحصيل
    payments = frappe.db.sql("""
        SELECT 
            posting_date,
            'Customer Payment' as voucher_type,
            name as voucher_no,
            CONCAT('سداد - ', payment_mode, ' - ', COALESCE(remarks, '')) as description,
            0 as debit,
            paid_amount as credit
        FROM `tabCustomer Payment`
        WHERE customer = %s AND docstatus = 1
            AND posting_date BETWEEN %s AND %s
    """, (customer, from_date, to_date), as_dict=True)
    
    # جلب المرتجعات
    returns = frappe.db.sql("""
        SELECT 
            return_date as posting_date,
            'Sales Return' as voucher_type,
            name as voucher_no,
            CONCAT('مرتجع - ', COALESCE(return_reason, '')) as description,
            0 as debit,
            return_value as credit
        FROM `tabSales Return`
        WHERE customer = %s AND docstatus = 1
            AND return_date BETWEEN %s AND %s
    """, (customer, from_date, to_date), as_dict=True)
    
    # دمج وترتيب الحركات
    all_transactions = sales + payments + returns
    all_transactions.sort(key=lambda x: (x.get("posting_date"), x.get("voucher_no", "")))
    
    # حساب الأرصدة المتراكمة
    for row in all_transactions:
        debit = flt(row.get("debit", 0))
        credit = flt(row.get("credit", 0))
        running_balance += debit - credit
        
        data.append({
            "posting_date": row.get("posting_date"),
            "voucher_type": row.get("voucher_type"),
            "voucher_no": row.get("voucher_no"),
            "description": row.get("description"),
            "debit": debit,
            "credit": credit,
            "balance": running_balance
        })
    
    # رصيد آخر المدة
    if data:
        data.append({
            "posting_date": to_date,
            "voucher_type": "",
            "voucher_no": "",
            "description": _("رصيد آخر المدة"),
            "debit": 0,
            "credit": 0,
            "balance": running_balance
        })
    
    return data


def get_opening_balance(customer, from_date):
    """حساب رصيد أول المدة"""
    # مجموع المبيعات قبل الفترة
    total_sales = frappe.db.sql("""
        SELECT COALESCE(SUM(net_amount), 0)
        FROM `tabTele Sales Order`
        WHERE customer = %s AND docstatus = 1 AND order_date < %s
    """, (customer, from_date))[0][0] or 0
    
    # مجموع المدفوعات قبل الفترة
    total_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabCustomer Payment`
        WHERE customer = %s AND docstatus = 1 AND posting_date < %s
    """, (customer, from_date))[0][0] or 0
    
    # مجموع المرتجعات قبل الفترة
    total_returns = frappe.db.sql("""
        SELECT COALESCE(SUM(return_value), 0)
        FROM `tabSales Return`
        WHERE customer = %s AND docstatus = 1 AND return_date < %s
    """, (customer, from_date))[0][0] or 0
    
    return flt(total_sales) - flt(total_payments) - flt(total_returns)


def get_summary(data):
    if not data:
        return []
    
    total_debit = sum(d.get("debit", 0) for d in data)
    total_credit = sum(d.get("credit", 0) for d in data)
    closing_balance = data[-1].get("balance", 0) if data else 0
    
    return [
        {
            "value": total_debit,
            "indicator": "Blue",
            "label": _("إجمالي المدين"),
            "datatype": "Currency"
        },
        {
            "value": total_credit,
            "indicator": "Green",
            "label": _("إجمالي الدائن"),
            "datatype": "Currency"
        },
        {
            "value": closing_balance,
            "indicator": "Red" if closing_balance > 0 else "Green",
            "label": _("الرصيد النهائي"),
            "datatype": "Currency"
        }
    ]
