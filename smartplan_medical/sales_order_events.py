"""
Sales Order Server Events
Handles stock reservation, over-reservation validation, and discount logic.
Migrated from database Server Scripts to app code.
"""
import frappe
from frappe.utils import flt


def before_save(doc, method):
    """
    Validate that requested qty does not exceed available stock.
    (Migrated from Server Script: 'over reservation')
    """
    for row in doc.items:
        if not row.item_code:
            continue

        warehouse = row.warehouse or doc.set_warehouse
        if not warehouse:
            continue

        # Get actual stock qty
        actual = frappe.get_all(
            "Bin",
            filters={
                "item_code": row.item_code,
                "warehouse": warehouse,
            },
            fields=["actual_qty"],
        )

        actual_qty = actual[0].actual_qty if actual else 0

        # Get reservations from other orders
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

        available = actual_qty - reserved

        if row.qty > available:
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

            frappe.msgprint(
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
            frappe.throw("لا يمكن حجز كمية أكبر من المتاح")


def after_save(doc, method):
    """
    Create stock reservations for each item in the Sales Order.
    Deletes old reservations first, then re-creates them.
    (Migrated from Server Script: 'Stock Reservation')
    """
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


def after_cancel(doc, method):
    """
    Delete stock reservations when the Sales Order is cancelled.
    (Migrated from Server Script: 'Stock Reservation_cancelled')
    """
    reservations = frappe.get_all(
        "Stock Reservation",
        filters={"sales_order": doc.name},
        pluck="name",
    )
    for r in reservations:
        frappe.delete_doc("Stock Reservation", r, ignore_permissions=True)


def before_insert(doc, method):
    """
    Apply discount from custom_discount_ field to item rates.
    (Migrated from Server Script: 'discount' - was disabled)
    """
    for item in doc.items:
        if item.get("custom_discount_") and item.get("price_list_rate"):
            discount = flt(item.custom_discount_)
            price = flt(item.price_list_rate)
            qty = flt(item.qty) or 1

            new_rate = price - (price * discount / 100)

            item.discount_percentage = discount
            item.rate = new_rate
            item.amount = new_rate * qty
