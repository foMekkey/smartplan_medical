import frappe
import json

def execute():
    print("🚀 إنشاء Workspace بسيط (بدون Number Cards)...")

    # 1. تنظيف
    for ws in frappe.get_all("Workspace", filters={"name": "Pharma Cycle Management"}):
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ تم حذف: {ws.name}")

    frappe.db.commit()

    # 2. إنشاء Workspace
    print("\n🏢 إنشاء Workspace...")
    
    ws = frappe.new_doc("Workspace")
    ws.name = "Pharma Cycle Management"
    ws.label = "Pharma Cycle Management"
    ws.title = "Pharma Cycle Management"
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.public = 1
    ws.is_hidden = 0
    ws.is_standard = 0
    
    # 3. Content JSON (بدون Number Cards)
    content = [
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

    # 4. Shortcuts
    shortcuts_config = [
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
        ("Sales By Employee Report", "تقرير المبيعات بالموظف", "Green", "Report"),
        ("Discount Analysis Report", "تقرير تحليل الخصومات", "Orange", "Report"),
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
