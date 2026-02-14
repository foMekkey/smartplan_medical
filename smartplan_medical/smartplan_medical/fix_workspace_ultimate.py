import frappe
import json

def execute():
    print("🚀 الحل النهائي لمشكلة Number Cards...")

    # 1. تنظيف
    for ws in frappe.get_all("Workspace", filters={"name": "Pharma Cycle Management"}):
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف: {ws.name}")

    frappe.db.commit()

    # 2. إنشاء Number Cards بأسماء إنجليزية (مهم جداً!)
    print("\n📊 إنشاء Number Cards...")
    
    cards_config = [
        ("draft_sales_orders", "طلبات مسودة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Draft",false]]', "#ffc107"),
        ("pending_approval_orders", "طلبات تنتظر الموافقة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Pending Approval",false]]', "#ff9800"),
        ("approved_sales_orders", "طلبات معتمدة", "Tele Sales Order", 
         '[["Tele Sales Order","status","=","Approved",false]]', "#4caf50"),
        ("completed_dispatches", "عمليات الصرف المنفذة", "Warehouse Dispatch", 
         '[["Warehouse Dispatch","docstatus","=","1",false]]', "#2196f3"),
        ("completed_collections", "عمليات التحصيل المنفذة", "Delivery Collection", 
         '[["Delivery Collection","docstatus","=","1",false]]', "#9c27b0"),
        ("failed_processes", "عمليات فاشلة", "Pharma Process Log", 
         '[["Pharma Process Log","status","=","Failed",false]]', "#f44336"),
        ("pending_approvals", "موافقات معلقة", "Pharma Approval Request", 
         '[["Pharma Approval Request","status","=","Pending",false]]', "#ff5722"),
        ("today_collections", "تحصيلات اليوم", "Customer Payment", 
         '[["Customer Payment","posting_date","=","Today",false],["Customer Payment","docstatus","=","1",false]]', "#4caf50"),
        ("today_supplier_payments", "مدفوعات الموردين اليوم", "Supplier Payment", 
         '[["Supplier Payment","posting_date","=","Today",false],["Supplier Payment","docstatus","=","1",false]]', "#f44336"),
        ("active_cashboxes", "الصناديق النشطة", "Cashbox", 
         '[["Cashbox","is_active","=","1",false]]', "#ff9800"),
        ("pending_daily_closings", "إغلاقات معلقة", "Daily Closing", 
         '[["Daily Closing","docstatus","=","0",false]]', "#9c27b0"),
    ]

    created_cards = []

    for english_name, label, doctype, filters, color in cards_config:
        # حذف القديم
        if frappe.db.exists("Number Card", english_name):
            frappe.delete_doc("Number Card", english_name, force=1)

        nc = frappe.new_doc("Number Card")
        nc.name = english_name  # اسم إنجليزي
        nc.label = label
        nc.module = "Smartplan Medical"
        nc.document_type = doctype
        nc.type = "Document Type"
        nc.function = "Count"
        nc.filters_json = filters
        nc.is_public = 1
        nc.is_standard = 0  # مهم: custom cards
        nc.show_percentage_stats = 1
        nc.stats_time_interval = "Daily"
        nc.color = color
        
        try:
            nc.insert(ignore_permissions=True)
            created_cards.append(english_name)
            print(f"   ✅ {label} -> {english_name}")
        except Exception as e:
            print(f"   ⚠️ فشل {label}: {str(e)[:100]}")

    frappe.db.commit()

    # 3. إنشاء Workspace
    print("\n🏢 إنشاء Workspace...")
    
    ws = frappe.new_doc("Workspace")
    ws.name = "Pharma Cycle Management"
    ws.label = "Pharma Cycle Management"
    ws.title = "Pharma Cycle Management"
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.public = 1
    ws.is_hidden = 0
    ws.is_standard = 0  # custom workspace
    
    # 4. Content JSON (استخدام الأسماء الإنجليزية)
    content = [
        {"type": "header", "data": {"text": "📊 لوحة الحالات التشغيلية", "col": 12}},
        {"type": "card", "data": {"card_name": "draft_sales_orders", "col": 4}},
        {"type": "card", "data": {"card_name": "pending_approval_orders", "col": 4}},
        {"type": "card", "data": {"card_name": "approved_sales_orders", "col": 4}},
        {"type": "card", "data": {"card_name": "completed_dispatches", "col": 4}},
        {"type": "card", "data": {"card_name": "completed_collections", "col": 4}},
        {"type": "card", "data": {"card_name": "failed_processes", "col": 4}},
        
        {"type": "shortcut", "data": {"shortcut_name": "طلبات التلي سيلز", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "إذن صرف مخزن", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "التوصيل والتحصيل", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير الحالات التشغيلية", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "⚠️ لوحة الحالات الاستثنائية", "col": 12}},
        {"type": "card", "data": {"card_name": "pending_approvals", "col": 6}},
        {"type": "card", "data": {"card_name": "failed_processes", "col": 6}},
        
        {"type": "shortcut", "data": {"shortcut_name": "لوحة الاستثناءات", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "سجل العمليات", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "طلبات الموافقة", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير المخزون قرب الانتهاء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير المخزون المنتهي", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير التحصيلات المتأخرة", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "📅 الإغلاق اليومي والمالي", "col": 12}},
        {"type": "card", "data": {"card_name": "pending_daily_closings", "col": 3}},
        {"type": "card", "data": {"card_name": "today_collections", "col": 3}},
        {"type": "card", "data": {"card_name": "today_supplier_payments", "col": 3}},
        {"type": "card", "data": {"card_name": "active_cashboxes", "col": 3}},
        
        {"type": "shortcut", "data": {"shortcut_name": "تقرير الإغلاق اليومي", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير الصرف والتحصيل", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "📋 الملكية التشغيلية والمسؤوليات", "col": 12}},
        {"type": "paragraph", "data": {"text": "<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'><table style='width:100%; color: white; font-size: 14px;'><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>🎯 Tele Sales</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>أوامر البيع + طلبات الموافقة على الخصومات</td></tr><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>📦 إدارة المخازن</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>صرف المخزن + FEFO + مراقبة الصلاحية</td></tr><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>🚚 مندوبي التوصيل</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>التوصيل + التحصيل + التسوية</td></tr><tr><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'><b>💰 الإدارة المالية</b></td><td style='padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);'>العمولات + الموافقات + التسويات</td></tr><tr><td style='padding: 10px;'><b>👔 الإدارة العليا</b></td><td style='padding: 10px;'>التقارير + المتابعة + القرارات</td></tr></table></div>", "col": 12}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "🔒 القواعد الصارمة (Hard Rules)", "col": 12}},
        {"type": "paragraph", "data": {"text": "<div style='background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); padding: 20px; border-radius: 12px; color: #333; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'><table style='width:100%; font-size: 14px;'><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>🏷️ <b>أقصى خصم بدون موافقة</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>محدد في إعدادات سير العمل</code></td></tr><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>📅 <b>سياسة FEFO</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>First Expiry First Out - إلزامي</code></td></tr><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>⏰ <b>الحد الأدنى قبل الانتهاء</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>30 يوم على الأقل</code></td></tr><tr><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1);'>🚫 <b>منع المخزون السالب</b></td><td style='padding: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>ممنوع - لا يمكن الصرف بدون رصيد</code></td></tr><tr><td style='padding: 8px;'>🔐 <b>منع التعديل بعد الاعتماد</b></td><td style='padding: 8px; text-align: left;'><code style='background: #fff; padding: 3px 8px; border-radius: 4px;'>المستندات المعتمدة للقراءة فقط</code></td></tr></table></div>", "col": 12}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "🛒 عمليات البيع", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "طلبات التلي سيلز", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "إذن صرف مخزن", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "التوصيل والتحصيل", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "📦 إدارة المخازن", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "المخازن", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "الأصناف الدوائية", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "👥 العملاء والمبيعات", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "العملاء", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "فريق المبيعات", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "حساب العمولات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "🚚 التوصيل", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "خطوط التوصيل", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "مندوبي التوصيل", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "السيارات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "✅ سير العمل والموافقات", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "طلبات الموافقة", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "مصفوفة الموافقات", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "سجل العمليات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "📈 التقارير", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير المبيعات بالموظف", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير تحليل الخصومات", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير العمولات", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "💰 الإدارة المالية - العملاء", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "تحصيلات العملاء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "كشف حساب عميل", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "أعمار مديونيات العملاء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "التحصيلات اليومية", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "💳 الإدارة المالية - الموردين", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "مدفوعات الموردين", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "كشف حساب مورد", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "أعمار مستحقات الموردين", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "🏦 إدارة النقدية والبنوك", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "الصناديق", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "حركات النقدية", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "الإغلاق اليومي للصندوق", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "دفتر النقدية", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "ملخص الصناديق", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "حركات البنك", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "كشف حساب بنكي", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        {"type": "header", "data": {"text": "⚙️ الإعدادات", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "الإعدادات العامة", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "إعدادات سير العمل", "col": 4}},
    ]
    
    ws.content = json.dumps(content)

    # 5. Skip number_cards child table - use content JSON only


    # 6. Shortcuts (نفس الكود السابق)
    shortcuts_config = [
        ("Operational Status Report", "تقرير الحالات التشغيلية", "Blue", "Report"),
        ("Exception Dashboard Report", "لوحة الاستثناءات", "Red", "Report"),
        ("Daily Closing Report", "تقرير الإغلاق اليومي", "Purple", "Report"),
        ("Tele Sales Order", "طلبات التلي سيلز", "Red", "DocType"),
        ("Warehouse Dispatch", "إذن صرف مخزن", "Orange", "DocType"),
        ("Delivery Collection", "التوصيل والتحصيل", "Green", "DocType"),
        ("Pharma Warehouse", "المخازن", "Blue", "DocType"),
        ("Pharma Item", "الأصناف الدوائية", "Purple", "DocType"),
        ("Pharma Customer", "العملاء", "Green", "DocType"),
        ("Tele Sales Team", "فريق المبيعات", "Orange", "DocType"),
        ("Commission Calculation", "حساب العمولات", "Blue", "DocType"),
        ("Delivery Route", "خطوط التوصيل", "Yellow", "DocType"),
        ("Delivery Representative", "مندوبي التوصيل", "Cyan", "DocType"),
        ("Delivery Vehicle", "السيارات", "Grey", "DocType"),
        ("Pharma Approval Request", "طلبات الموافقة", "Red", "DocType"),
        ("Pharma Approval Matrix", "مصفوفة الموافقات", "Orange", "DocType"),
        ("Pharma Process Log", "سجل العمليات", "Blue", "DocType"),
        ("Expiring Stock Report", "تقرير المخزون قرب الانتهاء", "Yellow", "Report"),
        ("Expired Stock Report", "تقرير المخزون المنتهي", "Red", "Report"),
        ("Sales By Employee Report", "تقرير المبيعات بالموظف", "Green", "Report"),
        ("Discount Analysis Report", "تقرير تحليل الخصومات", "Orange", "Report"),
        ("Dispatch vs Collection Report", "تقرير الصرف والتحصيل", "Blue", "Report"),
        ("Overdue Collections Report", "تقرير التحصيلات المتأخرة", "Red", "Report"),
        ("Commission Report", "تقرير العمولات", "Purple", "Report"),
        ("Pharma General Settings", "الإعدادات العامة", "Pink", "DocType"),
        ("Pharma Workflow Settings", "إعدادات سير العمل", "Grey", "DocType"),
        ("Customer Payment", "تحصيلات العملاء", "Green", "DocType"),
        ("Customer Statement", "كشف حساب عميل", "Blue", "Report"),
        ("Customer Aging Report", "أعمار مديونيات العملاء", "Orange", "Report"),
        ("Daily Collections", "التحصيلات اليومية", "Cyan", "Report"),
        ("Supplier Payment", "مدفوعات الموردين", "Red", "DocType"),
        ("Supplier Statement", "كشف حساب مورد", "Blue", "Report"),
        ("Supplier Aging Report", "أعمار مستحقات الموردين", "Orange", "Report"),
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

    try:
        ws.insert(ignore_permissions=True)
        print(f"✅ تم إنشاء Workspace بنجاح!")
    except Exception as e:
        print(f"❌ فشل إنشاء Workspace: {str(e)}")

    frappe.db.commit()
    frappe.clear_cache()
    print("✅ تم الانتهاء - جرب دلوقتي!")
