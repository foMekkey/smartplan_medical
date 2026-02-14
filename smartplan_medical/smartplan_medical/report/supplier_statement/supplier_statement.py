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
    if not filters.get("supplier"):
        frappe.throw(_("يجب اختيار المورد"))
    
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
    supplier = filters.get("supplier")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    # رصيد أول المدة
    opening_balance = get_opening_balance(supplier, from_date)
    
    if opening_balance != 0:
        data.append({
            "posting_date": from_date,
            "voucher_type": "",
            "voucher_no": "",
            "description": _("رصيد أول المدة"),
            "debit": abs(opening_balance) if opening_balance < 0 else 0,
            "credit": opening_balance if opening_balance > 0 else 0,
            "balance": opening_balance
        })
    
    running_balance = opening_balance
    
    # جلب حركات المشتريات من ERPNext Purchase Invoice
    purchases = frappe.db.sql("""
        SELECT 
            posting_date,
            'Purchase Invoice' as voucher_type,
            name as voucher_no,
            CONCAT('فاتورة مشتريات - ', COALESCE(bill_no, name)) as description,
            0 as debit,
            grand_total as credit
        FROM `tabPurchase Invoice`
        WHERE supplier = %s AND docstatus = 1
            AND posting_date BETWEEN %s AND %s
    """, (supplier, from_date, to_date), as_dict=True)
    
    # جلب حركات السداد من ERPNext Payment Entry
    payments = frappe.db.sql("""
        SELECT 
            posting_date,
            'Payment Entry' as voucher_type,
            name as voucher_no,
            CONCAT('سداد - ', mode_of_payment, ' - ', COALESCE(remarks, '')) as description,
            paid_amount as debit,
            0 as credit
        FROM `tabPayment Entry`
        WHERE party_type = 'Supplier' AND party = %s AND docstatus = 1
            AND posting_date BETWEEN %s AND %s
    """, (supplier, from_date, to_date), as_dict=True)
    
    # جلب المرتجعات من ERPNext Purchase Invoice (is_return)
    returns = frappe.db.sql("""
        SELECT 
            posting_date,
            'Purchase Invoice' as voucher_type,
            name as voucher_no,
            CONCAT('مرتجع مشتريات - ', COALESCE(remarks, '')) as description,
            ABS(grand_total) as debit,
            0 as credit
        FROM `tabPurchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND is_return = 1
            AND posting_date BETWEEN %s AND %s
    """, (supplier, from_date, to_date), as_dict=True)
    
    # دمج وترتيب الحركات
    all_transactions = purchases + payments + returns
    all_transactions.sort(key=lambda x: (x.get("posting_date"), x.get("voucher_no", "")))
    
    # حساب الأرصدة المتراكمة
    for row in all_transactions:
        debit = flt(row.get("debit", 0))
        credit = flt(row.get("credit", 0))
        running_balance += credit - debit
        
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


def get_opening_balance(supplier, from_date):
    """حساب رصيد أول المدة"""
    # مجموع المشتريات قبل الفترة من ERPNext Purchase Invoice
    total_purchases = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabPurchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND is_return = 0 AND posting_date < %s
    """, (supplier, from_date))[0][0] or 0
    
    # مجموع المدفوعات قبل الفترة من ERPNext Payment Entry
    total_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabPayment Entry`
        WHERE party_type = 'Supplier' AND party = %s AND docstatus = 1 AND posting_date < %s
    """, (supplier, from_date))[0][0] or 0
    
    # مجموع المرتجعات قبل الفترة
    total_returns = frappe.db.sql("""
        SELECT COALESCE(SUM(ABS(grand_total)), 0)
        FROM `tabPurchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND is_return = 1 AND posting_date < %s
    """, (supplier, from_date))[0][0] or 0
    
    return flt(total_purchases) - flt(total_payments) - flt(total_returns)


def get_summary(data):
    if not data:
        return []
    
    total_debit = sum(d.get("debit", 0) for d in data)
    total_credit = sum(d.get("credit", 0) for d in data)
    closing_balance = data[-1].get("balance", 0) if data else 0
    
    return [
        {
            "value": total_credit,
            "indicator": "Blue",
            "label": _("إجمالي المشتريات (دائن)"),
            "datatype": "Currency"
        },
        {
            "value": total_debit,
            "indicator": "Green",
            "label": _("إجمالي المدفوع (مدين)"),
            "datatype": "Currency"
        },
        {
            "value": closing_balance,
            "indicator": "Blue" if closing_balance > 0 else "Green",
            "label": _("الرصيد النهائي (للمورد)"),
            "datatype": "Currency"
        }
    ]
