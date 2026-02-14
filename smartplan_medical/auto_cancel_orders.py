"""
Auto-cancel expired draft Sales Orders.
Runs as a scheduled task (every 15 minutes via cron).
Deletes draft Sales Orders that haven't been submitted within the configured time limit,
and releases their stock reservations.
"""
import frappe
from frappe.utils import now_datetime, time_diff_in_hours


def auto_cancel_expired_orders():
    """Find and delete draft Sales Orders older than the configured timeout."""
    # Get timeout setting (default 2 hours)
    timeout_hours = frappe.db.get_single_value(
        "Selling Settings", "custom_so_auto_cancel_hours"
    )
    if not timeout_hours:
        timeout_hours = 2

    timeout_hours = float(timeout_hours)
    now = now_datetime()

    # Find draft Sales Orders (docstatus=0) older than timeout
    draft_orders = frappe.get_all(
        "Sales Order",
        filters={
            "docstatus": 0,
        },
        fields=["name", "creation", "owner", "customer", "custom_sales_person"],
    )

    cancelled_count = 0

    for order in draft_orders:
        hours_since_creation = time_diff_in_hours(now, order.creation)

        if hours_since_creation >= timeout_hours:
            try:
                # Delete stock reservations for this order
                reservations = frappe.get_all(
                    "Stock Reservation",
                    filters={"sales_order": order.name},
                    pluck="name",
                )
                for r in reservations:
                    frappe.delete_doc(
                        "Stock Reservation", r, ignore_permissions=True
                    )

                # Delete the draft Sales Order
                frappe.delete_doc(
                    "Sales Order", order.name,
                    ignore_permissions=True,
                    force=True,
                )

                cancelled_count += 1

                frappe.logger().info(
                    f"Auto-cancelled expired Sales Order: {order.name} "
                    f"(Customer: {order.customer}, "
                    f"Sales Person: {order.custom_sales_person}, "
                    f"Age: {hours_since_creation:.1f} hours)"
                )

            except Exception as e:
                frappe.log_error(
                    title=f"Auto-Cancel SO Failed: {order.name}",
                    message=str(e),
                )

    if cancelled_count:
        frappe.db.commit()
        frappe.logger().info(
            f"Auto-cancel: Deleted {cancelled_count} expired draft Sales Orders"
        )
