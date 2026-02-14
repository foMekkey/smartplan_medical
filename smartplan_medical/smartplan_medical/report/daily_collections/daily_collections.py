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
            "fieldname": "posting_date",
            "label": _("التاريخ"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "name",
            "label": _("رقم الإيصال"),
            "fieldtype": "Link",
            "options": "Customer Payment",
            "width": 140
        },
        {
            "fieldname": "customer",
            "label": _("العميل"),
            "fieldtype": "Link",
            "options": "Pharma Customer",
            "width": 120
        },
        {
            "fieldname": "customer_name",
            "label": _("اسم العميل"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "payment_mode",
            "label": _("طريقة الدفع"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "paid_amount",
            "label": _("المبلغ"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "bank_account",
            "label": _("الحساب البنكي"),
            "fieldtype": "Link",
            "options": "Bank Account",
            "width": 120
        },
        {
            "fieldname": "remarks",
            "label": _("ملاحظات"),
            "fieldtype": "Data",
            "width": 150
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            cp.posting_date,
            cp.name,
            cp.customer,
            cp.customer_name,
            cp.mode_of_payment as payment_mode,
            cp.paid_amount,
            cp.bank_account,
            cp.remarks
        FROM `tabCustomer Payment` cp
        WHERE cp.docstatus = 1
            {conditions}
        ORDER BY cp.posting_date DESC, cp.creation DESC
    """.format(conditions=conditions), as_dict=True)
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append(f"AND cp.posting_date >= '{filters.get('from_date')}'")
    
    if filters.get("to_date"):
        conditions.append(f"AND cp.posting_date <= '{filters.get('to_date')}'")
    
    if filters.get("customer"):
        conditions.append(f"AND cp.customer = '{filters.get('customer')}'")
    
    if filters.get("payment_mode"):
        conditions.append(f"AND cp.mode_of_payment = '{filters.get('payment_mode')}'")
    
    if filters.get("bank_account"):
        conditions.append(f"AND cp.bank_account = '{filters.get('bank_account')}'")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    # تجميع حسب طريقة الدفع
    payment_modes = {}
    for row in data:
        mode = row.get("payment_mode", "غير محدد")
        payment_modes[mode] = payment_modes.get(mode, 0) + flt(row.get("paid_amount", 0))
    
    return {
        "data": {
            "labels": list(payment_modes.keys()),
            "datasets": [{
                "name": _("المبلغ"),
                "values": list(payment_modes.values())
            }]
        },
        "type": "pie",
        "colors": ["#28a745", "#007bff", "#ffc107"]
    }


def get_summary(data):
    if not data:
        return []
    
    total_amount = sum(d.get("paid_amount", 0) for d in data)
    total_cash = sum(d.get("paid_amount", 0) for d in data if d.get("payment_mode") == "نقدي")
    total_check = sum(d.get("paid_amount", 0) for d in data if d.get("payment_mode") == "شيك")
    total_transfer = sum(d.get("paid_amount", 0) for d in data if d.get("payment_mode") == "تحويل بنكي")
    
    return [
        {
            "value": total_amount,
            "indicator": "Green",
            "label": _("إجمالي التحصيلات"),
            "datatype": "Currency"
        },
        {
            "value": total_cash,
            "indicator": "Blue",
            "label": _("نقدي"),
            "datatype": "Currency"
        },
        {
            "value": total_check,
            "indicator": "Orange",
            "label": _("شيكات"),
            "datatype": "Currency"
        },
        {
            "value": total_transfer,
            "indicator": "Purple",
            "label": _("تحويلات"),
            "datatype": "Currency"
        }
    ]
