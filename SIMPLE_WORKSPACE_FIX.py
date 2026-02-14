# كود تحديث Workspace الاحترافي - Enterprise Grade
# يتضمن لوحات الحالات التشغيلية والاستثنائية والإغلاق اليومي
# انسخه كله وشغله في Console

import frappe
import json

def execute():
    print("=" * 70)
    print("🏢 جاري إنشاء Workspace احترافي لإدارة دورة شركة الأدوية...")
    print("=" * 70)

    # 1) حذف كل الـ Workspaces القديمة للموديول
    for ws in frappe.get_all("Workspace", filters={"module": "Smartplan Medical"}):
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف: {ws.name}")

    # حذف أي workspace اسمه عربي أو Pharma
    for ws in frappe.get_all("Workspace"):
        if "دور" in ws.name or "أدوية" in ws.name or "ادار" in ws.name or "Pharma" in ws.name:
            if ws.module == "Smartplan Medical": # Safety check
                frappe.delete_doc("Workspace", ws.name, force=1)
                print(f"🗑️ تم حذف: {ws.name}")

    frappe.db.commit()

    # 2) إنشاء Number Cards *أولاً* - هذه الخطوة مهمة جداً قبل الـ Workspace
    print("\n📊 جاري إنشاء Number Cards...")

    number_cards = [
        {
            "name": "Draft Sales Orders",
            "label": "طلبات مسودة",
            "document_type": "Tele Sales Order",
            "filters_json": '[["Tele Sales Order","status","=","Draft",false]]',
            "color": "#ffc107"
        },
        {
            "name": "Pending Approval Orders",
            "label": "طلبات تنتظر الموافقة",
            "document_type": "Tele Sales Order",
            "filters_json": '[["Tele Sales Order","status","=","Pending Approval",false]]',
            "color": "#ff9800"
        },
        {
            "name": "Approved Sales Orders",
            "label": "طلبات معتمدة",
            "document_type": "Tele Sales Order",
            "filters_json": '[["Tele Sales Order","status","=","Approved",false]]',
            "color": "#4caf50"
        },
        {
            "name": "Completed Dispatches",
            "label": "عمليات الصرف المنفذة",
            "document_type": "Warehouse Dispatch",
            "filters_json": '[["Warehouse Dispatch","docstatus","=","1",false]]',
            "color": "#2196f3"
        },
        {
            "name": "Completed Collections",
            "label": "عمليات التحصيل المنفذة",
            "document_type": "Delivery Collection",
            "filters_json": '[["Delivery Collection","docstatus","=","1",false]]',
            "color": "#9c27b0"
        },
        {
            "name": "Failed Processes",
            "label": "عمليات فاشلة",
            "document_type": "Pharma Process Log",
            "filters_json": '[["Pharma Process Log","status","=","Failed",false]]',
            "color": "#f44336"
        },
        {
            "name": "Pending Approvals",
            "label": "موافقات معلقة",
            "document_type": "Pharma Approval Request",
            "filters_json": '[["Pharma Approval Request","status","=","Pending",false]]',
            "color": "#ff5722"
        },
        # ═══════════════════════════════════════════════════════════════
        # 💰 Number Cards المالية
        # ═══════════════════════════════════════════════════════════════
        {
            "name": "Today Collections",
            "label": "تحصيلات اليوم",
            "document_type": "Customer Payment",
            "filters_json": '[["Customer Payment","posting_date","=","Today",false],["Customer Payment","docstatus","=","1",false]]',
            "color": "#4caf50"
        },
        {
            "name": "Today Supplier Payments",
            "label": "مدفوعات الموردين اليوم",
            "document_type": "Supplier Payment",
            "filters_json": '[["Supplier Payment","posting_date","=","Today",false],["Supplier Payment","docstatus","=","1",false]]',
            "color": "#f44336"
        },
        {
            "name": "Active Cashboxes",
            "label": "الصناديق النشطة",
            "document_type": "Cashbox",
            "filters_json": '[["Cashbox","is_active","=","1",false]]',
            "color": "#ff9800"
        },
        {
            "name": "Pending Daily Closings",
            "label": "إغلاقات معلقة",
            "document_type": "Daily Closing",
            "filters_json": '[["Daily Closing","docstatus","=","0",false]]',
            "color": "#9c27b0"
        },
    ]

    for nc_config in number_cards:
        # حذف القديم إن وجد
        if frappe.db.exists("Number Card", nc_config["name"]):
            frappe.delete_doc("Number Card", nc_config["name"], force=1)
        
        nc = frappe.new_doc("Number Card")
        nc.name = nc_config["name"]
        nc.label = nc_config["label"]
        nc.document_type = nc_config["document_type"]
        nc.filters_json = nc_config["filters_json"]
        nc.function = "Count"
        nc.is_public = 1
        nc.is_standard = 0
        nc.show_percentage_stats = 1
        nc.stats_time_interval = "Daily"
        nc.type = "Document Type"
        nc.color = nc_config.get("color")
        try:
            nc.insert(ignore_permissions=True)
            print(f"   ✅ {nc_config['label']}")
        except Exception as e:
            print(f"   ⚠️ {nc_config['label']}: {str(e)[:50]}")

    frappe.db.commit()


    # 3) إنشاء Workspace جديد باسم إنجليزي وتضمين الكروت في الـ Content
    ws = frappe.new_doc("Workspace")
    ws.name = "Pharma Cycle Management"
    ws.label = "Pharma Cycle Management"
    ws.title = "Pharma Cycle Management"
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.public = 1
    ws.is_hidden = 0

    # 4) Content JSON الشامل - Enterprise Layout - مع الكروت (Number Cards)
    content = [
        # ═══════════════════════════════════════════════════════════════
        # 📊 لوحة الحالات التشغيلية
        # ═══════════════════════════════════════════════════════════════
        {"type": "header", "data": {"text": "📊 لوحة الحالات التشغيلية", "col": 12}},
        {"type": "card", "data": {"card_name": "Draft Sales Orders", "col": 4}},
        {"type": "card", "data": {"card_name": "Pending Approval Orders", "col": 4}},
        {"type": "card", "data": {"card_name": "Approved Sales Orders", "col": 4}},
        # New Row
        {"type": "card", "data": {"card_name": "Completed Dispatches", "col": 4}},
        {"type": "card", "data": {"card_name": "Completed Collections", "col": 4}},
        {"type": "card", "data": {"card_name": "Failed Processes", "col": 4}},
        
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
        {"type": "card", "data": {"card_name": "Pending Approvals", "col": 6}},
        {"type": "card", "data": {"card_name": "Failed Processes", "col": 6}},
        
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
        {"type": "card", "data": {"card_name": "Pending Daily Closings", "col": 3}},
        {"type": "card", "data": {"card_name": "Today Collections", "col": 3}},
        {"type": "card", "data": {"card_name": "Today Supplier Payments", "col": 3}},
        {"type": "card", "data": {"card_name": "Active Cashboxes", "col": 3}},
        
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
    ws.content = json.dumps(content)

    # 5) جميع الـ Shortcuts - شاملة الجديدة
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
        ws.append("shortcuts", {
            "type": link_type,
            "link_to": link_to,
            "label": label,
            "doc_view": "List" if link_type == "DocType" else "",
            "color": color
        })

    # 6) حفظ الـ Workspace
    ws.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"\n✅ تم إنشاء Workspace بنجاح: {ws.name}")

    # Clear cache after everything
    frappe.clear_cache()
