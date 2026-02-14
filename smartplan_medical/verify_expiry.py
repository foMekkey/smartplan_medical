
import frappe
from frappe.utils import add_days, nowdate
from smartplan_medical.fetch_new_stock import get_expiring_items


def execute():
    # 1. Create Item
    item_code = "TEST-EXP-ITEM-" + frappe.generate_hash(length=5)
    if not frappe.db.exists("Item", item_code):
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Test Expiry Item",
            "item_group": "Products",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "has_batch_no": 1,
            "has_expiry_date": 1,
            "create_new_batch": 1,
            "batch_number_series": "TEST-BATCH-.#####"
        }).insert()
    
    # 2. Create Batch expiring in 10 days
    expiry_date = add_days(nowdate(), 10)
    batch_no = "TEST-BATCH-10DAYS-" + frappe.generate_hash(length=5)
    if not frappe.db.exists("Batch", batch_no):
        frappe.get_doc({
            "doctype": "Batch",
            "batch_id": batch_no,
            "item": item_code,
            "expiry_date": expiry_date
        }).insert()
        
    frappe.db.commit() # Ensure item/batch are committed
        
    # 3. Add Stock
    warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
    if not warehouse:
        print("❌ No valid warehouse found!")
        return

    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "items": [{
            "item_code": item_code,
            "qty": 10,
            "uom": "Nos",
            "batch_no": batch_no,
            "t_warehouse": warehouse,
            "basic_rate": 100.0
        }]
    })
    se.insert()
    se.submit()
    
    # Debug SE
    se.reload()
    print("Debug SE Items:")
    for d in se.items:
        print(f"Item: {d.item_code}, Batch: {d.batch_no}, Qty: {d.qty}")

    print(f"Created Item {item_code} with Batch {batch_no} expiring on {expiry_date}")
    
    # Debug
    print("Debug SLE:")
    sles = frappe.db.get_list("Stock Ledger Entry", fields=["item_code", "batch_no", "warehouse", "actual_qty", "posting_date", "serial_and_batch_bundle"], filters={"item_code": item_code})
    print(sles)
    
    print("Debug Batch:")
    batch = frappe.db.get_value("Batch", batch_no, ["name", "expiry_date"], as_dict=True)
    print(batch)
    
    # 4. Test API
    print("\nTesting get_expiring_items(days=30)...")
    items_30 = get_expiring_items(days=30)
    found_30 = any(i['batch_no'] == batch_no for i in items_30)
    if found_30:
        print("✅ Found item within 30 days.")
    else:
        print("❌ Item NOT found within 30 days!")
        
    print("\nTesting get_expiring_items(days=5)...")
    items_5 = get_expiring_items(days=5)
    found_5 = any(i['batch_no'] == batch_no for i in items_5)
    if not found_5:
        print("✅ Item correctly NOT found within 5 days.")
    else:
        print("❌ Item INCORRECTLY found within 5 days!")
        
    # Cleanup (Optional, but good for test hygiene)
    # Reverting stock entry is complex, maybe just leave it as test data is fine in dev env.
