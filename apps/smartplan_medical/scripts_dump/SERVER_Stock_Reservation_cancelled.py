reservations = frappe.get_all(
    "Stock Reservation",
    filters={"sales_invoice": doc.name},
    pluck="name"
)

for r in reservations:
    frappe.delete_doc("Stock Reservation", r, ignore_permissions=True)
