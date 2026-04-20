for row in doc.items:
    if not row.item_code:
        continue

    warehouse = row.warehouse or doc.set_warehouse

    actual = frappe.get_all(
        "Bin",
        filters={
            "item_code": row.item_code,
            "warehouse": warehouse
        },
        fields=["actual_qty"]
    )

    actual_qty = actual[0].actual_qty if actual else 0

    reserved = frappe.db.sql("""
        select ifnull(sum(qty),0)
        from `tabStock Reservation`
        where item_code=%s
        and warehouse=%s
        and sales_invoice != %s
    """, (row.item_code, warehouse, doc.name))[0][0]

    available = actual_qty - reserved

    if row.qty > available:

        reservations = frappe.db.sql("""
            select sales_invoice, sales_person, qty
            from `tabStock Reservation`
            where item_code=%s and warehouse=%s
        """, (row.item_code, warehouse), as_dict=True)

        details = ""
        for r in reservations:
            details += f"<br>فاتورة: {r.sales_invoice} | مندوب: {r.sales_person} | كمية: {r.qty}"

        frappe.msgprint(f"""
<b>لا يمكن حجز كمية أكبر من المتاح</b><br><br>

<b>الصنف:</b> {row.item_code}<br>
<b>المخزن:</b> {warehouse}<br><br>

<b>المخزون الفعلي:</b> {actual_qty}<br>
<b>المحجوز:</b> {reserved}<br>
<b>المتاح للبيع:</b> {available}<br>
<b>المطلوب:</b> {row.qty}<br><br>

<b>الحجوزات الحالية:</b>
{details}
""")

        frappe.throw("لا يمكن حجز كمية أكبر من المتاح ")
