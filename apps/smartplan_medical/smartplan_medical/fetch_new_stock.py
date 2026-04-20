"""
Fetch New Stock Items API
Returns recently received items with batch and expiry details
for use in Sales Invoice.
"""
import frappe
from frappe.utils import nowdate, add_days, getdate, flt


@frappe.whitelist()
def get_new_stock_items(warehouse=None, days=30):
    """
    Get items that were recently received into stock with batch and expiry info.

    Args:
        warehouse: Optional warehouse filter
        days: Number of days to look back (default 30)

    Returns:
        List of dicts with item details, batch info, expiry, and available qty
    """
    days = int(days)
    from_date = add_days(nowdate(), -days)

    conditions = """
        sle.posting_date >= %(from_date)s
        AND sle.actual_qty > 0
        AND sle.is_cancelled = 0
    """
    params = {"from_date": from_date}

    if warehouse:
        conditions += " AND sle.warehouse = %(warehouse)s"
        params["warehouse"] = warehouse

    query = f"""
        SELECT
            sle.item_code,
            item.item_name,
            sle.batch_no,
            batch.expiry_date,
            sle.warehouse,
            sle.stock_uom,
            SUM(sle.actual_qty) as total_incoming_qty,
            ROUND(AVG(sle.incoming_rate), 2) as avg_incoming_rate,
            MIN(sle.posting_date) as first_received_date,
            MAX(sle.posting_date) as last_received_date,
            item.item_group
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabItem` item ON item.name = sle.item_code
        LEFT JOIN `tabBatch` batch ON batch.name = sle.batch_no
        WHERE {conditions}
        GROUP BY sle.item_code, sle.batch_no, sle.warehouse
        ORDER BY sle.posting_date DESC, sle.item_code ASC
    """

    items = frappe.db.sql(query, params, as_dict=True)

    # Calculate actual available qty per item+batch+warehouse
    today = getdate(nowdate())
    result = []
    for item in items:
        # Get current balance qty for this item+batch+warehouse
        balance_filters = {
            "item_code": item.item_code,
            "warehouse": item.warehouse,
            "is_cancelled": 0,
        }
        if item.batch_no:
            balance_filters["batch_no"] = item.batch_no

        balance = frappe.db.sql(
            """
            SELECT SUM(actual_qty) as qty
            FROM `tabStock Ledger Entry`
            WHERE item_code = %(item_code)s
            AND warehouse = %(warehouse)s
            AND is_cancelled = 0
            {batch_filter}
        """.format(
                batch_filter="AND batch_no = %(batch_no)s" if item.batch_no else ""
            ),
            {
                "item_code": item.item_code,
                "warehouse": item.warehouse,
                "batch_no": item.batch_no or "",
            },
            as_dict=True,
        )

        available_qty = flt(balance[0].qty) if balance else 0
        if available_qty <= 0:
            continue

        # Determine expiry status
        expiry_status = "no_expiry"
        days_to_expiry = None
        if item.expiry_date:
            expiry_date = getdate(item.expiry_date)
            days_to_expiry = (expiry_date - today).days
            if days_to_expiry < 0:
                expiry_status = "expired"
            elif days_to_expiry <= 30:
                expiry_status = "near_expiry"
            elif days_to_expiry <= 90:
                expiry_status = "warning"
            else:
                expiry_status = "ok"

        result.append(
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "item_group": item.item_group,
                "batch_no": item.batch_no or "",
                "expiry_date": str(item.expiry_date) if item.expiry_date else "",
                "days_to_expiry": days_to_expiry,
                "expiry_status": expiry_status,
                "warehouse": item.warehouse,
                "stock_uom": item.stock_uom,
                "available_qty": available_qty,
                "total_incoming_qty": flt(item.total_incoming_qty),
                "avg_incoming_rate": flt(item.avg_incoming_rate),
                "first_received_date": str(item.first_received_date),
                "last_received_date": str(item.last_received_date),
            }
        )

    return result


@frappe.whitelist()
def get_expiring_items(days=90, warehouse=None):
    """
    Fetch items with batches expiring within the given days.
    Supports both legacy Batch No (in SLE) and new Serial and Batch Bundle (SABB).
    """
    from frappe.utils import add_days, nowdate, getdate, flt
    
    days = int(days)
    today = getdate(nowdate())
    expiry_limit = add_days(today, days)
    
    params = {"expiry_limit": expiry_limit, "today": today}
    warehouse_condition = ""
    if warehouse:
        warehouse_condition = "AND sle.warehouse = %(warehouse)s"
        params["warehouse"] = warehouse
        
    query = f"""
        SELECT
            item_code, item_name, batch_no, expiry_date, warehouse, SUM(qty) as qty, description, stock_uom, item_group
        FROM (
            -- Legacy: Batch No directly in SLE
            SELECT
                sle.item_code,
                item.item_name,
                sle.batch_no,
                batch.expiry_date,
                sle.warehouse,
                SUM(sle.actual_qty) as qty,
                item.description,
                item.stock_uom,
                item.item_group
            FROM
                `tabStock Ledger Entry` sle
            INNER JOIN `tabBatch` batch ON sle.batch_no = batch.name
            INNER JOIN `tabItem` item ON sle.item_code = item.name
            WHERE
                sle.is_cancelled = 0
                AND sle.batch_no IS NOT NULL
                AND batch.expiry_date <= %(expiry_limit)s
                AND batch.expiry_date >= %(today)s
                {warehouse_condition}
            GROUP BY
                sle.item_code, sle.batch_no, sle.warehouse

            UNION ALL

            -- New: Serial and Batch Bundle (SABB)
            SELECT
                sle.item_code,
                item.item_name,
                sabe.batch_no,
                batch.expiry_date,
                sle.warehouse,
                SUM(sabe.qty * (CASE WHEN sle.actual_qty < 0 THEN -1 ELSE 1 END)) as qty,
                item.description,
                item.stock_uom,
                item.item_group
            FROM
                `tabStock Ledger Entry` sle
            INNER JOIN `tabSerial and Batch Bundle` sabb ON sle.serial_and_batch_bundle = sabb.name
            INNER JOIN `tabSerial and Batch Entry` sabe ON sabb.name = sabe.parent
            INNER JOIN `tabBatch` batch ON sabe.batch_no = batch.name
            INNER JOIN `tabItem` item ON sle.item_code = item.name
            WHERE
                sle.is_cancelled = 0
                AND sabb.is_cancelled = 0
                AND batch.expiry_date <= %(expiry_limit)s
                AND batch.expiry_date >= %(today)s
                {warehouse_condition}
            GROUP BY
                sle.item_code, sabe.batch_no, sle.warehouse
        ) as unioned_data
        GROUP BY item_code, batch_no, warehouse
        HAVING qty > 0
        ORDER BY expiry_date ASC
    """
    
    items = frappe.db.sql(query, params, as_dict=True)
    
    # Format dates and ensure numeric types for JS
    results = []
    for item in items:
        results.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "batch_no": item.batch_no,
            "expiry_date": str(item.expiry_date),
            "warehouse": item.warehouse,
            "available_qty": flt(item.qty),
            "stock_uom": item.stock_uom,
            "description": item.description,
        })
        
    return results
