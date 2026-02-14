import frappe
import json

def execute():
    print("🚀 بدء إصلاح Workspace (v3)...")

    # 1. تنظيف عميق للـ Workspaces
    workspaces_to_delete = frappe.get_all("Workspace", filters={"module": "Smartplan Medical"})
    for ws in workspaces_to_delete:
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف Workspace قديم: {ws.name}")
    
    personal_ws = frappe.get_all("Workspace", filters={"name": "Pharma Cycle Management"})
    for ws in personal_ws:
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف تخصيص شخصي: {ws.name}")

    frappe.db.commit()

    # 2. إنشاء Number Cards وجمع الأسماء الحقيقية
    print("\n📊 إنشاء Number Cards (Simple Configuration)...")
    
    # قائمة الكروت
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

    card_name_map = {} # To store the actual name created vs config name

    for config_name, label, doctype, filters, color in cards_config:
        # حذف القديم إذا أمكن (باستخدام الاسم العربي المتوقع أيضاً)
        possible_names = [config_name, label]
        for pname in possible_names:
             if frappe.db.exists("Number Card", pname):
                frappe.delete_doc("Number Card", pname, force=1)

        # إنشاء الجديد
        nc = frappe.new_doc("Number Card")
        # لا نحدد الاسم يدوياً هنا، نترك النظام يختار أو نستخدمه إذا قبل
        nc.label = label
        nc.module = "Smartplan Medical"
        nc.document_type = doctype
        nc.type = "Document Type"
        nc.function = "Count"
        nc.aggregate_function_based_on = ""
        nc.filters_json = filters
        nc.is_public = 1
        nc.is_standard = 1
        nc.show_percentage_stats = 1
        nc.stats_time_interval = "Daily"
        nc.color = color
        
        try:
            nc.insert(ignore_permissions=True)
            real_name = nc.name
            card_name_map[config_name] = real_name # Map config name to real created name
            print(f"   ✅ تم إنشاء الكارت: {label} (الاسم الحقيقي: {real_name})")
        except Exception as e:
            print(f"   ⚠️ فشل إنشاء {label}: {str(e)}")
            card_name_map[config_name] = None

    frappe.db.commit()

    # 3. إنشاء Workspace مع استخدام الأسماء الحقيقية للكروت
    print("\n🏢 إنشاء Workspace...")
    
    ws = frappe.new_doc("Workspace")
    ws.name = "Pharma Cycle Management"
    ws.label = "Pharma Cycle Management"
    ws.title = "Pharma Cycle Management" # Added Title
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.public = 1
    ws.is_hidden = 0
    ws.extends_another_page = 0
    ws.is_standard = 1
    
    # Helper to get real name safely
    def get_card_name(config_key):
        return card_name_map.get(config_key)

    # بناء المحتوى
    content = [
        {"type": "header", "data": {"text": "📊 مؤشرات الأداء", "col": 12}},
        
        # الصف الأول
        {"type": "card", "data": {"card_name": get_card_name("Draft Sales Orders"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Approved Sales Orders"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Completed Dispatches"), "col": 4}},
        
        # الصف الثاني
        {"type": "card", "data": {"card_name": get_card_name("Today Collections"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Today Supplier Payments"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Active Cashboxes"), "col": 4}},
        
        {"type": "spacer", "data": {"col": 12}},

        # Shortcuts
        {"type": "header", "data": {"text": "⚡ وصول سريع", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Tele Sales Order", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Customer Payment", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Warehouse Dispatch", "col": 4}},
    ]
    
    # Filter out None cards if any failed
    # content = [item for item in content if item.get("data", {}).get("card_name") is not None or item["type"] != "card"]
    # Actually, keep simpler logic: if name is None, card won't show but script won't crash if handled gracefully by frappe.
    # But let's remove None cards to be clean.
    clean_content = []
    for item in content:
        if item["type"] == "card":
             if item["data"].get("card_name"):
                 clean_content.append(item)
        else:
            clean_content.append(item)

    ws.content = json.dumps(clean_content)
    
    # إضافة Shortcuts
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
