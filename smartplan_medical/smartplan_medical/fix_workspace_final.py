import frappe
import json

def execute():
    print("🚀 بدء إصلاح Workspace (Final Version)...")

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
    print("\n📊 إنشاء Number Cards (Full Configuration)...")
    
    # (KeyName, Label, DocType, Filters, Color)
    cards_config = [
        ("Draft Sales Orders", "طلبات مسودة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Draft",false]]', "#ffc107"),

        ("Pending Approval Orders", "طلبات تنتظر الموافقة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Pending Approval",false]]', "#ff9800"),

        ("Approved Sales Orders", "طلبات معتمدة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Approved",false]]', "#4caf50"),

        ("Completed Dispatches", "عمليات الصرف المنفذة", "Warehouse Dispatch", 
         '[["Warehouse Dispatch","docstatus","=","1",false]]', "#2196f3"),

        ("Completed Collections", "عمليات التحصيل المنفذة", "Delivery Collection", 
         '[["Delivery Collection","docstatus","=","1",false]]', "#9c27b0"),

        ("Failed Processes", "عمليات فاشلة", "Pharma Process Log", 
         '[["Pharma Process Log","status","=","Failed",false]]', "#f44336"),

        ("Pending Approvals", "موافقات معلقة", "Pharma Approval Request", 
         '[["Pharma Approval Request","status","=","Pending",false]]', "#ff5722"),

        # Finance
        ("Today Collections", "تحصيلات اليوم", "Customer Payment", 
         '[["Customer Payment","posting_date","=","Today",false],["Customer Payment","docstatus","=","1",false]]', "#4caf50"),

        ("Today Supplier Payments", "مدفوعات الموردين اليوم", "Supplier Payment", 
         '[["Supplier Payment","posting_date","=","Today",false],["Supplier Payment","docstatus","=","1",false]]', "#f44336"),

        ("Active Cashboxes", "الصناديق النشطة", "Cashbox", 
         '[["Cashbox","is_active","=","1",false]]', "#ff9800"),

        ("Pending Daily Closings", "إغلاقات معلقة", "Daily Closing", 
         '[["Daily Closing","docstatus","=","0",false]]', "#9c27b0"),
    ]

    card_name_map = {} 

    for config_name, label, doctype, filters, color in cards_config:
        # Try to delete by label slug or config name just in case
        possible_names = [config_name, label]
        for pname in possible_names:
             if frappe.db.exists("Number Card", pname):
                frappe.delete_doc("Number Card", pname, force=1)

        nc = frappe.new_doc("Number Card")
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
            card_name_map[config_name] = real_name
            print(f"   ✅ تم إنشاء الكارت: {label} -> {real_name}")
        except Exception as e:
            print(f"   ⚠️ فشل إنشاء {label}: {str(e)[:100]}")
            card_name_map[config_name] = None

    frappe.db.commit()

    # 3. إنشاء Workspace
    print("\n🏢 إنشاء Workspace...")
    
    ws = frappe.new_doc("Workspace")
    ws.name = "Pharma Cycle Management"
    # Title and label in Arabic as requested
    ws.label = "إدارة دورة شركة الأدوية"
    ws.title = "إدارة دورة شركة الأدوية"
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.public = 1
    ws.is_hidden = 0
    ws.extends_another_page = 0
    ws.is_standard = 1
    
    def get_card_name(config_key):
        return card_name_map.get(config_key)

    # 4. Content JSON
    content = [
        # ═══════════════════════════════════════════════════════════════
        # 📊 لوحة الحالات التشغيلية
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "📊 لوحة الحالات التشغيلية", "col": 12}},
        {"type": "card", "data": {"card_name": get_card_name("Draft Sales Orders"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Pending Approval Orders"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Approved Sales Orders"), "col": 4}},
        # New Row
        {"type": "card", "data": {"card_name": get_card_name("Completed Dispatches"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Completed Collections"), "col": 4}},
        {"type": "card", "data": {"card_name": get_card_name("Failed Processes"), "col": 4}},
        
        # Original Shortcuts
        {"type": "shortcut", "data": {"shortcut_name": "طلبات التلي سيلز", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "إذن صرف مخزن", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "التوصيل والتحصيل", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير الحالات التشغيلية", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # ⚠️ لوحة الحالات الاستثنائية
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "⚠️ لوحة الحالات الاستثنائية", "col": 12}},
        {"type": "card", "data": {"card_name": get_card_name("Pending Approvals"), "col": 6}},
        {"type": "card", "data": {"card_name": get_card_name("Failed Processes"), "col": 6}}, # Reusing Failed Processes card logic
        
        {"type": "shortcut", "data": {"shortcut_name": "لوحة الاستثناءات", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "سجل العمليات", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "طلبات الموافقة", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير المخزون قرب الانتهاء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير المخزون المنتهي", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير التحصيلات المتأخرة", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # 📅 الإغلاق اليومي
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "📅 الإغلاق اليومي والمالي", "col": 12}},
        {"type": "card", "data": {"card_name": get_card_name("Pending Daily Closings"), "col": 3}},
        {"type": "card", "data": {"card_name": get_card_name("Today Collections"), "col": 3}},
        {"type": "card", "data": {"card_name": get_card_name("Today Supplier Payments"), "col": 3}},
        {"type": "card", "data": {"card_name": get_card_name("Active Cashboxes"), "col": 3}},
        
        {"type": "shortcut", "data": {"shortcut_name": "تقرير الإغلاق اليومي", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير الصرف والتحصيل", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # 📋 الملكية التشغيلية
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "📋 الملكية التشغيلية والمسؤوليات", "col": 12}},
        {"type": "paragraph", "data": {"text": "<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'><table style='width:100%; color: white; font-size: 14px;'><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>🎯 Tele Sales</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>أوامر البيع + طلبات الموافقة على الخصومات</td></tr><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>📦 إدارة المخازن</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>صرف المخزن + FEFO + مراقبة الصلاحية</td></tr><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>🚚 مندوبي التوصيل</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>التوصيل + التحصيل + التسوية</td></tr><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>💰 الإدارة المالية</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>العمولات + الموافقات + التسويات</td></tr><tr><td style='padding: 10px;'><b>👔 الإدارة العليا</b></td><td style='padding: 10px;'>التقارير + المتابعة + القرارات</td></tr></table></div>", "col": 12}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # 🔒 القواعد الصارمة
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "🔒 القواعد الصارمة (Hard Rules)", "col": 12}},
        {"type": "paragraph", "data": {"text": "<div style='background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); padding: 20px; border-radius: 12px; color: #333; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'><table style='width:100%; font-size: 14px;'><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>🏷️ <b>أقصى خصم بدون موافقة</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>محدد في إعدادات سير العمل</code></td></tr><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>📅 <b>سياسة FEFO</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>First Expiry First Out - إلزامي</code></td></tr><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>⏰ <b>الحد الأدنى قبل الانتهاء</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>30 يوم على الأقل</code></td></tr><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>🚫 <b>منع المخزون السالب</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>ممنوع - لا يمكن الصرف بدون رصيد</code></td></tr><tr><td style='padding: 8px;'>🔐 <b>منع التعديل بعد الاعتماد</b></td><td style='padding: 8px; text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>المستندات المعتمدة للقراءة فقط</code></td></tr></table></div>", "col": 12}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # عمليات البيع
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "🛒 عمليات البيع", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "طلبات التلي سيلز", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "إذن صرف مخزن", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "التوصيل والتحصيل", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # إدارة المخازن
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "📦 إدارة المخازن", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "المخازن", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "الأصناف الدوائية", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # العملاء والمبيعات
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "👥 العملاء والمبيعات", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "العملاء", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "فريق المبيعات", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "حساب العمولات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # التوصيل
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "🚚 التوصيل", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "خطوط التوصيل", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "مندوبي التوصيل", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "السيارات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # سير العمل والموافقات
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "✅ سير العمل والموافقات", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "طلبات الموافقة", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "مصفوفة الموافقات", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "سجل العمليات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # التقارير
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "📈 التقارير", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير المبيعات بالموظف", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير تحليل الخصومات", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير العمولات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # 💰 الإدارة المالية - العملاء
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "💰 الإدارة المالية - العملاء", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "تحصيلات العملاء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "كشف حساب عميل", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "أعمار مديونيات العملاء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "التحصيلات اليومية", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # 💳 الإدارة المالية - الموردين
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "💳 الإدارة المالية - الموردين", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "مدفوعات الموردين", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "كشف حساب مورد", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "أعمار مستحقات الموردين", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # 🏦 إدارة النقدية والبنوك
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "🏦 إدارة النقدية والبنوك", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "الصناديق", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "حركات النقدية", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "الإغلاق اليومي للصندوق", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "دفتر النقدية", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "ملخص الصناديق", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "حركات البنك", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "كشف حساب بنكي", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        # ═══════════════════════════════════════════════════════════════
        # الإعدادات
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "⚙️ الإعدادات", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "الإعدادات العامة", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "إعدادات سير العمل", "col": 4}},
    ]
    
    # Clean content to remove null cards if any failed
    clean_content = []
    for item in content:
        if item["type"] == "card":
             if item["data"].get("card_name"):
                 clean_content.append(item)
        else:
            clean_content.append(item)

    ws.content = json.dumps(clean_content)

    # 5. Shortcuts
    shortcuts_config = [
        # ═══════════════════════════════════════════════════════════════
        # 📊 لوحة الحالات التشغيلية
        # ═══════════════════════════════════════════════════════════════
        ("Operational Status Report", "تقرير الحالات التشغيلية", "Blue", "Report"),
        
        # ═══════════════════════════════════════════════════════════════
        # ⚠️ لوحة الحالات الاستثنائية
        # ═══════════════════════════════════════════════════════════════
        ("Exception Dashboard Report", "لوحة الاستثناءات", "Red", "Report"),
        
        # ═══════════════════════════════════════════════════════════════
        # 📅 الإغلاق اليومي
        # ═══════════════════════════════════════════════════════════════
        ("Daily Closing Report", "تقرير الإغلاق اليومي", "Purple", "Report"),
    # Additional module-specific DocTypes (ensure custom doctypes are visible)
    ("Pharma Supplier", "الموردين", "Orange", "DocType"),
    ("Pharma Purchase Cycle", "دورة الشراء", "Orange", "DocType"),
    ("Pharma Purchase Cycle Item", "أصناف دورة الشراء", "Orange", "DocType"),
    ("Pharma Item Price History", "سجل أسعار الأصناف", "Blue", "DocType"),
    ("Pharma Audit Log Entry", "سجل التدقيق", "Grey", "DocType"),
    ("Pharma Warehouse", "المخازن الدوائية", "Blue", "DocType"),
        
        # ═══════════════════════════════════════════════════════════════
        # عمليات البيع
        # ═══════════════════════════════════════════════════════════════
        ("Tele Sales Order", "طلبات التلي سيلز", "Red", "DocType"),
        ("Warehouse Dispatch", "إذن صرف مخزن", "Orange", "DocType"),
        ("Delivery Collection", "التوصيل والتحصيل", "Green", "DocType"),
        
        # ═══════════════════════════════════════════════════════════════
        # إدارة المخازن
        # ═══════════════════════════════════════════════════════════════
        ("Pharma Warehouse", "المخازن", "Blue", "DocType"),
        ("Pharma Item", "الأصناف الدوائية", "Purple", "DocType"),
        
        # ═══════════════════════════════════════════════════════════════
        # العملاء والمبيعات
        # ═══════════════════════════════════════════════════════════════
        ("Pharma Customer", "العملاء", "Green", "DocType"),
        ("Tele Sales Team", "فريق المبيعات", "Orange", "DocType"),
        ("Commission Calculation", "حساب العمولات", "Blue", "DocType"),
        
        # ═══════════════════════════════════════════════════════════════
        # التوصيل
        # ═══════════════════════════════════════════════════════════════
        ("Delivery Route", "خطوط التوصيل", "Yellow", "DocType"),
        ("Delivery Representative", "مندوبي التوصيل", "Cyan", "DocType"),
        ("Delivery Vehicle", "السيارات", "Grey", "DocType"),
        
        # ═══════════════════════════════════════════════════════════════
        # سير العمل والموافقات
        # ═══════════════════════════════════════════════════════════════
        ("Pharma Approval Request", "طلبات الموافقة", "Red", "DocType"),
        ("Pharma Approval Matrix", "مصفوفة الموافقات", "Orange", "DocType"),
        ("Pharma Process Log", "سجل العمليات", "Blue", "DocType"),
        
        # ═══════════════════════════════════════════════════════════════
        # التقارير
        # ═══════════════════════════════════════════════════════════════
        ("Expiring Stock Report", "تقرير المخزون قرب الانتهاء", "Yellow", "Report"),
        ("Expired Stock Report", "تقرير المخزون المنتهي", "Red", "Report"),
        ("Sales By Employee Report", "تقرير المبيعات بالموظف", "Green", "Report"),
        ("Discount Analysis Report", "تقرير تحليل الخصومات", "Orange", "Report"),
        ("Dispatch vs Collection Report", "تقرير الصرف والتحصيل", "Blue", "Report"),
        ("Overdue Collections Report", "تقرير التحصيلات المتأخرة", "Red", "Report"),
        ("Commission Report", "تقرير العمولات", "Purple", "Report"),
        
        # ═══════════════════════════════════════════════════════════════
        # الإعدادات
        # ═══════════════════════════════════════════════════════════════
        ("Pharma General Settings", "الإعدادات العامة", "Pink", "DocType"),
        ("Pharma Workflow Settings", "إعدادات سير العمل", "Grey", "DocType"),
        
        # ═══════════════════════════════════════════════════════════════
        # 💰 الإدارة المالية - العملاء
        # ═══════════════════════════════════════════════════════════════
        ("Customer Payment", "تحصيلات العملاء", "Green", "DocType"),
        ("Customer Statement", "كشف حساب عميل", "Blue", "Report"),
        ("Customer Aging Report", "أعمار مديونيات العملاء", "Orange", "Report"),
        ("Daily Collections", "التحصيلات اليومية", "Cyan", "Report"),
        
        # ═══════════════════════════════════════════════════════════════
        # 💳 الإدارة المالية - الموردين
        # ═══════════════════════════════════════════════════════════════
        ("Supplier Payment", "مدفوعات الموردين", "Red", "DocType"),
        ("Supplier Statement", "كشف حساب مورد", "Blue", "Report"),
        ("Supplier Aging Report", "أعمار مستحقات الموردين", "Orange", "Report"),
        
        # ═══════════════════════════════════════════════════════════════
        # 🏦 إدارة النقدية والبنوك
        # ═══════════════════════════════════════════════════════════════
        ("Cashbox", "الصناديق", "Yellow", "DocType"),
        ("Cash Transaction", "حركات النقدية", "Green", "DocType"),
        ("Daily Closing", "الإغلاق اليومي للصندوق", "Purple", "DocType"),
        ("Cashbox Ledger", "دفتر النقدية", "Blue", "Report"),
        ("Cashbox Summary", "ملخص الصناديق", "Cyan", "Report"),
        ("Bank Transaction Entry", "حركات البنك", "Blue", "DocType"),
        ("Bank Statement", "كشف حساب بنكي", "Green", "Report"),
    ]

    for link_to, label, color, link_type in shortcuts_config:
        # Safety: only add shortcut if the target DocType/Report exists
        try:
            if link_type == "DocType":
                if not frappe.db.exists("DocType", link_to):
                    print(f"⚠️ تخطي الاختصار '{label}': DocType {link_to} غير موجود")
                    continue
            elif link_type == "Report":
                if not frappe.db.exists("Report", link_to):
                    print(f"⚠️ تخطي الاختصار '{label}': Report {link_to} غير موجود")
                    continue

            ws.append("shortcuts", {
                "type": link_type,
                "link_to": link_to,
                "label": label,
                "doc_view": "List" if link_type == "DocType" else "",
                "color": color
            })
        except Exception as e:
            print(f"⚠️ فشل التحقق/الإضافة للاختصار {label}: {str(e)[:120]}")

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
