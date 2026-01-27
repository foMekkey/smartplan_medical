# كود تحديث Workspace الاحترافي - Enterprise Grade
# يتضمن لوحات الحالات التشغيلية والاستثنائية والإغلاق اليومي
# انسخه كله وشغله في Console

import frappe
import json

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
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف: {ws.name}")

frappe.db.commit()

# 2) إنشاء Workspace جديد باسم إنجليزي
ws = frappe.new_doc("Workspace")
ws.name = "Pharma Cycle Management"
ws.label = "Pharma Cycle Management"
ws.title = "Pharma Cycle Management"
ws.module = "Smartplan Medical"
ws.icon = "healthcare"
ws.public = 1
ws.is_hidden = 0

# 3) Content JSON الشامل - Enterprise Layout
content = [
    # ═══════════════════════════════════════════════════════════════
    # 📊 لوحة الحالات التشغيلية
    # ═══════════════════════════════════════════════════════════════
    {"type": "header", "data": {"text": "📊 لوحة الحالات التشغيلية", "col": 12}},
    {"type": "onboarding", "data": {"onboarding_name": "Pharma Operations Cards", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "طلبات التلي سيلز", "col": 3}},
    {"type": "shortcut", "data": {"shortcut_name": "إذن صرف مخزن", "col": 3}},
    {"type": "shortcut", "data": {"shortcut_name": "التوصيل والتحصيل", "col": 3}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير الحالات التشغيلية", "col": 3}},
    {"type": "spacer", "data": {"col": 12}},
    
    # ═══════════════════════════════════════════════════════════════
    # ⚠️ لوحة الحالات الاستثنائية
    # ═══════════════════════════════════════════════════════════════
    {"type": "header", "data": {"text": "⚠️ لوحة الحالات الاستثنائية", "col": 12}},
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
    {"type": "header", "data": {"text": "📅 الإغلاق اليومي", "col": 12}},
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
    # الإعدادات
    # ═══════════════════════════════════════════════════════════════
    {"type": "header", "data": {"text": "⚙️ الإعدادات", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "الإعدادات العامة", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "إعدادات سير العمل", "col": 4}},
]
ws.content = json.dumps(content)

# 4) جميع الـ Shortcuts - شاملة الجديدة
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
]

for link_to, label, color, link_type in shortcuts_config:
    ws.append("shortcuts", {
        "type": link_type,
        "link_to": link_to,
        "label": label,
        "doc_view": "List" if link_type == "DocType" else "",
        "color": color
    })

# 5) حفظ الـ Workspace أولاً بدون Number Cards
ws.insert(ignore_permissions=True)
frappe.db.commit()
print(f"\n✅ تم إنشاء Workspace: {ws.name}")

# 6) إنشاء Number Cards
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
]

print("\n📊 جاري إنشاء Number Cards...")
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

# 7) إضافة Number Cards للـ Workspace (بعد إنشائهم وحفظهم)
print("\n🔗 جاري ربط Number Cards بالـ Workspace...")
ws_doc = frappe.get_doc("Workspace", "Pharma Cycle Management")
for nc_config in number_cards:
    if frappe.db.exists("Number Card", nc_config["name"]):
        ws_doc.append("number_cards", {
            "number_card_name": nc_config["name"],
            "label": nc_config["label"]
        })
        print(f"   ✅ {nc_config['label']}")

ws_doc.save(ignore_permissions=True)
frappe.db.commit()
frappe.clear_cache()

print("\n" + "=" * 70)
print("🎉 تم بنجاح إنشاء Workspace احترافي!")
print("=" * 70)
print(f"📁 Workspace: Pharma Cycle Management")
print(f"🔗 Shortcuts: {len(ws.shortcuts)}")
print(f"📊 Number Cards: {len(number_cards)}")

print("\n" + "═" * 70)
print("📋 ملخص المكونات:")
print("═" * 70)
print("""
┌────────────────────────────────────────────────────────────────────┐
│  📊 لوحة الحالات التشغيلية                                        │
│     • Number Cards للطلبات (مسودة/معلقة/معتمدة)                   │
│     • عمليات الصرف والتحصيل                                       │
│     • تقرير الحالات التشغيلية                                     │
├────────────────────────────────────────────────────────────────────┤
│  ⚠️ لوحة الحالات الاستثنائية                                      │
│     • العمليات الفاشلة                                            │
│     • الموافقات المعلقة                                           │
│     • لوحة الاستثناءات التفصيلية                                  │
│     • تنبيهات المخزون                                             │
├────────────────────────────────────────────────────────────────────┤
│  📅 الإغلاق اليومي                                                │
│     • تقرير الإغلاق اليومي (صرف/تحصيل/فرق)                        │
│     • تقرير الصرف والتحصيل التفصيلي                               │
├────────────────────────────────────────────────────────────────────┤
│  📋 الملكية التشغيلية                                             │
│     • توزيع المسؤوليات على الأقسام                                │
├────────────────────────────────────────────────────────────────────┤
│  🔒 القواعد الصارمة                                               │
│     • أقصى خصم بدون موافقة                                        │
│     • سياسة FEFO                                                  │
│     • الحد الأدنى للصلاحية                                        │
│     • منع المخزون السالب                                          │
│     • منع التعديل بعد الاعتماد                                    │
└────────────────────────────────────────────────────────────────────┘
""")
print("=" * 70)
