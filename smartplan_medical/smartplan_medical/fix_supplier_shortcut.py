import frappe
import json

def execute():
    """
    إصلاح مشكلة عدم ظهور اختصار الموردين - إضافة shortcut باسم "قائمة الموردين"
    """
    print("🔧 إصلاح اختصار الموردين...")
    
    ws = frappe.get_doc("Workspace", "إدارة دورة شركة الأدوية")
    
    # Check if "قائمة الموردين" shortcut exists
    has_supplier_list = any(s.label == "قائمة الموردين" for s in ws.shortcuts)
    
    if not has_supplier_list:
        print("   ➕ إضافة اختصار 'قائمة الموردين'...")
        ws.append("shortcuts", {
            "type": "DocType",
            "link_to": "Pharma Supplier",
            "label": "قائمة الموردين",
            "doc_view": "List",
            "color": "Orange"
        })
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        print("   ✅ تمت الإضافة بنجاح!")
    else:
        print("   ✅ الاختصار موجود بالفعل")
    
    # Also ensure other shortcuts in suppliers section exist
    supplier_shortcuts = [
        ("Pharma Purchase Cycle", "دورة الشراء", "Blue"),
        ("Supplier Payment", "مدفوعات الموردين", "Red"),
        ("Supplier Aging Report", "تقرير أعمار الموردين", "Orange"),
    ]
    
    for link_to, label, color in supplier_shortcuts:
        has_it = any(s.label == label for s in ws.shortcuts)
        if not has_it:
            # Determine type
            is_report = "Report" in link_to or "report" in label.lower() or "تقرير" in label
            link_type = "Report" if is_report else "DocType"
            
            if frappe.db.exists(link_type, link_to):
                ws.append("shortcuts", {
                    "type": link_type,
                    "link_to": link_to,
                    "label": label,
                    "doc_view": "" if is_report else "List",
                    "color": color
                })
                print(f"   ➕ أضيف: {label}")
    
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    
    print("\n✅ تم الإصلاح - حدّث المتصفح الآن (Ctrl+Shift+R)")

if __name__ == "__main__":
    execute()
