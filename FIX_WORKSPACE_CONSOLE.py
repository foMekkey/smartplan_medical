"""
Fix Workspace - Run this in ERPNext Console
تشغيل هذا الكود في Console على السيرفر
"""

import frappe
import json
import re

print("=" * 60)
print("🔄 جاري إصلاح الـ Workspace...")
print("=" * 60)

# 1) حذف كل الـ Workspaces القديمة للموديول
for ws in frappe.get_all("Workspace", filters={"module": "Smartplan Medical"}):
    frappe.delete_doc("Workspace", ws.name, force=1)
    print(f"🗑️ تم حذف: {ws.name}")

# حذف أي workspace فيها كلمات عربية أو Pharma
for ws in frappe.get_all("Workspace"):
    if bool(re.search(r"[\u0600-\u06FF]", str(ws.name))) or "Pharma" in ws.name:
        try:
            frappe.delete_doc("Workspace", ws.name, force=1)
            print(f"🗑️ تم حذف: {ws.name}")
        except:
            pass

frappe.db.commit()

# 2) إنشاء Workspace جديد
ws = frappe.new_doc("Workspace")
ws.name = "Pharma Cycle Management"
ws.label = "Pharma Cycle Management"
ws.title = "إدارة دورة شركة الأدوية"
ws.module = "Smartplan Medical"
ws.icon = "healthcare"
ws.public = 1
ws.is_hidden = 0

# 3) Content JSON
content = [
    {"type": "header", "data": {"text": "عمليات البيع", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "طلبات التلي سيلز", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "إذن صرف مخزن", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "التوصيل والتحصيل", "col": 4}},
    {"type": "spacer", "data": {"col": 12}},
    {"type": "header", "data": {"text": "إدارة المخازن", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "المخازن", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "الأصناف الدوائية", "col": 4}},
    {"type": "spacer", "data": {"col": 12}},
    {"type": "header", "data": {"text": "العملاء والمبيعات", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "العملاء", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "فريق المبيعات", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "حساب العمولات", "col": 4}},
    {"type": "spacer", "data": {"col": 12}},
    {"type": "header", "data": {"text": "التوصيل", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "خطوط التوصيل", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "مندوبي التوصيل", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "السيارات", "col": 4}},
    {"type": "spacer", "data": {"col": 12}},
    {"type": "header", "data": {"text": "سير العمل والموافقات", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "طلبات الموافقة", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "مصفوفة الموافقات", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "سجل العمليات", "col": 4}},
    {"type": "spacer", "data": {"col": 12}},
    {"type": "header", "data": {"text": "التقارير", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير المخزون قرب الانتهاء", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير المخزون المنتهي", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير المبيعات بالموظف", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير تحليل الخصومات", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير الصرف والتحصيل", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير التحصيلات المتأخرة", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "تقرير العمولات", "col": 4}},
    {"type": "spacer", "data": {"col": 12}},
    {"type": "header", "data": {"text": "الإعدادات", "col": 12}},
    {"type": "shortcut", "data": {"shortcut_name": "الإعدادات العامة", "col": 4}},
    {"type": "shortcut", "data": {"shortcut_name": "إعدادات سير العمل", "col": 4}},
]
ws.content = json.dumps(content)

# 4) Shortcuts
shortcuts = [
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
]

for link_to, label, color, link_type in shortcuts:
    ws.append("shortcuts", {
        "type": link_type,
        "link_to": link_to,
        "label": label,
        "doc_view": "List" if link_type == "DocType" else "",
        "color": color
    })

ws.insert(ignore_permissions=True)
frappe.db.commit()
frappe.clear_cache()

print("\n" + "=" * 60)
print("✅ تم بنجاح!")
print(f"📁 Workspace: {ws.name}")
print(f"🔗 Shortcuts: {len(ws.shortcuts)}")
print("=" * 60)
