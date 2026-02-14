import frappe
import json

def execute():
    print("🚀 بدء إصلاح Workspace (v2)...")

    # 1. تنظيف عميق للـ Workspaces المكررة أو القديمة
    workspaces_to_delete = frappe.get_all("Workspace", filters={"module": "Smartplan Medical"})
    for ws in workspaces_to_delete:
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف Workspace قديم: {ws.name}")
    
    # حذف أي تخصيصات شخصية (Customizations) قد تخفي الـ Workspace الأصلي
    # (Checking for 'Workspace' docs where module is NOT 'Smartplan Medical' but name is target)
    personal_ws = frappe.get_all("Workspace", filters={"name": "Pharma Cycle Management"})
    for ws in personal_ws:
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف تخصيص شخصي: {ws.name}")

    frappe.db.commit()

    # 2. إنشاء Number Cards بسيطة ومضمونة
    print("\n📊 إنشاء Number Cards (Simple Configuration)...")
    
    # قائمة الكروت - سنستخدم فلاتر بسيطة جداً في البداية للتأكد من الظهور
    cards_config = [
        # Sales
        ("Draft Sales Orders", "طلبات مسودة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Draft",false]]', "#FFC107"),
         
        ("Approved Sales Orders", "طلبات معتمدة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Approved",false]]', "#4CAF50"),

        # Stock
        ("Completed Dispatches", "عمليات صرف", "Warehouse Dispatch", 
         '[["Warehouse Dispatch","docstatus","=","1",false]]', "#2196F3"),

        # Finance
        ("Today Collections", "تحصيلات اليوم", "Customer Payment", 
         '[["Customer Payment","posting_date","=","Today",false]]', "#4CAF50"),

        ("Today Supplier Payments", "مدفوعات موردين اليوم", "Supplier Payment", 
         '[["Supplier Payment","posting_date","=","Today",false]]', "#F44336"),

        # System
        ("Active Cashboxes", "صناديق نشطة", "Cashbox", 
         '[["Cashbox","is_active","=","1",false]]', "#FF9800"),
    ]

    for name, label, doctype, filters, color in cards_config:
        # حذف القديم
        if frappe.db.exists("Number Card", name):
            frappe.delete_doc("Number Card", name, force=1)

        # إنشاء الجديد
        nc = frappe.new_doc("Number Card")
        nc.name = name
        nc.label = label
        nc.module = "Smartplan Medical"  # Important!
        nc.document_type = doctype
        nc.type = "Document Type"
        nc.function = "Count"
        nc.aggregate_function_based_on = "" # Not needed for count
        nc.filters_json = filters
        nc.is_public = 1
        nc.is_standard = 1 # Force standard
        nc.show_percentage_stats = 1
        nc.stats_time_interval = "Daily"
        nc.color = color
        
        try:
            nc.insert(ignore_permissions=True)
            print(f"   ✅ تم إنشاء الكارت: {label}")
        except Exception as e:
            print(f"   ⚠️ فشل إنشاء {label}: {str(e)}")

    frappe.db.commit()

    # 3. إنشاء Workspace بسيط ومباشر
    print("\n🏢 إنشاء Workspace...")
    
    ws = frappe.new_doc("Workspace")
    ws.name = "Pharma Cycle Management"
    ws.label = "Pharma Cycle Management"
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.public = 1
    ws.is_hidden = 0
    ws.extends_another_page = 0
    ws.is_standard = 1 # Force standard
    
    # بناء المحتوى
    content = [
        {"type": "header", "data": {"text": "📊 مؤشرات الأداء", "col": 12}},
        
        # الصف الأول من الكروت
        {"type": "card", "data": {"card_name": "Draft Sales Orders", "col": 4}},
        {"type": "card", "data": {"card_name": "Approved Sales Orders", "col": 4}},
        {"type": "card", "data": {"card_name": "Completed Dispatches", "col": 4}},
        
        # الصف الثاني
        {"type": "card", "data": {"card_name": "Today Collections", "col": 4}},
        {"type": "card", "data": {"card_name": "Today Supplier Payments", "col": 4}},
        {"type": "card", "data": {"card_name": "Active Cashboxes", "col": 4}},
        
        {"type": "spacer", "data": {"col": 12}},

        # Shortcuts
        {"type": "header", "data": {"text": "⚡ وصول سريع", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Tele Sales Order", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Customer Payment", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Warehouse Dispatch", "col": 4}},
    ]
    
    ws.content = json.dumps(content)
    
    # إضافة Shortcuts للربط (مهم عشان تظهر في القائمة)
    ws.append("shortcuts", {
        "type": "DocType",
        "link_to": "Tele Sales Order",
        "label": "أوامر البيع",
        "color": "Blue"
    })
    ws.append("shortcuts", {
        "type": "DocType",
        "link_to": "Customer Payment",
        "label": "التحصيلات",
        "color": "Green"
    })
    ws.append("shortcuts", {
        "type": "DocType",
        "link_to": "Warehouse Dispatch",
        "label": "صرف مخزني",
        "color": "Orange"
    })

    try:
        ws.insert(ignore_permissions=True)
        print(f"✅ تم إنشاء Workspace بنجاح!")
    except Exception as e:
        print(f"❌ فشل إنشاء Workspace: {str(e)}")

    frappe.db.commit()
    
    # Clear Cache
    print("🧹 تنظيف الكاش...")
    frappe.clear_cache()
    print("✅ تم الانتهاء.")

