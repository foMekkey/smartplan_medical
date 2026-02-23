# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, date_diff, today


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)

    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "item_code",
            "label": _("الصنف"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 140,
        },
        {
            "fieldname": "item_name",
            "label": _("اسم الصنف"),
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "fieldname": "batch_no",
            "label": _("رقم الباتش"),
            "fieldtype": "Link",
            "options": "Batch",
            "width": 120,
        },
        {
            "fieldname": "expiry_date",
            "label": _("تاريخ الانتهاء"),
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "fieldname": "days_to_expiry",
            "label": _("أيام للانتهاء"),
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "fieldname": "purchase_date",
            "label": _("تاريخ الشراء"),
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "fieldname": "purchase_rate",
            "label": _("سعر الشراء"),
            "fieldtype": "Currency",
            "width": 110,
        },
        {
            "fieldname": "purchase_discount",
            "label": _("خصم الشراء %"),
            "fieldtype": "Percent",
            "width": 100,
        },
        {
            "fieldname": "net_purchase_rate",
            "label": _("صافي الشراء"),
            "fieldtype": "Currency",
            "width": 110,
        },
        {
            "fieldname": "selling_rate",
            "label": _("سعر البيع"),
            "fieldtype": "Currency",
            "width": 110,
        },
        {
            "fieldname": "selling_discount",
            "label": _("خصم البيع %"),
            "fieldtype": "Percent",
            "width": 100,
        },
        {
            "fieldname": "net_selling_rate",
            "label": _("صافي البيع"),
            "fieldtype": "Currency",
            "width": 110,
        },
        {
            "fieldname": "profit_margin",
            "label": _("هامش الربح %"),
            "fieldtype": "Percent",
            "width": 110,
        },
        {
            "fieldname": "profit_amount",
            "label": _("الربح/الخسارة"),
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "status",
            "label": _("الحالة"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "recommendation",
            "label": _("التوصية"),
            "fieldtype": "Data",
            "width": 200,
        },
    ]


def get_data(filters):
    pi_conditions = get_conditions(filters, parent_alias="pi", item_alias="pii")
    pr_conditions = get_conditions(filters, parent_alias="pr", item_alias="pri")

    # Get purchase data — items with batches from Purchase Invoices
    purchase_data = frappe.db.sql("""
        SELECT
            pii.item_code,
            pii.item_name,
            pii.batch_no,
            b.expiry_date,
            pi.posting_date as purchase_date,
            pii.price_list_rate as purchase_rate,
            COALESCE(pii.discount_percentage, 0) as purchase_discount,
            pii.rate as net_purchase_rate,
            pii.qty
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        LEFT JOIN `tabBatch` b ON b.name = pii.batch_no
        WHERE pi.docstatus = 1
            {conditions}
        ORDER BY pii.item_code, b.expiry_date ASC
    """.format(conditions=pi_conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "item_code": filters.get("item_code"),
    }, as_dict=True)

    # Also check Purchase Receipts for items without invoices
    receipt_data = frappe.db.sql("""
        SELECT
            pri.item_code,
            pri.item_name,
            pri.batch_no,
            b.expiry_date,
            pr.posting_date as purchase_date,
            pri.price_list_rate as purchase_rate,
            COALESCE(pri.discount_percentage, 0) as purchase_discount,
            pri.rate as net_purchase_rate,
            pri.qty
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        LEFT JOIN `tabBatch` b ON b.name = pri.batch_no
        WHERE pr.docstatus = 1
            {conditions}
        ORDER BY pri.item_code, b.expiry_date ASC
    """.format(conditions=pr_conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "item_code": filters.get("item_code"),
    }, as_dict=True)

    # Merge, deduplicate by (item_code, batch_no)
    seen = set()
    all_items = []
    for item in purchase_data + receipt_data:
        key = (item.item_code, item.batch_no or "")
        if key not in seen:
            seen.add(key)
            all_items.append(item)

    # Get selling data from Classification Price Lists if classification filter set
    selling_map = {}
    classification = filters.get("classification")
    if classification:
        selling_map = _get_classification_selling_map(classification)

    # If no classification filter, get from all submitted CPLs
    if not selling_map:
        selling_map = _get_all_selling_map()

    # Build report data
    current_date = getdate(today())
    result = []

    for item in all_items:
        row = {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "batch_no": item.batch_no or "",
            "expiry_date": item.expiry_date,
            "purchase_date": item.purchase_date,
            "purchase_rate": flt(item.purchase_rate),
            "purchase_discount": flt(item.purchase_discount),
            "net_purchase_rate": flt(item.net_purchase_rate),
        }

        # Calculate days to expiry
        if item.expiry_date:
            row["days_to_expiry"] = date_diff(item.expiry_date, current_date)
        else:
            row["days_to_expiry"] = None

        # Get selling price from classification map
        sell_key = (item.item_code, item.batch_no or "")
        sell_item_key = (item.item_code, "")
        sell_info = selling_map.get(sell_key) or selling_map.get(sell_item_key)

        if sell_info:
            row["selling_rate"] = flt(sell_info.get("standard_rate", 0))
            row["selling_discount"] = flt(sell_info.get("selling_discount", 0))
            row["net_selling_rate"] = flt(sell_info.get("discounted_rate", 0))
        else:
            # Fallback: use Item standard selling rate
            std_rate = frappe.db.get_value("Item", item.item_code, "standard_rate") or 0
            row["selling_rate"] = flt(std_rate)
            row["selling_discount"] = 0
            row["net_selling_rate"] = flt(std_rate)

        # Calculate profit margin
        net_purchase = flt(row["net_purchase_rate"])
        net_selling = flt(row["net_selling_rate"])

        if net_purchase > 0:
            row["profit_margin"] = ((net_selling - net_purchase) / net_purchase) * 100
        else:
            row["profit_margin"] = 0

        row["profit_amount"] = net_selling - net_purchase

        # Status and recommendations
        is_loss = row["profit_amount"] < 0
        is_expiring = row["days_to_expiry"] is not None and row["days_to_expiry"] <= 90
        is_warning = row["days_to_expiry"] is not None and row["days_to_expiry"] <= 180

        if is_loss:
            row["status"] = "خسارة ❌"
        elif is_expiring:
            row["status"] = "أولوية صرف ⚠️"
        else:
            row["status"] = "ربح ✅"

        # Recommendations
        recommendations = []
        if is_loss:
            recommendations.append("مراجعة سعر البيع - خسارة!")
        if is_expiring:
            recommendations.append(f"أولوية صرف - ينتهي خلال {row['days_to_expiry']} يوم")
        elif is_warning:
            recommendations.append(f"قريب الانتهاء - {row['days_to_expiry']} يوم")

        row["recommendation"] = " | ".join(recommendations) if recommendations else ""

        # Filter out non-loss items if show_loss_only
        if filters.get("show_loss_only") and not is_loss:
            continue

        # Filter by dispatch priority (expiry within N days)
        dispatch_priority = filters.get("dispatch_priority")
        if dispatch_priority:
            days_limit = int(dispatch_priority.replace(" يوم", ""))
            if row["days_to_expiry"] is None or row["days_to_expiry"] > days_limit:
                continue

        result.append(row)

    # Sort: losses first, then by expiry date (earliest first)
    result.sort(key=lambda x: (
        0 if x.get("profit_amount", 0) < 0 else 1,
        x.get("days_to_expiry") if x.get("days_to_expiry") is not None else 99999,
    ))

    return result


