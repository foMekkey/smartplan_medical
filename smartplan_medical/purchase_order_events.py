"""
Purchase Order Server Events
Handles discount logic and auto-creation of Purchase Invoice / Purchase Receipt on submit.
Same pattern as Sales Order events.
"""
import frappe
from frappe.utils import flt


def before_save(doc, method):
    """Set price before discount for each item."""
    if doc.docstatus == 2:
        return  # Skip on cancel

    for row in doc.items:
        # Set price before discount (read-only display field)
        row.custom_price_before_discount = flt(row.price_list_rate)

    # Calculate total before discount
    total_before = sum(
        flt(row.price_list_rate) * flt(row.qty)
        for row in doc.items
        if row.item_code
    )
    doc.custom_total_before_discount = total_before


def before_insert(doc, method):
    """Apply discount from custom_discount_ field to item rates."""
    for item in doc.items:
        if item.get("custom_discount_") and item.get("price_list_rate"):
            discount = flt(item.custom_discount_)
            price = flt(item.price_list_rate)
            qty = flt(item.qty) or 1

            new_rate = price - (price * discount / 100)

            item.discount_percentage = discount
            item.rate = new_rate
            item.amount = new_rate * qty


def on_submit(doc, method):
    """
    On Purchase Order submit:
    1. Create Purchase Receipt (draft)
    2. Create Purchase Invoice (submitted)
    """
    frappe.logger().info(f"on_submit fired for Purchase Order: {doc.name}")

    # Create Purchase Receipt (draft) FIRST
    _create_purchase_receipt(doc)

    # Create Purchase Invoice (submitted)
    _create_purchase_invoice(doc)


# ============================================================
# Helper functions
# ============================================================

def _create_purchase_invoice(po_doc):
    """Create and submit a Purchase Invoice from the Purchase Order."""
    from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice

    pi = make_purchase_invoice(po_doc.name)
    pi.flags.ignore_permissions = True
    pi.flags.ignore_mandatory = True
    pi.set_posting_time = 0

    # Copy batch/serial from PO items
    _copy_batch_serial(po_doc, pi)

    pi.insert(ignore_permissions=True, ignore_mandatory=True)
    pi.submit()

    frappe.msgprint(
        f'✅ تم إنشاء فاتورة مشتريات: <a href="/app/purchase-invoice/{pi.name}">{pi.name}</a>',
        alert=True,
        indicator="green",
    )


def _create_purchase_receipt(po_doc):
    """Create a Purchase Receipt (draft) from the Purchase Order."""
    from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

    pr = make_purchase_receipt(po_doc.name)
    pr.flags.ignore_permissions = True
    pr.flags.ignore_mandatory = True

    # Copy batch/serial from PO items
    _copy_batch_serial(po_doc, pr)

    pr.insert(ignore_permissions=True, ignore_mandatory=True)
    # NOTE: Purchase Receipt stays as DRAFT — not submitted

    frappe.msgprint(
        f'📦 تم إنشاء إيصال استلام (مسودة): <a href="/app/purchase-receipt/{pr.name}">{pr.name}</a>',
        alert=True,
        indicator="blue",
    )


def _copy_batch_serial(po_doc, target_doc):
    """Copy batch_no and serial_no from PO Items to target document items."""
    # Build mapping: (item_code, po_detail) -> {batch_no, serial_no}
    po_item_map = {}
    for row in po_doc.items:
        po_item_map[row.name] = {
            "batch_no": row.get("custom_batch_no") or "",
            "serial_no": row.get("custom_serial_no") or "",
        }

    for item in target_doc.items:
        po_detail = item.get("purchase_order_item") or item.get("po_detail")
        if po_detail and po_detail in po_item_map:
            info = po_item_map[po_detail]
            if info["batch_no"]:
                item.batch_no = info["batch_no"]
            if info["serial_no"]:
                item.serial_no = info["serial_no"]
