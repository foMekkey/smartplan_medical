import frappe

def execute():
    """
    Check available Warehouse Types in ERPNext
    """
    print("🔍 فحص أنواع المخازن المتاحة...")
    
    # Check if Warehouse Type DocType exists
    if not frappe.db.exists("DocType", "Warehouse Type"):
        print("⚠️ DocType 'Warehouse Type' غير موجود في هذا الإصدار من ERPNext")
        print("   سيتم إنشاء المخازن بدون تحديد النوع")
        return
    
    # Get all warehouse types
    wh_types = frappe.get_all("Warehouse Type", fields=["name"])
    
    if not wh_types:
        print("⚠️ لا توجد أنواع مخازن معرفة في النظام")
        print("   يجب إنشاء Warehouse Types أولاً")
    else:
        print(f"✅ الأنواع المتاحة ({len(wh_types)}):")
        for wt in wh_types:
            print(f"   - {wt.name}")
    
    # Check default warehouses
    print("\n📦 المخازن الموجودة:")
    warehouses = frappe.get_all("Warehouse", fields=["name", "warehouse_type"], limit=10)
    for wh in warehouses:
        print(f"   - {wh.name} (Type: {wh.warehouse_type or 'Not Set'})")

if __name__ == "__main__":
    execute()