def get_conditions(filters, parent_alias="pi", item_alias="pii"):
    conditions = []
    if filters.get("from_date"):
        conditions.append(f"AND {parent_alias}.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append(f"AND {parent_alias}.posting_date <= %(to_date)s")
    if filters.get("item_code"):
        conditions.append(f"AND {item_alias}.item_code = %(item_code)s")
    return " ".join(conditions)


def _get_classification_selling_map(classification):
    """Get selling data from the latest submitted CPL for a classification."""
    cpls = frappe.get_all(
        "Classification Price List",
        filters={"classification": classification, "docstatus": 1},
        fields=["name"],
        order_by="modified desc",
        limit_page_length=1,
    )
    if not cpls:
        return {}

    items = frappe.get_all(
        "Classification Price List Item",
        filters={"parent": cpls[0].name},
        fields=["item_code", "batch_no", "standard_rate", "selling_discount", "discounted_rate"],
    )

    result = {}
    for item in items:
        key = (item.item_code, item.batch_no or "")
        result[key] = item
    return result


def _get_all_selling_map():
    """Get selling data from all submitted CPLs (latest per item+batch)."""
    cpls = frappe.get_all(
        "Classification Price List",
        filters={"docstatus": 1},
        fields=["name"],
        order_by="modified desc",
    )
    if not cpls:
        return {}

    result = {}
    for cpl in cpls:
        items = frappe.get_all(
            "Classification Price List Item",
            filters={"parent": cpl.name},
            fields=["item_code", "batch_no", "standard_rate", "selling_discount", "discounted_rate"],
        )
        for item in items:
            key = (item.item_code, item.batch_no or "")
            if key not in result:
                result[key] = item
    return result


def get_chart(data):
    if not data:
        return None

    profit_items = [d for d in data if flt(d.get("profit_amount", 0)) >= 0]
    loss_items = [d for d in data if flt(d.get("profit_amount", 0)) < 0]

    return {
        "data": {
            "labels": ["ربح", "خسارة"],
            "datasets": [{
                "name": _("عدد الأصناف"),
                "values": [len(profit_items), len(loss_items)],
            }],
        },
        "type": "donut",
        "colors": ["#28a745", "#dc3545"],
    }


def get_summary(data):
    total_items = len(data)
    loss_items = [d for d in data if flt(d.get("profit_amount", 0)) < 0]
    expiring = [d for d in data if d.get("days_to_expiry") is not None and d["days_to_expiry"] <= 90]

    total_profit = sum(flt(d.get("profit_amount", 0)) for d in data if flt(d.get("profit_amount", 0)) >= 0)
    total_loss = sum(flt(d.get("profit_amount", 0)) for d in data if flt(d.get("profit_amount", 0)) < 0)

    return [
        {
            "value": total_items,
            "indicator": "Blue",
            "label": _("إجمالي الأصناف"),
            "datatype": "Int",
        },
        {
            "value": len(loss_items),
            "indicator": "Red",
            "label": _("أصناف خاسرة"),
            "datatype": "Int",
        },
        {
            "value": len(expiring),
            "indicator": "Orange",
            "label": _("قريبة الانتهاء (90 يوم)"),
            "datatype": "Int",
        },
        {
            "value": total_profit,
            "indicator": "Green",
            "label": _("إجمالي الأرباح"),
            "datatype": "Currency",
        },
        {
            "value": abs(total_loss),
            "indicator": "Red",
            "label": _("إجمالي الخسائر"),
            "datatype": "Currency",
        },
    ]
