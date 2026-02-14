import frappe
import json

def execute():
    """
    Check if Pharma Supplier exists and add it to workspace shortcuts
    """
    print("🔍 فحص وجود الموردين...")
    
    # Check if Pharma Supplier DocType exists
    pharma_supplier_exists = frappe.db.exists("DocType", "Pharma Supplier")
    print(f"   Pharma Supplier موجود: {pharma_supplier_exists}")
    
    # List all Pharma-related DocTypes
    all_pharma = frappe.get_all(
        "DocType", 
        filters={
            "module": "Smartplan Medical",
            "istable": 0
        },
        fields=["name", "custom"]
    )
    
    print(f"\n📋 جميع Doctypes في الموديول ({len(all_pharma)}):")
    for dt in sorted(all_pharma, key=lambda x: x.name):
        print(f"   - {dt.name} (Custom: {dt.custom})")
    
    # Get current workspace
    if not frappe.db.exists("Workspace", "إدارة دورة شركة الأدوية"):
        print("\n⚠️ الـ Workspace غير موجود!")
        return
    
    ws = frappe.get_doc("Workspace", "إدارة دورة شركة الأدوية")
    
    # Check current shortcuts
    print(f"\n🔗 الاختصارات الحالية ({len(ws.shortcuts)}):")
    supplier_shortcuts = [s for s in ws.shortcuts if "مورد" in s.label or "Supplier" in s.label]
    print(f"   اختصارات الموردين: {len(supplier_shortcuts)}")
    for s in supplier_shortcuts:
        print(f"      - {s.label} -> {s.link_to}")
    
    # Add Pharma Supplier if missing and exists
    has_pharma_supplier = any(s.link_to == "Pharma Supplier" for s in ws.shortcuts)
    
    if pharma_supplier_exists and not has_pharma_supplier:
        print("\n✨ إضافة اختصار الموردين...")
        ws.append("shortcuts", {
            "type": "DocType",
            "link_to": "Pharma Supplier",
            "label": "الموردين الدوائية",
            "doc_view": "List",
            "color": "Orange"
        })
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        print("   ✅ تم إضافة الموردين بنجاح!")
    elif not pharma_supplier_exists:
        print("\n⚠️ DocType 'Pharma Supplier' غير موجود في النظام")
        print("   يجب تثبيت/إنشاء الـ DocType أولاً")
    else:
        print("\n✅ اختصار الموردين موجود بالفعل")
    
    frappe.clear_cache()
    print("\n✅ انتهى الفحص")

if __name__ == "__main__":
    execute()
