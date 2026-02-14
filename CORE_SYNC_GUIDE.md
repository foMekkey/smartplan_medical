# دليل المزامنة مع ERPNext Core

## نظرة عامة
تم تحديث جميع الـ Doctypes المخصصة في `smartplan_medical` لتتزامن تلقائياً مع Doctypes الأساسية في ERPNext Core.

## الـ Doctypes المُحدّثة

### 1. Pharma Customer → Customer
**الحقول المضافة:**
- `erpnext_customer` (Link to Customer) - للقراءة فقط

**المنطق:**
- عند حفظ Pharma Customer، يتم تلقائياً:
  - إنشاء Customer جديد في ERPNext إذا لم يكن موجود
  - تحديث بيانات Customer الموجود (الاسم، البريد، الهاتف، الرقم الضريبي)
- يتم ملء حقل `erpnext_customer` تلقائياً بعد الإنشاء

**الملفات المُعدّلة:**
- `doctype/pharma_customer/pharma_customer.json`
- `doctype/pharma_customer/pharma_customer.py`

---

### 2. Pharma Supplier → Supplier
**الحقول الموجودة:**
- `erpnext_supplier` (Link to Supplier) - موجود سابقاً

**المنطق:**
- المزامنة موجودة بالفعل في `pharma_supplier.py`
- تم إضافة تعريف JSON الكامل في `pharma_supplier.json` (كان مفقوداً)

**الملفات المُعدّلة:**
- `doctype/pharma_supplier/pharma_supplier.json` (أُنشئ من الصفر)

---

### 3. Pharma Item → Item
**الحقول المضافة:**
- `item_code` (Link to Item) - للقراءة فقط

**المنطق:**
- عند حفظ Pharma Item، يتم تلقائياً:
  - إنشاء Item جديد في ERPNext مع:
    - `item_code` = `item_name`
    - `item_group` = "Products"
    - `stock_uom` = من حقل `unit_of_measure`
    - `standard_rate` = من حقل `public_price`
    - `brand` = من حقل `manufacturer`
  - تحديث بيانات Item الموجود
- يتم ملء حقل `item_code` تلقائياً

**الملفات المُعدّلة:**
- `doctype/pharma_item/pharma_item.json`
- `doctype/pharma_item/pharma_item.py`

---

### 4. Pharma Warehouse → Warehouse
**الحقول المضافة:**
- `erpnext_warehouse` (Link to Warehouse) - للقراءة فقط

**المنطق:**
- عند حفظ Pharma Warehouse، يتم تلقائياً:
  - إنشاء Warehouse جديد في ERPNext مع:
    - `warehouse_name` من الحقل
    - `company` من الإعدادات الافتراضية
    - `warehouse_type` يترجم من العربية
  - تحديث بيانات Warehouse الموجود
- يتم ملء حقل `erpnext_warehouse` تلقائياً

**الملفات المُعدّلة:**
- `doctype/pharma_warehouse/pharma_warehouse.json`
- `doctype/pharma_warehouse/pharma_warehouse.py`

---

### 5. Pharma Purchase Cycle (تحسينات)
**التحديثات:**
- تحسين التحقق من وجود `item_code` في Pharma Item قبل إنشاء Purchase Order
- رسالة خطأ واضحة إذا كان الصنف غير مربوط بـ ERPNext Item

**الملفات المُعدّلة:**
- `doctype/pharma_purchase_cycle/pharma_purchase_cycle.py`

---

## خطوات التطبيق

### الخطوة 1: تثبيت التطبيق (إذا لم يكن مثبتاً)
```bash
cd /home/frappe/frappe-bench
bench --site reunion.eg-smartplan.solutions install-app smartplan_medical
```

### الخطوة 2: ترحيل قاعدة البيانات (لتحديث الحقول)
```bash
bench --site reunion.eg-smartplan.solutions migrate
```

### الخطوة 3: مسح الكاش
```bash
bench --site reunion.eg-smartplan.solutions clear-cache
```

