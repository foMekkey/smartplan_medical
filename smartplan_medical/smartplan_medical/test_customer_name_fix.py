#!/usr/bin/env python3
"""
Test script to verify customer_name field resolution
"""
import frappe

def execute():
    frappe.init(site='reunion.eg-smartplan.solutions')
    frappe.connect()
    
    print("\n" + "="*60)
    print("🧪 Testing customer_name field resolution")
    print("="*60)
    
    # Test 1: Check Pharma Customer fields
    print("\n1️⃣ Checking Pharma Customer DocType...")
    pc_meta = frappe.get_meta("Pharma Customer")
    legal_name_field = pc_meta.get_field("legal_name")
    if legal_name_field:
        print(f"   ✅ legal_name field exists in Pharma Customer")
        print(f"      Type: {legal_name_field.fieldtype}, Label: {legal_name_field.label}")
    
    # Test 2: Check Warehouse Dispatch fetch_from
    print("\n2️⃣ Checking Warehouse Dispatch customer_name fetch_from...")
    wd_meta = frappe.get_meta("Warehouse Dispatch")
    customer_name_field = wd_meta.get_field("customer_name")
    if customer_name_field:
        print(f"   ✅ customer_name field exists")
        print(f"      fetch_from: {customer_name_field.fetch_from}")
        if customer_name_field.fetch_from == "customer.legal_name":
            print(f"      ✅ Correctly set to 'customer.legal_name'")
        else:
            print(f"      ⚠️  Expected 'customer.legal_name', got '{customer_name_field.fetch_from}'")
    
    # Test 3: Check Delivery Collection fetch_from
    print("\n3️⃣ Checking Delivery Collection customer_name fetch_from...")
    dc_meta = frappe.get_meta("Delivery Collection")
    customer_name_field = dc_meta.get_field("customer_name")
    if customer_name_field:
        print(f"   ✅ customer_name field exists")
        print(f"      fetch_from: {customer_name_field.fetch_from}")
        if customer_name_field.fetch_from == "customer.legal_name":
            print(f"      ✅ Correctly set to 'customer.legal_name'")
        else:
            print(f"      ⚠️  Expected 'customer.legal_name', got '{customer_name_field.fetch_from}'")
    
    # Test 4: Try to get a Pharma Customer and verify field access
    print("\n4️⃣ Testing actual field access...")
    customers = frappe.get_all("Pharma Customer", fields=["name", "legal_name"], limit=1)
    if customers:
        customer = customers[0]
        print(f"   ✅ Found customer: {customer.name}")
        print(f"      legal_name: {customer.legal_name}")
        
        # Try validate_link simulation
        try:
            result = frappe.client.get_value(
                "Pharma Customer",
                ["legal_name"],
                customer.name
            )
            print(f"   ✅ frappe.client.get_value worked: {result}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    else:
        print("   ℹ️  No Pharma Customer records found to test")
    
    # Test 5: Test get_pending_tele_sales_orders
    print("\n5️⃣ Testing get_pending_tele_sales_orders function...")
    try:
        from smartplan_medical.smartplan_medical.doctype.warehouse_dispatch.warehouse_dispatch import get_pending_tele_sales_orders
        orders = get_pending_tele_sales_orders()
        print(f"   ✅ Function executed successfully")
        print(f"      Returned {len(orders)} orders")
        if orders:
            print(f"      Sample order: {orders[0]}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60 + "\n")
    
    frappe.destroy()

if __name__ == "__main__":
    execute()
