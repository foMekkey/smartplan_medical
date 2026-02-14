import frappe

def execute():
    """
    اختبار إنشاء مخزن تجريبي للتأكد من حل المشكلة
    """
    print("🧪 اختبار إنشاء مخزن...")
    
    test_name = "_Test Pharma Warehouse"
    
    # Delete if exists
    if frappe.db.exists("Pharma Warehouse", test_name):
        frappe.delete_doc("Pharma Warehouse", test_name, force=1)
        print(f"🗑️ حذف المخزن التجريبي القديم")
    
    # Create test warehouse
    try:
        wh = frappe.new_doc("Pharma Warehouse")
        wh.warehouse_name = test_name
        wh.location = "موقع تجريبي"
        wh.storage_capacity = 1000
        wh.warehouse_type = "رئيسي"  # Not "توزيع", so it won't set warehouse_type in ERPNext
        wh.insert(ignore_permissions=True)
        
        print(f"✅ تم إنشاء المخزن التجريبي: {wh.name}")
        print(f"   مربوط بمخزن ERPNext: {wh.erpnext_warehouse}")
        
        # Check ERPNext warehouse
        if wh.erpnext_warehouse:
            erpnext_wh = frappe.get_doc("Warehouse", wh.erpnext_warehouse)
            print(f"   نوع المخزن في ERPNext: {erpnext_wh.warehouse_type or 'Not Set'}")
        
        # Cleanup
        frappe.delete_doc("Pharma Warehouse", test_name, force=1)
        if wh.erpnext_warehouse and frappe.db.exists("Warehouse", wh.erpnext_warehouse):
            frappe.delete_doc("Warehouse", wh.erpnext_warehouse, force=1)
        
        frappe.db.commit()
        print("\n✅ الاختبار نجح! المشكلة تم حلها")
        
    except Exception as e:
        print(f"❌ فشل الاختبار: {str(e)}")
        frappe.db.rollback()

if __name__ == "__main__":
    execute()
