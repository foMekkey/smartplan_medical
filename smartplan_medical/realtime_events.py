import frappe


def on_stock_change(doc, method):
    """Emit realtime event when stock/sales documents are submitted or cancelled."""
    doctype_labels = {
        "Purchase Invoice": "فاتورة شراء",
        "Sales Invoice": "فاتورة بيع",
        "Stock Entry": "حركة مخزنية",
        "Delivery Note": "إذن تسليم",
        "Purchase Receipt": "إيصال استلام",
    }

    label = doctype_labels.get(doc.doctype, doc.doctype)
    action = "إلغاء" if method == "on_cancel" else "اعتماد"

    frappe.publish_realtime(
        event="profit_report_update",
        message={
            "message": f"تم {action} {label}: {doc.name}",
            "doctype": doc.doctype,
            "name": doc.name,
        },
        after_commit=True,
    )
