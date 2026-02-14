#!/bin/bash
# سكربت تثبيت وتهيئة smartplan_medical مع المزامنة التلقائية لـ ERPNext Core

set -e  # إيقاف عند أول خطأ

SITE_NAME="reunion.eg-smartplan.solutions"
BENCH_PATH="/home/frappe/frappe-bench"

echo "======================================"
echo "🚀 تثبيت وتهيئة Smartplan Medical"
echo "======================================"
echo ""

# التحقق من وجود bench
if [ ! -d "$BENCH_PATH" ]; then
    echo "❌ خطأ: مسار bench غير موجود: $BENCH_PATH"
    exit 1
fi

cd "$BENCH_PATH"

# الخطوة 1: أخذ نسخة احتياطية
echo "📦 الخطوة 1/6: أخذ نسخة احتياطية من قاعدة البيانات..."
bench --site "$SITE_NAME" backup --with-files || {
    echo "⚠️ تحذير: فشل أخذ النسخة الاحتياطية (قد يكون التطبيق غير مثبت بعد)"
}
echo "✅ تمت النسخة الاحتياطية (أو تم التجاوز)"
echo ""

# الخطوة 2: تثبيت التطبيق
echo "📥 الخطوة 2/6: تثبيت التطبيق..."
if bench --site "$SITE_NAME" list-apps | grep -q "smartplan_medical"; then
    echo "✅ التطبيق مثبت بالفعل"
else
    bench --site "$SITE_NAME" install-app smartplan_medical
    echo "✅ تم تثبيت التطبيق"
fi
echo ""

# الخطوة 3: ترحيل قاعدة البيانات
echo "🔄 الخطوة 3/6: ترحيل قاعدة البيانات (تحديث الحقول)..."
bench --site "$SITE_NAME" migrate
echo "✅ تم الترحيل بنجاح"
echo ""

# الخطوة 4: مسح الكاش
echo "🧹 الخطوة 4/6: مسح الكاش..."
bench --site "$SITE_NAME" clear-cache
bench --site "$SITE_NAME" clear-website-cache
echo "✅ تم مسح الكاش"
echo ""

# الخطوة 5: إنشاء Item Group إذا لم تكن موجودة
echo "📦 الخطوة 5/6: التحقق من Item Groups..."
bench --site "$SITE_NAME" execute "
import frappe
try:
    if not frappe.db.exists('Item Group', 'Products'):
        ig = frappe.new_doc('Item Group')
        ig.item_group_name = 'Products'
        ig.parent_item_group = 'All Item Groups'
        ig.is_group = 0
        ig.insert(ignore_permissions=True)
        frappe.db.commit()
        print('✅ تم إنشاء Item Group: Products')
    else:
        print('✅ Item Group موجودة بالفعل')
except Exception as e:
    print(f'⚠️ تحذير: {str(e)}')
" || echo "⚠️ تم التجاوز"
echo ""

# الخطوة 6: إنشاء Workspace العربية
echo "🏢 الخطوة 6/6: إنشاء Workspace العربية..."
bench --site "$SITE_NAME" execute "smartplan_medical.smartplan_medical.fix_workspace_arabic.execute" || {
    echo "❌ فشل إنشاء Workspace"
    echo "يرجى التحقق من الأخطاء أعلاه"
    exit 1
}
echo "✅ تم إنشاء Workspace بنجاح"
echo ""

# إعادة تشغيل bench
echo "🔄 إعادة تشغيل Bench..."
bench restart
echo "✅ تم إعادة التشغيل"
echo ""

echo "======================================"
echo "✅ اكتمل التثبيت بنجاح!"
echo "======================================"
echo ""
echo "📋 الخطوات التالية:"
echo "1. افتح المتصفح وسجل الدخول إلى: https://$SITE_NAME"
echo "2. ابحث عن Workspace: Pharma Cycle Management"
echo "3. جرّب إنشاء:"
echo "   - Pharma Customer (سيُنشئ Customer في ERPNext)"
echo "   - Pharma Item (سيُنشئ Item في ERPNext)"
echo "   - Pharma Warehouse (سيُنشئ Warehouse في ERPNext)"
echo "   - Pharma Supplier (سيُنشئ Supplier في ERPNext)"
echo ""
echo "📖 راجع الأدلة:"
echo "   - دليل المستخدم: apps/smartplan_medical/USER_MANUAL.md"
echo "   - دليل المزامنة: apps/smartplan_medical/CORE_SYNC_GUIDE.md"
echo ""
echo "🎉 كل شيء جاهز للاستخدام!"
