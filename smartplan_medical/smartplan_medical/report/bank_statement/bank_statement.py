# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def validate_filters(filters):
    if not filters.get("bank_account"):
        frappe.throw(_("يجب اختيار الحساب البنكي"))
    
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
            "width": 140
        },
        {
            "fieldname": "voucher_no",
            "label": _("رقم المستند"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 150
        },
        {
            "fieldname": "reference_no",
            "label": _("رقم المرجع"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "description",
            "label": _("البيان"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "debit",
            "label": _("إيداع"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "credit",
            "label": _("سحب"),
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
    bank_account = filters.get("bank_account")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    # رصيد أول المدة
    opening_balance = get_opening_balance(bank_account, from_date)
    
    data.append({
        "posting_date": from_date,
        "voucher_type": "",
        "voucher_no": "",
        "reference_no": "",
        "description": _("رصيد أول المدة"),
        "debit": opening_balance if opening_balance > 0 else 0,
        "credit": 0,
        "balance": opening_balance
    })
    
    running_balance = opening_balance
    
    # جلب حركات البنك
    transactions = frappe.db.sql("""
        SELECT 
            posting_date,
            'Bank Transaction Entry' as voucher_type,
            name as voucher_no,
            reference_no,
            CONCAT(transaction_type, ' - ', COALESCE(description, '')) as description,
            CASE 
                WHEN transaction_type IN ('إيداع نقدي', 'تحويل وارد', 'فوائد') THEN amount 
                ELSE 0 
            END as debit,
            CASE 
                WHEN transaction_type IN ('سحب نقدي', 'تحويل صادر', 'رسوم بنكية') THEN amount 
                ELSE 0 
            END as credit
        FROM `tabBank Transaction Entry`
        WHERE bank_account = %s AND docstatus = 1
            AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (bank_account, from_date, to_date), as_dict=True)
    
    # جلب تحصيلات العملاء بتحويل بنكي
    customer_payments = frappe.db.sql("""
        SELECT 
            posting_date,
            'Customer Payment' as voucher_type,
            name as voucher_no,
            reference_no,
            CONCAT('تحصيل من عميل - ', customer, ' - ', COALESCE(remarks, '')) as description,
            paid_amount as debit,
            0 as credit
        FROM `tabCustomer Payment`
        WHERE bank_account = %s AND docstatus = 1
            AND payment_mode = 'تحويل بنكي'
            AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (bank_account, from_date, to_date), as_dict=True)
    
    # جلب مدفوعات الموردين بتحويل بنكي
    supplier_payments = frappe.db.sql("""
        SELECT 
            posting_date,
            'Supplier Payment' as voucher_type,
            name as voucher_no,
            reference_no,
            CONCAT('سداد لمورد - ', supplier, ' - ', COALESCE(remarks, '')) as description,
            0 as debit,
            paid_amount as credit
        FROM `tabSupplier Payment`
        WHERE bank_account = %s AND docstatus = 1
            AND payment_mode = 'تحويل بنكي'
            AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (bank_account, from_date, to_date), as_dict=True)
    
    # دمج جميع الحركات
    all_transactions = transactions + customer_payments + supplier_payments
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
            "reference_no": row.get("reference_no"),
            "description": row.get("description"),
            "debit": debit,
            "credit": credit,
            "balance": running_balance
        })
    
    # رصيد آخر المدة
    data.append({
        "posting_date": to_date,
        "voucher_type": "",
        "voucher_no": "",
        "reference_no": "",
        "description": _("رصيد آخر المدة"),
        "debit": 0,
        "credit": 0,
        "balance": running_balance
    })
    
    return data


def get_opening_balance(bank_account, from_date):
    """حساب رصيد أول المدة"""
    # الرصيد الافتتاحي
    opening = frappe.db.get_value("Bank Account", bank_account, "opening_balance") or 0
    
    # الإيداعات قبل الفترة
    deposits = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabBank Transaction Entry`
        WHERE bank_account = %s AND docstatus = 1 
            AND transaction_type IN ('إيداع نقدي', 'تحويل وارد', 'فوائد')
            AND posting_date < %s
    """, (bank_account, from_date))[0][0] or 0
    
    # السحوبات قبل الفترة
    withdrawals = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabBank Transaction Entry`
        WHERE bank_account = %s AND docstatus = 1 
            AND transaction_type IN ('سحب نقدي', 'تحويل صادر', 'رسوم بنكية')
            AND posting_date < %s
    """, (bank_account, from_date))[0][0] or 0
    
    # تحصيلات العملاء بتحويل بنكي قبل الفترة
    customer_deposits = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabCustomer Payment`
        WHERE bank_account = %s AND docstatus = 1 AND payment_mode = 'تحويل بنكي'
            AND posting_date < %s
    """, (bank_account, from_date))[0][0] or 0
    
    # مدفوعات الموردين بتحويل بنكي قبل الفترة
    supplier_withdrawals = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabSupplier Payment`
        WHERE bank_account = %s AND docstatus = 1 AND payment_mode = 'تحويل بنكي'
            AND posting_date < %s
    """, (bank_account, from_date))[0][0] or 0
    
    return (flt(opening) + flt(deposits) + flt(customer_deposits) 
            - flt(withdrawals) - flt(supplier_withdrawals))


def get_chart(data):
    if not data or len(data) <= 2:
        return None
    
    # تجميع البيانات حسب التاريخ
    dates = []
    deposits = []
    withdrawals = []
    
    for row in data[1:-1]:  # استثناء رصيد أول وآخر المدة
        date = str(row.get("posting_date"))
        if date not in dates:
            dates.append(date)
            deposits.append(0)
            withdrawals.append(0)
        
        idx = dates.index(date)
        deposits[idx] += row.get("debit", 0)
        withdrawals[idx] += row.get("credit", 0)
    
    # أخذ آخر 15 يوم فقط للعرض
    if len(dates) > 15:
        dates = dates[-15:]
        deposits = deposits[-15:]
        withdrawals = withdrawals[-15:]
    
    return {
        "data": {
            "labels": dates,
            "datasets": [
                {"name": _("إيداع"), "values": deposits},
                {"name": _("سحب"), "values": withdrawals}
            ]
        },
        "type": "bar",
        "colors": ["#28a745", "#dc3545"]
    }


def get_summary(data):
    if not data:
        return []
    
    total_deposits = sum(d.get("debit", 0) for d in data)
    total_withdrawals = sum(d.get("credit", 0) for d in data)
    closing_balance = data[-1].get("balance", 0) if data else 0
    
    return [
        {
            "value": total_deposits,
            "indicator": "Green",
            "label": _("إجمالي الإيداعات"),
            "datatype": "Currency"
        },
        {
            "value": total_withdrawals,
            "indicator": "Red",
            "label": _("إجمالي السحوبات"),
            "datatype": "Currency"
        },
        {
            "value": closing_balance,
            "indicator": "Blue",
            "label": _("الرصيد النهائي"),
            "datatype": "Currency"
        }
    ]
