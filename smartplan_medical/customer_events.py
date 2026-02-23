"""
Customer Server Events
Handles auto-linking of customers to Classification Price Lists.
When a customer's classification changes, update their default_price_list.
"""
import frappe


def after_save(doc, method):
    """Sync customer's default_price_list based on their classification."""
    classification = doc.custom_classification
    if not classification:
        # If no classification, clear the price list only if it was auto-set
        return

    pl_name = f"قائمة أسعار بيع - {classification}"

    # Fallback: also check old naming convention
    if not frappe.db.exists("Price List", pl_name):
        pl_name_old = f"قائمة أسعار - {classification}"
        if frappe.db.exists("Price List", pl_name_old):
            pl_name = pl_name_old

    if frappe.db.exists("Price List", pl_name):
        if doc.default_price_list != pl_name:
            frappe.db.set_value(
                "Customer", doc.name, "default_price_list", pl_name,
                update_modified=False,
            )
            frappe.msgprint(
                f"تم ربط العميل بقائمة الأسعار: {pl_name}",
                alert=True,
                indicator="green",
            )
