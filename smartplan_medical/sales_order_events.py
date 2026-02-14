"""
Sales Order Server Events
Handles stock reservation, over-reservation validation, discount logic,
and auto-creation of Sales Invoice / Delivery Note on submit.
"""
import frappe
from frappe.utils import flt, getdate, today


def before_validate(doc, method):
    """Auto-fill delivery_date with today if not set, so ERPNext validation passes."""
    if not doc.delivery_date:
        doc.delivery_date = today()
    for row in doc.items:
        if not row.delivery_date:
            row.delivery_date = doc.delivery_date

def before_save(doc, method):
    """
    Validate that requested qty does not exceed available stock.
    Block items with zero stock completely.
    """
    if doc.docstatus == 2:
        return  # Skip on cancel

    for row in doc.items:
        # Set price before discount (read-only display field)
        row.custom_price_before_discount = flt(row.price_list_rate)

        if not row.item_code:
            continue

        warehouse = row.warehouse or doc.set_warehouse
        if not warehouse:
            continue

        # Get actual stock qty from Bin
        bin_data = frappe.get_all(
            "Bin",
            filters={
                "item_code": row.item_code,
                "warehouse": warehouse,
            },
            fields=["actual_qty"],
        )

        actual_qty = bin_data[0].actual_qty if bin_data else 0

        # Get reservations from OTHER orders (exclude current order)
        reserved = frappe.db.sql(
            """
            SELECT IFNULL(SUM(qty), 0)
            FROM `tabStock Reservation`
            WHERE item_code=%s
            AND warehouse=%s
            AND sales_order != %s
            """,
            (row.item_code, warehouse, doc.name),
        )[0][0]

        available = flt(actual_qty) - flt(reserved)

        # Block if no stock at all
        if actual_qty <= 0:
            frappe.throw(
                f"""<b>⛔ لا يوجد رصيد للصنف في المخزن</b><br><br>
<b>الصنف:</b> {row.item_code}<br>
<b>المخزن:</b> {warehouse}<br>
<b>الرصيد الحالي:</b> {actual_qty}<br><br>
يرجى اختيار صنف آخر أو تغيير المخزن."""
            )

        # Block if requested qty exceeds available
        if row.qty > available:
            # Show who has reservations
            reservations = frappe.db.sql(
                """
                SELECT sales_order, sales_person, qty
                FROM `tabStock Reservation`
                WHERE item_code=%s AND warehouse=%s
                """,
                (row.item_code, warehouse),
                as_dict=True,
            )

            details = ""
            for r in reservations:
                details += f"<br>طلب: {r.sales_order} | مندوب: {r.sales_person} | كمية: {r.qty}"

            frappe.throw(
                f"""<b>لا يمكن حجز كمية أكبر من المتاح</b><br><br>
<b>الصنف:</b> {row.item_code}<br>
<b>المخزن:</b> {warehouse}<br><br>
<b>المخزون الفعلي:</b> {actual_qty}<br>
<b>المحجوز:</b> {reserved}<br>
<b>المتاح للبيع:</b> {available}<br>
<b>المطلوب:</b> {row.qty}<br><br>
<b>الحجوزات الحالية:</b>
{details}"""
            )

    # Calculate total before discount
    total_before = sum(
        flt(row.price_list_rate) * flt(row.qty)
        for row in doc.items
        if row.item_code
    )
    doc.custom_total_before_discount = total_before

def after_save(doc, method):
    """
    Create stock reservations for each item in the Sales Order.
    Only for draft orders (docstatus=0).
    Deletes old reservations first, then re-creates them.
    """
    if doc.docstatus != 0:
        return  # Only create reservations for drafts

    # Delete old reservations for this order
    old = frappe.get_all(
        "Stock Reservation",
        filters={"sales_order": doc.name},
        pluck="name",
    )
    for d in old:
        frappe.delete_doc("Stock Reservation", d, ignore_permissions=True)

    # Create new reservations
    for row in doc.items:
        if not row.item_code:
            continue

        reservation = frappe.new_doc("Stock Reservation")
        reservation.item_code = row.item_code
        reservation.warehouse = row.warehouse or doc.set_warehouse
        reservation.qty = row.qty
        reservation.sales_order = doc.name
        reservation.sales_person = doc.get("custom_sales_person", "")
        reservation.insert(ignore_permissions=True)


def on_submit(doc, method):
    """
    On Sales Order submit:
    1. Delete stock reservations (stock is now committed via SO)
    2. Create Delivery Note (draft) FIRST
    3. Create Sales Invoice (submitted)
    """
    frappe.logger().info(f"on_submit fired for Sales Order: {doc.name}")

    # Delete stock reservations — stock is now committed
    _delete_reservations(doc.name)

    # Create Delivery Note (draft) FIRST — before billing
    _create_delivery_note(doc)

    # Create Sales Invoice (submitted)
    _create_sales_invoice(doc)


def after_cancel(doc, method):
    """Delete stock reservations when the Sales Order is cancelled."""
    _delete_reservations(doc.name)


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


# ============================================================
# Helper functions
# ============================================================

def _delete_reservations(sales_order_name):
    """Delete all Stock Reservations linked to a Sales Order."""
    reservations = frappe.get_all(
        "Stock Reservation",
        filters={"sales_order": sales_order_name},
        pluck="name",
    )
    for r in reservations:
        frappe.delete_doc("Stock Reservation", r, ignore_permissions=True)


def _create_sales_invoice(so_doc):
    """Create and submit a Sales Invoice from the Sales Order."""
    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

    si = make_sales_invoice(so_doc.name)
    si.flags.ignore_permissions = True
    si.flags.ignore_mandatory = True
    si.set_posting_time = 0

    # Copy custom fields (always copy, even if empty)
    si.custom_sales_person = so_doc.get("custom_sales_person") or ""

    si.insert(ignore_permissions=True, ignore_mandatory=True)
    si.submit()

    frappe.msgprint(
        f'✅ تم إنشاء فاتورة مبيعات: <a href="/app/sales-invoice/{si.name}">{si.name}</a>',
        alert=True,
        indicator="green",
    )


def _create_delivery_note(so_doc):
    """Create a Delivery Note (draft) from the Sales Order."""
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

    dn = make_delivery_note(so_doc.name)
    dn.flags.ignore_permissions = True
    dn.flags.ignore_mandatory = True

    # Copy custom fields (always copy, even if empty)
    dn.custom_sales_person = so_doc.get("custom_sales_person") or ""

    dn.insert(ignore_permissions=True, ignore_mandatory=True)
    # NOTE: Delivery Note stays as DRAFT — not submitted

    frappe.msgprint(
        f'📦 تم إنشاء إذن تسليم (مسودة): <a href="/app/delivery-note/{dn.name}">{dn.name}</a>',
        alert=True,
        indicator="blue",
    )

