#!/usr/bin/env python3
"""
Comprehensive test for all fetch_from field paths
"""
import frappe

def execute():
    frappe.init(site='reunion.eg-smartplan.solutions')
    frappe.connect()
    
    print("\n" + "="*70)
    print("🧪 COMPREHENSIVE FETCH_FROM VALIDATION TEST")
    print("="*70)
    
    test_results = []
    
    # Test 1: Pharma Customer -> legal_name
    print("\n1️⃣ Testing Pharma Customer fields...")
    try:
        customers = frappe.get_all("Pharma Customer", fields=["name", "legal_name"], limit=1)
        if customers:
            customer = customers[0]
            result = frappe.client.get_value("Pharma Customer", ["legal_name"], customer.name)
            print(f"   ✅ Pharma Customer.legal_name - SUCCESS")
            print(f"      Sample: {result}")
            test_results.append(("Pharma Customer.legal_name", "✅ PASS"))
        else:
            print(f"   ⚠️  No Pharma Customer records to test")
            test_results.append(("Pharma Customer.legal_name", "⚠️ SKIP (no data)"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        test_results.append(("Pharma Customer.legal_name", f"❌ FAIL: {str(e)}"))
    
    # Test 2: Tele Sales Order -> customer.legal_name
    print("\n2️⃣ Testing Tele Sales Order -> customer.legal_name...")
    try:
        tso_meta = frappe.get_meta("Tele Sales Order")
        customer_name_field = tso_meta.get_field("customer_name")
        if customer_name_field and customer_name_field.fetch_from == "customer.legal_name":
            print(f"   ✅ Tele Sales Order.customer_name fetch_from is correct")
            test_results.append(("TSO.customer_name fetch_from", "✅ PASS"))
        else:
            print(f"   ❌ Tele Sales Order.customer_name fetch_from is incorrect")
            print(f"      Expected: customer.legal_name")
            print(f"      Got: {customer_name_field.fetch_from if customer_name_field else 'NOT FOUND'}")
            test_results.append(("TSO.customer_name fetch_from", "❌ FAIL"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        test_results.append(("TSO.customer_name fetch_from", f"❌ FAIL: {str(e)}"))
    
    # Test 3: Tele Sales Order -> sales_order_reference
    print("\n3️⃣ Testing Tele Sales Order fields...")
    try:
        tso_meta = frappe.get_meta("Tele Sales Order")
        sor_field = tso_meta.get_field("sales_order_reference")
        if sor_field:
            print(f"   ✅ Tele Sales Order.sales_order_reference exists")
            
            # Try to query it
            tso_list = frappe.get_all("Tele Sales Order", 
                fields=["name", "sales_order_reference"], 
                limit=1)
            print(f"   ✅ Can query sales_order_reference")
            test_results.append(("TSO.sales_order_reference", "✅ PASS"))
        else:
            print(f"   ❌ sales_order_reference field not found")
            test_results.append(("TSO.sales_order_reference", "❌ FAIL"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        test_results.append(("TSO.sales_order_reference", f"❌ FAIL: {str(e)}"))
    
    # Test 4: Warehouse Dispatch -> tele_sales_order.sales_order_reference
    print("\n4️⃣ Testing Warehouse Dispatch -> sales_order fetch_from...")
    try:
        wd_meta = frappe.get_meta("Warehouse Dispatch")
        sales_order_field = wd_meta.get_field("sales_order")
        if sales_order_field and sales_order_field.fetch_from == "tele_sales_order.sales_order_reference":
            print(f"   ✅ Warehouse Dispatch.sales_order fetch_from is correct")
            test_results.append(("WD.sales_order fetch_from", "✅ PASS"))
        else:
            print(f"   ❌ Warehouse Dispatch.sales_order fetch_from is incorrect")
            print(f"      Expected: tele_sales_order.sales_order_reference")
            print(f"      Got: {sales_order_field.fetch_from if sales_order_field else 'NOT FOUND'}")
            test_results.append(("WD.sales_order fetch_from", "❌ FAIL"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        test_results.append(("WD.sales_order fetch_from", f"❌ FAIL: {str(e)}"))
    
    # Test 5: Warehouse Dispatch -> customer.legal_name
    print("\n5️⃣ Testing Warehouse Dispatch -> customer_name fetch_from...")
    try:
        wd_meta = frappe.get_meta("Warehouse Dispatch")
        customer_name_field = wd_meta.get_field("customer_name")
        if customer_name_field and customer_name_field.fetch_from == "customer.legal_name":
            print(f"   ✅ Warehouse Dispatch.customer_name fetch_from is correct")
            test_results.append(("WD.customer_name fetch_from", "✅ PASS"))
        else:
            print(f"   ❌ Warehouse Dispatch.customer_name fetch_from is incorrect")
            print(f"      Expected: customer.legal_name")
            print(f"      Got: {customer_name_field.fetch_from if customer_name_field else 'NOT FOUND'}")
            test_results.append(("WD.customer_name fetch_from", "❌ FAIL"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        test_results.append(("WD.customer_name fetch_from", f"❌ FAIL: {str(e)}"))
    
    # Test 6: Delivery Collection -> customer.legal_name
    print("\n6️⃣ Testing Delivery Collection -> customer_name fetch_from...")
    try:
        dc_meta = frappe.get_meta("Delivery Collection")
        customer_name_field = dc_meta.get_field("customer_name")
        if customer_name_field and customer_name_field.fetch_from == "customer.legal_name":
            print(f"   ✅ Delivery Collection.customer_name fetch_from is correct")
            test_results.append(("DC.customer_name fetch_from", "✅ PASS"))
        else:
            print(f"   ❌ Delivery Collection.customer_name fetch_from is incorrect")
            print(f"      Expected: customer.legal_name")
            print(f"      Got: {customer_name_field.fetch_from if customer_name_field else 'NOT FOUND'}")
            test_results.append(("DC.customer_name fetch_from", "❌ FAIL"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        test_results.append(("DC.customer_name fetch_from", f"❌ FAIL: {str(e)}"))
    
    # Test 7: Test actual link validation (simulate form behavior)
    print("\n7️⃣ Testing actual link validation (form behavior)...")
    try:
        customers = frappe.get_all("Pharma Customer", fields=["name"], limit=1)
        if customers:
            customer_name = customers[0].name
            # This simulates what happens when you select a link field
            result = frappe.client.get_value(
                "Pharma Customer",
                ["legal_name"],
                customer_name
            )
            print(f"   ✅ Link validation works for Pharma Customer")
            print(f"      Customer: {customer_name} -> legal_name: {result.get('legal_name')}")
            test_results.append(("Link validation (Pharma Customer)", "✅ PASS"))
        else:
            print(f"   ⚠️  No data to test")
            test_results.append(("Link validation", "⚠️ SKIP"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        test_results.append(("Link validation", f"❌ FAIL: {str(e)}"))
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in test_results if "✅" in result)
    failed = sum(1 for _, result in test_results if "❌" in result)
    skipped = sum(1 for _, result in test_results if "⚠️" in result)
    total = len(test_results)
    
    for test_name, result in test_results:
        print(f"{result:20} {test_name}")
    
    print("\n" + "-"*70)
    print(f"Total Tests: {total}")
    print(f"✅ Passed:   {passed}")
    print(f"❌ Failed:   {failed}")
    print(f"⚠️  Skipped:  {skipped}")
    print("-"*70)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("All fetch_from paths are correctly configured.")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please review the errors above.")
    
    print("="*70 + "\n")
    
    frappe.destroy()

if __name__ == "__main__":
    execute()
