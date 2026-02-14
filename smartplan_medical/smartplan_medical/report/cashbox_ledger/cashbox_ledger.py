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
    summary = get_summary(data, filters)
    
    return columns, data, None, chart, summary


def validate_filters(filters):
    if not filters.get("cashbox"):
        frappe.throw(_("يجب اختيار الصندوق"))
    
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
            "fieldname": "party_type",
            "label": _("نوع الطرف"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "party",
            "label": _("الطرف"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "description",
            "label": _("البيان"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "receipt",
            "label": _("وارد"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "payment",
            "label": _("صادر"),
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
    cashbox = filters.get("cashbox")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    # رصيد أول المدة
    opening_balance = get_opening_balance(cashbox, from_date)
    
    data.append({
        "posting_date": from_date,
        "voucher_type": "",
        "voucher_no": "",
        "party_type": "",
        "party": "",
        "description": _("رصيد أول المدة"),
        "receipt": opening_balance if opening_balance > 0 else 0,
        "payment": 0,
        "balance": opening_balance
    })
    
    running_balance = opening_balance
    
    # جلب حركات الصندوق
    transactions = frappe.db.sql("""
        SELECT 
            posting_date,
            'Cash Transaction' as voucher_type,
            name as voucher_no,
            party_type,
            party,
            CONCAT(
                CASE WHEN transaction_type = 'قبض' THEN 'قبض - ' ELSE 'صرف - ' END,
                COALESCE(description, '')
            ) as description,
            CASE WHEN transaction_type = 'قبض' THEN amount ELSE 0 END as receipt,
            CASE WHEN transaction_type = 'صرف' THEN amount ELSE 0 END as payment
        FROM `tabCash Transaction`
        WHERE cashbox = %s AND docstatus = 1
            AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (cashbox, from_date, to_date), as_dict=True)
    
    # جلب حركات البنك (إيداع وسحب نقدي)
    bank_transactions = frappe.db.sql("""
        SELECT 
            posting_date,
            'Bank Transaction Entry' as voucher_type,
            name as voucher_no,
            '' as party_type,
            bank_account as party,
            CONCAT(
                CASE 
                    WHEN transaction_type = 'إيداع نقدي' THEN 'إيداع بالبنك - '
                    WHEN transaction_type = 'سحب نقدي' THEN 'سحب من البنك - '
                    ELSE transaction_type || ' - '
                END,
                COALESCE(description, '')
            ) as description,
            CASE WHEN transaction_type = 'سحب نقدي' THEN amount ELSE 0 END as receipt,
            CASE WHEN transaction_type = 'إيداع نقدي' THEN amount ELSE 0 END as payment
        FROM `tabBank Transaction Entry`
        WHERE cashbox = %s AND docstatus = 1
            AND transaction_type IN ('إيداع نقدي', 'سحب نقدي')
            AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (cashbox, from_date, to_date), as_dict=True)
    
    # جلب تحصيلات العملاء نقداً
    customer_payments = frappe.db.sql("""
        SELECT 
            posting_date,
            'Customer Payment' as voucher_type,
            name as voucher_no,
            'Pharma Customer' as party_type,
            customer as party,
            CONCAT('تحصيل من عميل - ', COALESCE(remarks, '')) as description,
            paid_amount as receipt,
            0 as payment
        FROM `tabCustomer Payment`
        WHERE cashbox = %s AND docstatus = 1
            AND payment_mode = 'نقدي'
            AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (cashbox, from_date, to_date), as_dict=True)
    
    # جلب مدفوعات الموردين نقداً
    supplier_payments = frappe.db.sql("""
        SELECT 
            posting_date,
            'Supplier Payment' as voucher_type,
            name as voucher_no,
            'Pharma Supplier' as party_type,
            supplier as party,
            CONCAT('سداد لمورد - ', COALESCE(remarks, '')) as description,
            0 as receipt,
            paid_amount as payment
        FROM `tabSupplier Payment`
        WHERE cashbox = %s AND docstatus = 1
            AND payment_mode = 'نقدي'
            AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (cashbox, from_date, to_date), as_dict=True)
    
    # دمج جميع الحركات
    all_transactions = transactions + bank_transactions + customer_payments + supplier_payments
    all_transactions.sort(key=lambda x: (x.get("posting_date"), x.get("voucher_no", "")))
    
    # حساب الأرصدة المتراكمة
    for row in all_transactions:
        receipt = flt(row.get("receipt", 0))
        payment = flt(row.get("payment", 0))
        running_balance += receipt - payment
        
        data.append({
            "posting_date": row.get("posting_date"),
            "voucher_type": row.get("voucher_type"),
            "voucher_no": row.get("voucher_no"),
            "party_type": row.get("party_type"),
            "party": row.get("party"),
            "description": row.get("description"),
            "receipt": receipt,
            "payment": payment,
            "balance": running_balance
        })
    
    # رصيد آخر المدة
    data.append({
        "posting_date": to_date,
        "voucher_type": "",
        "voucher_no": "",
        "party_type": "",
        "party": "",
        "description": _("رصيد آخر المدة"),
        "receipt": 0,
        "payment": 0,
        "balance": running_balance
    })
    
    return data


def get_opening_balance(cashbox, from_date):
    """حساب رصيد أول المدة"""
    # الرصيد الافتتاحي للصندوق
    initial_balance = frappe.db.get_value("Cashbox", cashbox, "opening_balance") or 0
    
    # مجموع الواردات قبل الفترة
    total_receipts = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabCash Transaction`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'قبض' AND posting_date < %s
    """, (cashbox, from_date))[0][0] or 0
    
    # مجموع المصروفات قبل الفترة
    total_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabCash Transaction`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'صرف' AND posting_date < %s
    """, (cashbox, from_date))[0][0] or 0
    
    # حركات البنك قبل الفترة
    bank_receipts = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabBank Transaction Entry`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'سحب نقدي' AND posting_date < %s
    """, (cashbox, from_date))[0][0] or 0
    
    bank_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabBank Transaction Entry`
        WHERE cashbox = %s AND docstatus = 1 AND transaction_type = 'إيداع نقدي' AND posting_date < %s
    """, (cashbox, from_date))[0][0] or 0
    
    # تحصيلات العملاء نقداً قبل الفترة
    customer_receipts = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabCustomer Payment`
        WHERE cashbox = %s AND docstatus = 1 AND payment_mode = 'نقدي' AND posting_date < %s
    """, (cashbox, from_date))[0][0] or 0
    
    # مدفوعات الموردين نقداً قبل الفترة
    supplier_payments_before = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabSupplier Payment`
        WHERE cashbox = %s AND docstatus = 1 AND payment_mode = 'نقدي' AND posting_date < %s
    """, (cashbox, from_date))[0][0] or 0
    
    return (flt(initial_balance) + flt(total_receipts) + flt(bank_receipts) + flt(customer_receipts) 
            - flt(total_payments) - flt(bank_payments) - flt(supplier_payments_before))


def get_chart(data):
    if not data or len(data) <= 2:
        return None
    
    # تجميع البيانات حسب التاريخ
    dates = []
    receipts = []
    payments = []
    
    for row in data[1:-1]:  # استثناء رصيد أول وآخر المدة
        date = str(row.get("posting_date"))
        if date not in dates:
            dates.append(date)
            receipts.append(0)
            payments.append(0)
        
        idx = dates.index(date)
        receipts[idx] += row.get("receipt", 0)
        payments[idx] += row.get("payment", 0)
    
    # أخذ آخر 15 يوم فقط للعرض
    if len(dates) > 15:
        dates = dates[-15:]
        receipts = receipts[-15:]
        payments = payments[-15:]
    
    return {
        "data": {
            "labels": dates,
            "datasets": [
                {"name": _("وارد"), "values": receipts},
                {"name": _("صادر"), "values": payments}
            ]
        },
        "type": "bar",
        "colors": ["#28a745", "#dc3545"]
    }


def get_summary(data, filters):
    if not data:
        return []
    
    total_receipts = sum(d.get("receipt", 0) for d in data)
    total_payments = sum(d.get("payment", 0) for d in data)
    closing_balance = data[-1].get("balance", 0) if data else 0
    
    # الرصيد الفعلي من الصندوق
    actual_balance = frappe.db.get_value("Cashbox", filters.get("cashbox"), "current_balance") or 0
    
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
            "value": closing_balance,
            "indicator": "Blue",
            "label": _("الرصيد النهائي"),
            "datatype": "Currency"
        },
        {
            "value": actual_balance,
            "indicator": "Orange",
            "label": _("الرصيد الفعلي"),
            "datatype": "Currency"
        }
    ]
