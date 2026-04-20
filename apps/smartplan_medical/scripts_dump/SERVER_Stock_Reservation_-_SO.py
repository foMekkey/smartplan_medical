old = frappe.get_all(
    "Stock Reservation",
    filters={"sales_order": doc.name},
    pluck="name"
)

for d in old:
    frappe.delete_doc("Stock Reservation", d, ignore_permissions=True)

for row in doc.items:
    if not row.item_code:
        continue

    reservation = frappe.new_doc("Stock Reservation")
    reservation.item_code = row.item_code
    reservation.warehouse = row.warehouse or doc.set_warehouse
    reservation.qty = row.qty
    reservation.sales_order = doc.name
    reservation.sales_person = doc.custom_sales_person
    reservation.insert(ignore_permissions=True)
