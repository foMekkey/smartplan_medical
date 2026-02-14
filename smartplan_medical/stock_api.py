"""
Stock availability API for Sales Order item popup.
Returns stock levels across all warehouses, reservation details
from draft Sales Order items, and batch information.
"""
import json
import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_item_stock_info(item_code, set_warehouse=None):
    """
    Return stock availability for an item across all warehouses,
    plus reservations from draft Sales Orders (docstatus=0) including
    batch allocations, and full batch details.
    """
    if not item_code:
        return {"warehouses": [], "total_actual": 0, "total_reserved": 0, "total_available": 0, "batches": []}

    # Get stock from all warehouses
    bins = frappe.get_all(
        "Bin",
        filters={"item_code": item_code, "actual_qty": [">", 0]},
        fields=["warehouse", "actual_qty"],
        order_by="actual_qty desc",
    )

    # Get reservations from draft Sales Order Items directly
    reservations = frappe.db.sql(
        """
        SELECT
            soi.warehouse,
            soi.qty,
            soi.custom_batch_allocations,
            so.name AS sales_order,
            so.custom_sales_person,
            IFNULL(emp.employee_name, so.custom_sales_person) AS sales_person_name
        FROM `tabSales Order Item` soi
        INNER JOIN `tabSales Order` so ON so.name = soi.parent
        LEFT JOIN `tabEmployee` emp ON emp.name = so.custom_sales_person
        WHERE soi.item_code = %s
        AND so.docstatus = 0
        """,
        (item_code,),
        as_dict=True,
    )

    # Build reservation map: warehouse -> list of reservations
    reservation_map = {}
    for r in reservations:
        wh = r.warehouse
        if wh not in reservation_map:
            reservation_map[wh] = []

        # Parse batch allocations JSON
        batch_allocs = []
        if r.custom_batch_allocations:
            try:
                batch_allocs = json.loads(r.custom_batch_allocations)
            except Exception:
                batch_allocs = []

        reservation_map[wh].append({
            "sales_order": r.sales_order,
            "sales_person": r.sales_person_name or "",
            "qty": flt(r.qty),
            "batch_allocations": batch_allocs,
        })

    result = []
    total_actual = 0
    total_reserved = 0

    for b in bins:
        wh = b.warehouse
        actual = flt(b.actual_qty)
        wh_reservations = reservation_map.get(wh, [])
        reserved = sum(r["qty"] for r in wh_reservations)
        available = actual - reserved

        result.append({
            "warehouse": wh,
            "actual_qty": actual,
            "reserved_qty": reserved,
            "available_qty": available,
            "is_selected": (wh == set_warehouse) if set_warehouse else False,
            "reservations": wh_reservations,
        })

        total_actual += actual
        total_reserved += reserved

    # Get batch details for this item
    batches = frappe.db.sql(
        """
        SELECT
            b.name AS batch_no,
            b.batch_qty AS qty,
            b.expiry_date,
            b.manufacturing_date
        FROM `tabBatch` b
        WHERE b.item = %s
        AND b.batch_qty > 0
        ORDER BY b.expiry_date ASC
        """,
        (item_code,),
        as_dict=True,
    )

    batch_list = []
    for b in batches:
        batch_list.append({
            "batch_no": b.batch_no,
            "qty": flt(b.qty),
            "expiry_date": str(b.expiry_date) if b.expiry_date else "",
            "manufacturing_date": str(b.manufacturing_date) if b.manufacturing_date else "",
        })

    return {
        "warehouses": result,
        "total_actual": total_actual,
        "total_reserved": total_reserved,
        "total_available": total_actual - total_reserved,
        "batches": batch_list,
    }


@frappe.whitelist()
def save_batch_allocations(so_name, item_code, allocations):
    """Save batch allocations to the Sales Order Item."""
    if isinstance(allocations, str):
        allocations = json.loads(allocations)

    so = frappe.get_doc("Sales Order", so_name)
    if so.docstatus != 0:
        frappe.throw("لا يمكن تعديل الباتشات إلا في الطلبات المسودة")

    for item in so.items:
        if item.item_code == item_code:
            item.custom_batch_allocations = json.dumps(allocations, ensure_ascii=False)
            break

    so.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "ok"}
