"""
Classification Pricing API
Whitelisted methods for fetching active pricing per customer classification.
Used by Sales Order JS to auto-apply discounts.
"""
import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def get_classification_pricing(classification, item_codes=None):
    """
    Get active Classification Price List items for a given classification.

    Args:
        classification: Customer Classification name
        item_codes: optional JSON list of item codes to filter

    Returns:
        list of dicts with item_code, batch_no, discount_percentage, discounted_rate, standard_rate
    """
    if not classification:
        return []

    current_date = today()

    # Find active (submitted) price lists for this classification
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
            import json
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
            "discount_percentage",
            "discounted_rate",
        ],
    )

    return items