### الخطوة 4: إنشاء Workspace العربية
```bash
bench --site reunion.eg-smartplan.solutions execute "smartplan_medical.smartplan_medical.fix_workspace_arabic.execute"
```

---

## اختبار المزامنة

### اختبار Customer
1. أنشئ Pharma Customer جديد
2. املأ الحقول المطلوبة (الاسم القانوني، البريد، الهاتف)
3. احفظ المستند
4. تحقق من:
   - ظهور رسالة "تم إنشاء عميل ERPNext: [اسم]"
   - ملء حقل "عميل ERPNext" تلقائياً
   - وجود Customer جديد في ERPNext بنفس البيانات

### اختبار Item
1. أنشئ Pharma Item جديد
2. املأ الحقول (اسم الصنف، السعر، وحدة القياس)
3. احفظ المستند
4. تحقق من:
   - ظهور رسالة "تم إنشاء صنف ERPNext: [اسم]"
   - ملء حقل "صنف ERPNext" تلقائياً
   - وجود Item جديد في Stock > Items

### اختبار Warehouse
1. أنشئ Pharma Warehouse جديد
2. املأ الحقول (اسم المخزن، الموقع، النوع)
3. احفظ المستند
4. تحقق من:
   - ظهور رسالة "تم إنشاء مخزن ERPNext: [اسم]"
   - ملء حقل "مخزن ERPNext" تلقائياً
   - وجود Warehouse جديد في Stock > Warehouses

### اختبار Purchase Cycle
1. تأكد من وجود Pharma Supplier و Pharma Item
2. أنشئ Pharma Purchase Cycle جديد
3. اختر المورد وأضف أصناف
4. اضغط "إنشاء أمر شراء"
5. تحقق من:
   - إنشاء Purchase Order في Buying
   - تغيير الحالة إلى "Ordered"

---

## معالجة الأخطاء

### خطأ: "App smartplan_medical is not installed"
**الحل:**
```bash
bench --site reunion.eg-smartplan.solutions install-app smartplan_medical
```

### خطأ: "Item Group Products does not exist"
**الحل:**
```bash
# إنشاء Item Group إذا لم تكن موجودة
bench --site reunion.eg-smartplan.solutions execute "import frappe; ig = frappe.new_doc('Item Group'); ig.item_group_name = 'Products'; ig.insert(ignore_if_duplicate=True)"
```

### خطأ: "Company not set"
**الحل:**
```bash
# تعيين شركة افتراضية
bench --site reunion.eg-smartplan.solutions set-config default_company "Your Company Name"
```

---

## ملاحظات مهمة

### القواعد الصارمة (لم تتغير)
- ✅ لم يتم تعديل أو حذف أي Doctype موجود
- ✅ لم يتم تغيير أي منطق Backend حالي (فقط إضافة)
- ✅ لم يتم كسر أي ربط محاسبي أو مخزني قائم
- ✅ جميع مسميات الحقول بالعربية فقط
- ✅ الإضافات تعتمد على ERPNext Core

### السلوك التلقائي
- المزامنة تحدث تلقائياً عند الحفظ (before_save hook)
- إذا فشل الإنشاء، يظهر خطأ واضح ولا يتم حفظ المستند
- إذا فشل التحديث، يتم تسجيل الخطأ في Log ولا يتم إيقاف العملية
- حقول الربط (erpnext_customer, item_code, etc.) للقراءة فقط لمنع التعديل اليدوي

### الصلاحيات
- المزامنة تستخدم `ignore_permissions=True` لتجنب مشاكل الصلاحيات
- تأكد من أن المستخدمين لديهم صلاحية إنشاء Pharma Doctypes على الأقل

---

## الدعم الفني
إذا واجهت أي مشكلة:
1. تحقق من سجل الأخطاء: `/desk#List/Error Log`
2. راجع الـ Traceback في الطرفية
3. تأكد من تشغيل `bench migrate` بعد التحديثات
4. أعد تشغيل bench إذا لزم: `bench restart`

---

تم إعداد هذا الدليل في: 2026-02-01
الإصدار: 1.0 (Enterprise Arabic Edition)
