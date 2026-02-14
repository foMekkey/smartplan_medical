import frappe
import json

def execute():
    """
    إصلاح مشكلة عدم ظهور الموردين بإضافة shortcuts المفقودة
    """
    print("🔧 إصلاح shortcuts الموردين...")
    
    # Get workspace
    ws_name = "إدارة دورة شركة الأدوية"
    if not frappe.db.exists("Workspace", ws_name):
        print(f"❌ الـ Workspace '{ws_name}' غير موجود")
        return
    
    ws = frappe.get_doc("Workspace", ws_name)
    
    # Get existing shortcut labels
    existing_labels = {s.label for s in ws.shortcuts}
    print(f"\n📋 الاختصارات الموجودة ({len(existing_labels)}):")
    for label in sorted(existing_labels):
        print(f"   - {label}")
    
    # Shortcuts that need to be added
    needed_shortcuts = [
        ("Pharma Supplier", "قائمة الموردين", "Orange", "DocType"),
        ("Pharma Purchase Cycle", "دورة الشراء", "Blue", "DocType"),
        ("Supplier Aging Report", "تقرير أعمار الموردين", "Orange", "Report"),
    ]
    
    print(f"\n✨ إضافة الاختصارات المفقودة...")
    added = 0
    
    for link_to, label, color, link_type in needed_shortcuts:
        # Skip if already exists
        if label in existing_labels:
            print(f"   ⏭️ موجود بالفعل: {label}")
            continue
        
        # Check if target exists
        if not frappe.db.exists(link_type, link_to):
            print(f"   ⚠️ تخطي {label}: {link_type} '{link_to}' غير موجود")
            continue
        
        # Add shortcut
        ws.append("shortcuts", {
            "type": link_type,
            "link_to": link_to,
            "label": label,
            "doc_view": "List" if link_type == "DocType" else "",
            "color": color
        })
        print(f"   ✅ تمت الإضافة: {label} -> {link_to}")
        added += 1
    
    if added > 0:
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.clear_cache()
        print(f"\n✅ تم إضافة {added} اختصار جديد")
        print("🔄 الآن: افتح المتصفح واضغط Ctrl+Shift+R لتحديث الصفحة")
    else:
        print("\n✅ جميع الاختصارات موجودة بالفعل")
    
    # Verify
    print(f"\n🔍 التحقق النهائي...")
    ws.reload()
    supplier_shortcuts = [s for s in ws.shortcuts if "مورد" in s.label.lower() or "supplier" in s.link_to.lower()]
    print(f"   اختصارات الموردين: {len(supplier_shortcuts)}")
    for s in supplier_shortcuts:
        print(f"      ✓ {s.label} → {s.link_to}")

if __name__ == "__main__":
    execute()
