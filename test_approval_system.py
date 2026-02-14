#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Approval System for Tele Sales Order
=========================================
This script tests the approval workflow:
1. Create a Tele Sales Order with high discount (requires approval)
2. Try to Submit without approval (should fail)
3. Approve the order
4. Submit successfully
"""

import frappe
from frappe import _

def test_approval_workflow():
	"""Test the complete approval workflow"""
	print("\n" + "="*80)
	print("🧪 اختبار نظام الموافقات لطلب البيع التليفوني")
	print("="*80 + "\n")
	
	# Connect to site
	frappe.init(site="reunion.eg-smartplan.solutions")
	frappe.connect()
	
	# Set current user to test user
	frappe.set_user("Administrator")
	
	try:
		# Step 1: Get or create test customer
		print("1️⃣ البحث عن عميل تجريبي...")
		
		if not frappe.db.exists("Customer", "_Test Customer"):
			customer = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "_Test Customer",
				"customer_type": "Company",
				"customer_group": "Commercial",
				"territory": "Egypt"
			})
			customer.insert(ignore_permissions=True)
			print(f"   ✅ تم إنشاء العميل: {customer.name}")
		else:
			print("   ✅ العميل موجود بالفعل: _Test Customer")
		
		# Step 2: Get test item
		print("\n2️⃣ البحث عن صنف تجريبي...")
		
		items = frappe.db.get_list("Item", 
			filters={"is_sales_item": 1, "disabled": 0}, 
			fields=["name", "item_name", "standard_rate"],
			limit=1
		)
		
		if not items:
			print("   ⚠️ لا توجد أصناف في النظام")
			return
		
		test_item = items[0]
		print(f"   ✅ تم العثور على صنف: {test_item['name']}")
		
		# Step 3: Create Tele Sales Order with HIGH discount
		print("\n3️⃣ إنشاء طلب بيع تليفوني بخصم عالي (60%)...")
		
		tso = frappe.get_doc({
			"doctype": "Tele Sales Order",
			"customer": "_Test Customer",
			"order_date": frappe.utils.today(),
			"items": [{
				"item_code": test_item['name'],
				"qty": 10,
				"rate": test_item.get('standard_rate', 100),
				"item_discount_percent": 60  # High discount!
			}]
		})
		
		tso.insert(ignore_permissions=True)
		print(f"   ✅ تم إنشاء الطلب: {tso.name}")
		print(f"   📊 إجمالي الخصم: {tso.total_discount_percent:.2f}%")
		print(f"   ⚠️ يتطلب موافقة: {'نعم' if tso.requires_approval else 'لا'}")
		print(f"   📝 الحالة: {tso.status}")
		
		# Step 4: Try to Submit WITHOUT approval (should FAIL)
		print("\n4️⃣ محاولة عمل Submit بدون موافقة (يجب أن تفشل)...")
		
		try:
			tso.submit()
			print("   ❌ خطأ: تم السماح بالـ Submit بدون موافقة!")
			return False
		except Exception as e:
			if "موافقة" in str(e) or "Approval" in str(e):
				print(f"   ✅ تم منع Submit بنجاح!")
				print(f"   💬 الرسالة: {str(e)[:100]}...")
			else:
				print(f"   ⚠️ فشل لسبب آخر: {str(e)}")
				raise
		
		# Step 5: Approve the order
		print("\n5️⃣ الموافقة على الطلب...")
		
		# Reload to ensure we have latest data
		tso.reload()
		
		# Call approve method
		tso.approve_order()
		
		print(f"   ✅ تمت الموافقة بواسطة: {tso.approved_by}")
		print(f"   📅 تاريخ الموافقة: {tso.approval_date}")
		print(f"   📝 الحالة الجديدة: {tso.status}")
		
		# Step 6: Now Submit should work
		print("\n6️⃣ محاولة عمل Submit بعد الموافقة (يجب أن تنجح)...")
		
		tso.reload()
		tso.submit()
		
		print(f"   ✅ تم Submit بنجاح!")
		print(f"   📋 رقم أمر البيع: {tso.sales_order_reference}")
		
		# Step 7: Verify Sales Order was created
		print("\n7️⃣ التحقق من إنشاء أمر البيع في ERPNext...")
		
		if tso.sales_order_reference:
			so = frappe.get_doc("Sales Order", tso.sales_order_reference)
			print(f"   ✅ تم إنشاء أمر البيع: {so.name}")
			print(f"   📝 الحالة: {so.status}")
			print(f"   💰 الإجمالي: {so.grand_total:.2f}")
		else:
			print("   ⚠️ لم يتم إنشاء أمر البيع")
		
		# Summary
		print("\n" + "="*80)
		print("✅ نجح اختبار نظام الموافقات!")
		print("="*80)
		print(f"\n📌 ملخص الاختبار:")
		print(f"   • الطلب: {tso.name}")
		print(f"   • الخصم: {tso.total_discount_percent:.2f}%")
		print(f"   • يتطلب موافقة: نعم")
		print(f"   • تمت الموافقة بواسطة: {tso.approved_by}")
		print(f"   • تم Submit: نعم")
		print(f"   • أمر البيع: {tso.sales_order_reference}")
		print("\n" + "="*80)
		
		return True
		
	except Exception as e:
		print(f"\n❌ حدث خطأ: {str(e)}")
		import traceback
		traceback.print_exc()
		return False
	
	finally:
		frappe.db.commit()
		frappe.destroy()


if __name__ == "__main__":
	success = test_approval_workflow()
	exit(0 if success else 1)
