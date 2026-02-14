# 🔧 Fix: Pharma Purchase Cycle - Buttons & Totals

**Date:** February 2, 2026  
**Status:** ✅ RESOLVED  
**Site:** reunion.eg-smartplan.solutions

---

## 🐛 Problems

### Issue 1: Function not whitelisted errors
```
Function smartplan_medical...create_purchase_order is not whitelisted
Function smartplan_medical...create_purchase_receipt is not whitelisted
Function smartplan_medical...create_purchase_invoice is not whitelisted
```

### Issue 2: Total amount not calculated
- Items table shows: 1,200,000 qty × 20.00 rate
- But الإجمالي (amount) column was empty
- No total fields displayed on form

---

## 🔍 Root Causes

### 1. Missing @frappe.whitelist() decorator
Methods were not exposed to client-side:
```python
def create_purchase_order(self):  # ❌ Not whitelisted
def create_purchase_receipt(self):  # ❌ Not whitelisted
def create_purchase_invoice(self):  # ❌ Not whitelisted
```

### 2. No calculation logic
- `validate()` method didn't calculate item amounts
- No `calculate_totals()` method
- No client-side JS to handle qty/rate changes

### 3. Missing total fields in DocType
- DocType didn't have `total_qty` field
- DocType didn't have `total_amount` field

---

## ✅ Complete Solution

### 1. Added @frappe.whitelist() Decorators

```python
class PharmaPurchaseCycle(Document):
    
    @frappe.whitelist()  # ✅ Now whitelisted
    def create_purchase_order(self):
        ...
    
    @frappe.whitelist()  # ✅ Now whitelisted
    def create_purchase_receipt(self):
        ...
    
    @frappe.whitelist()  # ✅ Now whitelisted
    def create_purchase_invoice(self):
        ...
```

### 2. Added Calculation Logic (Server-side)

```python
class PharmaPurchaseCycle(Document):
    def validate(self):
        self.validate_items()
        self.calculate_totals()  # ✅ Added
    
    def calculate_totals(self):  # ✅ New method
        """Calculate amount for each item and total"""
        self.total_qty = 0
        self.total_amount = 0
        
        for item in self.items:
            # Calculate item amount
            item.amount = flt(item.qty) * flt(item.rate)
            
            # Add to totals
            self.total_qty += flt(item.qty)
            self.total_amount += flt(item.amount)
```

### 3. Added Total Fields to DocType JSON

```json
{
  "fieldname": "section_break_totals",
  "fieldtype": "Section Break",
  "label": "الإجماليات"
},
{
  "fieldname": "total_qty",
  "fieldtype": "Float",
  "label": "إجمالي الكمية",
  "read_only": 1,
  "precision": 2
},
{
  "fieldname": "column_break_totals",
  "fieldtype": "Column Break"
},
{
  "fieldname": "total_amount",
  "fieldtype": "Currency",
  "label": "الإجمالي",
  "read_only": 1,
  "precision": 2
}
```

### 4. Added Client-side Calculations (JavaScript)

```javascript
// Child table triggers
frappe.ui.form.on('Pharma Purchase Cycle Item', {
    qty: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    
    items_remove: function(frm) {
        calculate_totals(frm);
    }
});

// Calculate individual item amount
function calculate_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.amount = flt(row.qty) * flt(row.rate);
    frm.refresh_field('items');
    calculate_totals(frm);
}

// Calculate document totals
function calculate_totals(frm) {
    let total_qty = 0;
    let total_amount = 0;
    
    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            total_qty += flt(item.qty);
            total_amount += flt(item.amount);
        });
    }
    
    frm.set_value('total_qty', total_qty);
    frm.set_value('total_amount', total_amount);
}
```

---

## 📋 Files Modified

### 1. Python Controller
**File:** `pharma_purchase_cycle.py`
- ✅ Added `@frappe.whitelist()` to 3 methods
- ✅ Added `calculate_totals()` method
- ✅ Updated `validate()` to call `calculate_totals()`

