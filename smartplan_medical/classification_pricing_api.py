"""
Classification Pricing API
Whitelisted methods for fetching active pricing per customer classification,
and for pulling purchased items with batch details.
"""
import json
import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def get_classification_pricing(classification, item_codes=None):
    """
    Get active Classification Price List items for a given classification.
    Used by Sales Order to auto-apply selling discounts.
    """
    if not classification:
        return []

    current_date = today()

    price_lists = frappe.get_all(
        "Classification Price List",
        filters={
            "classification": classification,
            "from_date": ["<=", current_date],
            "to_date": [">=", current_date],
            "docstatus": 1,
        },
        fields=["name"],
        order_by="modified desc",
        limit_page_length=1,
    )

    if not price_lists:
        return []

    cpl_name = price_lists[0].name

    filters = {"parent": cpl_name}
    if item_codes:
        if isinstance(item_codes, str):
            item_codes = json.loads(item_codes)
        filters["item_code"] = ["in", item_codes]

    items = frappe.get_all(
        "Classification Price List Item",
        filters=filters,
        fields=[
            "item_code",
            "item_name",
            "batch_no",
            "expiry_date",
            "standard_rate",
            "selling_discount",
            "discounted_rate",
        ],
    )

    return items


@frappe.whitelist()
def pull_purchased_items(from_date, to_date):
    """
    Pull all items purchased (from Purchase Invoices) within the given date range.
    Returns items with their batch details, purchase rates, and purchase discounts.
    Groups by item_code + batch_no.
    """
    if not from_date or not to_date:
        frappe.throw("يجب تحديد تاريخ البداية والنهاية")

    # Fetch from Purchase Invoice Items (submitted invoices within date range)
    items = frappe.db.sql("""
        SELECT
            pii.item_code,
            pii.item_name,
            pii.batch_no,
            b.expiry_date,
            pii.rate as purchase_rate,
            COALESCE(pii.discount_percentage, 0) as purchase_discount
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        LEFT JOIN `tabBatch` b ON b.name = pii.batch_no
        WHERE pi.docstatus = 1
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND pii.item_code IS NOT NULL
        GROUP BY pii.item_code, pii.batch_no
        ORDER BY pii.item_code, pii.batch_no
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    # Also check Purchase Receipts for items that might not have invoices yet
    receipt_items = frappe.db.sql("""
        SELECT
            pri.item_code,
            pri.item_name,
            pri.batch_no,
            b.expiry_date,
            pri.rate as purchase_rate,
            COALESCE(pri.discount_percentage, 0) as purchase_discount
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        LEFT JOIN `tabBatch` b ON b.name = pri.batch_no
        WHERE pr.docstatus = 1
          AND pr.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND pri.item_code IS NOT NULL
        GROUP BY pri.item_code, pri.batch_no
        ORDER BY pri.item_code, pri.batch_no
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    # Merge: use a set to track (item_code, batch_no) already added
    seen = set()
    result = []

    for item in items:
        key = (item.item_code, item.batch_no or "")
        if key not in seen:
            seen.add(key)
            result.append(item)

    for item in receipt_items:
        key = (item.item_code, item.batch_no or "")
        if key not in seen:
            seen.add(key)
            result.append(item)

    return result
