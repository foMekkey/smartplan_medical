import frappe
import json

def execute():
    """
    إضافة قسم خاص بالموردين في بداية الـ Workspace
    """
    print("🔧 إضافة قسم الموردين بشكل واضح...")
    
    ws = frappe.get_doc("Workspace", "إدارة دورة شركة الأدوية")
    
    # Parse content
    content = json.loads(ws.content)
    
    # Add Suppliers section at the beginning (after dashboard cards)
    suppliers_section = [
        {"type": "header", "data": {"text": "🏭 إدارة الموردين", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "قائمة الموردين", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "دورة الشراء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "مدفوعات الموردين", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير أعمار الموردين", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
    ]
    
    # Find position after first spacer (after cards)
    insert_pos = 0
    for i, item in enumerate(content):
        if item.get("type") == "spacer":
            insert_pos = i + 1
            break
    
    # Insert suppliers section
    for i, section_item in enumerate(suppliers_section):
        content.insert(insert_pos + i, section_item)
    
    ws.content = json.dumps(content)
    
    # Add shortcuts if not exist
    shortcut_configs = [
        ("Pharma Supplier", "قائمة الموردين", "Orange", "DocType"),
        ("Pharma Purchase Cycle", "دورة الشراء", "Blue", "DocType"),
        ("Supplier Payment", "مدفوعات الموردين", "Red", "DocType"),
        ("Supplier Aging Report", "تقرير أعمار الموردين", "Orange", "Report"),
    ]
    
    for link_to, label, color, link_type in shortcut_configs:
        # Check if already exists
        exists = any(s.link_to == link_to for s in ws.shortcuts)
        if not exists and frappe.db.exists(link_type, link_to):
            ws.append("shortcuts", {
                "type": link_type,
                "link_to": link_to,
                "label": label,
                "doc_view": "List" if link_type == "DocType" else "",
                "color": color
            })
            print(f"   ✅ تمت إضافة: {label}")
    
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    
    print("\n✅ تم إضافة قسم الموردين بنجاح!")
    print("🔄 حدّث المتصفح الآن (Ctrl+Shift+R)")

if __name__ == "__main__":
    execute()
