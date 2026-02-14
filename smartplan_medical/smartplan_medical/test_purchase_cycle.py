import frappe
from frappe.utils import nowdate

def test_pharma_purchase_cycle():
    print("🚀 Testing Pharma Purchase Cycle Logic...")

    # 1. Create Test Supplier
    if not frappe.db.exists("Supplier", "_Test Supplier"):
        supplier = frappe.new_doc("Supplier")
        supplier.supplier_name = "_Test Supplier"
        supplier.supplier_group = "All Supplier Groups"
        supplier.insert()

    # 1.1 Create Pharma Supplier
    if not frappe.db.exists("Pharma Supplier", "_Test Pharma Supplier"):
        ps = frappe.new_doc("Pharma Supplier")
        ps.legal_name = "_Test Pharma Supplier"
        ps.erpnext_supplier = "_Test Supplier"
        ps.insert()
        print("✅ Created Test Pharma Supplier")
    else:
        ps = frappe.get_doc("Pharma Supplier", "_Test Pharma Supplier")

    # 2. Create Test Item
    if not frappe.db.exists("Item", "_Test Item"):
        item = frappe.new_doc("Item")
        item.item_code = "_Test Item"
        item.item_group = "Products"
        item.stock_uom = "Nos"
        item.is_stock_item = 1
        item.insert()

    if not frappe.db.exists("Pharma Item", "_Test Item"):
        pi = frappe.new_doc("Pharma Item")
        pi.item_code = "_Test Item"
        pi.item_name = "_Test Item"
        pi.insert()
        print("✅ Created Test Pharma Item")

    # 3. Create Pharma Purchase Cycle
    cycle = frappe.new_doc("Pharma Purchase Cycle")
    cycle.pharma_supplier = ps.name
    cycle.transaction_date = nowdate()
    cycle.append("items", {
        "pharma_item": "_Test Item",
        "qty": 10,
        "rate": 100
    })
    cycle.insert()
    print(f"✅ Created Cycle Doc: {cycle.name}")

    # 4. Test Create PO
    cycle.create_purchase_order()
    cycle.reload()
    if cycle.status == "Ordered" and cycle.purchase_order:
        print(f"✅ PO Created: {cycle.purchase_order}")
    else:
        print("❌ PO Creation Failed")
        return

    # 5. Test Create PR
    cycle.create_purchase_receipt()
    cycle.reload()
    if cycle.status == "Received" and cycle.purchase_receipt:
        print(f"✅ PR Created: {cycle.purchase_receipt}")
    else:
        print("❌ PR Creation Failed")
        return

    # 6. Test Create PI
    cycle.create_purchase_invoice()
    cycle.reload()
    if cycle.status == "Billed" and cycle.purchase_invoice:
        print(f"✅ PI Created: {cycle.purchase_invoice}")
    else:
        print("❌ PI Creation Failed")
        return

    print("\n🎉 All Tests Passed!")

test_pharma_purchase_cycle()