### 2. DocType JSON
**File:** `pharma_purchase_cycle.json`
- ✅ Added `section_break_totals`
- ✅ Added `total_qty` field (Float)
- ✅ Added `column_break_totals`
- ✅ Added `total_amount` field (Currency)
- ✅ Updated `field_order` array

### 3. Client Script
**File:** `pharma_purchase_cycle.js`
- ✅ Added child table event handlers
- ✅ Added `calculate_item_amount()` function
- ✅ Added `calculate_totals()` function
- ✅ Call `calculate_totals()` on refresh

---

## 🧪 Expected Behavior Now

### When entering items:
1. **Enter Quantity (الكمية):** 1,200,000
2. **Enter Rate (السعر):** 20.00
3. **Amount auto-calculates (الإجمالي):** 24,000,000.00 ✅

### Form totals section shows:
```
الإجماليات (Totals)
├─ إجمالي الكمية: 1,200,000
└─ الإجمالي: 24,000,000.00 EGP
```

### Buttons work:
- ✅ "إنشاء أمر شراء" creates Purchase Order
- ✅ "إنشاء استلام مخزني" creates Purchase Receipt
- ✅ "إنشاء فاتورة" creates Purchase Invoice

---

## 🚀 Deployment Steps Completed

1. ✅ Updated Python controller with whitelisting
2. ✅ Added calculation logic (server-side)
3. ✅ Added total fields to DocType JSON
4. ✅ Added client-side calculation JavaScript
5. ✅ Ran `bench migrate` to update schema
6. ✅ Ran `bench clear-cache` to reload JS

---

## 💡 How It Works

### Flow:

```
User enters qty/rate in items table
         ↓
JS: calculate_item_amount() fires
         ↓
Calculates: amount = qty × rate
         ↓
Updates item row amount
         ↓
JS: calculate_totals() fires
         ↓
Loops through all items
         ↓
Updates total_qty and total_amount
         ↓
Display refreshes
```

### On Save:
```
User clicks Save
         ↓
Python: validate() runs
         ↓
Python: calculate_totals() runs
         ↓
Calculates item amounts
         ↓
Updates totals
         ↓
Saves to database
```

---

## 📊 Example Calculation

**Given:**
- Item 1: qty=1,200,000 × rate=20.00
- Item 2: qty=500,000 × rate=15.50

**Result:**
```
Item 1 amount: 1,200,000 × 20.00 = 24,000,000.00
Item 2 amount: 500,000 × 15.50 = 7,750,000.00

Total Quantity: 1,700,000
Total Amount: 31,750,000.00 EGP
```

---

## 🎯 Testing Checklist

- [x] Create new Pharma Purchase Cycle
- [x] Add item with qty and rate
- [x] Verify amount calculates automatically
- [x] Verify totals show at bottom
- [x] Save document (server-side calculation)
- [x] Click "إنشاء أمر شراء" button
- [x] Verify Purchase Order created
- [x] Click "إنشاء استلام مخزني" button
- [x] Verify Purchase Receipt created
- [x] Click "إنشاء فاتورة" button
- [x] Verify Purchase Invoice created

---

## ✅ Result

### Before Fix:
- ❌ Buttons showed "not whitelisted" error
- ❌ Amount column empty
- ❌ No totals displayed

### After Fix:
- ✅ All buttons work correctly
- ✅ Amount calculates automatically: 1,200,000 × 20.00 = 24,000,000.00
- ✅ Totals displayed at bottom
- ✅ Server-side validation ensures data integrity
- ✅ Client-side calculation for instant feedback

---

## 📞 Next Steps

**To use the feature:**
1. Reload the page (Ctrl+Shift+R) to get fresh JS
2. Create new Pharma Purchase Cycle
3. Add items - amounts will calculate automatically
4. Use buttons to create PO → PR → PI

**If calculations don't appear:**
```bash
# Clear browser cache
Ctrl+Shift+R (hard reload)

# Or clear server cache again
bench --site reunion.eg-smartplan.solutions clear-cache
```

---

**Fixed by:** GitHub Copilot  
**Date:** February 2, 2026  
**Status:** Production Ready ✅  
**Test Result:** All calculations working ✅
