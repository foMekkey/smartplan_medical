# ✅ Enhancement: Add Target Warehouse to Pharma Purchase Cycle

**Date:** February 2, 2026  
**Status:** ✅ COMPLETED  
**Site:** reunion.eg-smartplan.solutions

---

## 🎯 Requirement

Add a **Warehouse (Store)** dropdown field to Pharma Purchase Cycle form to:
1. Specify which warehouse/store to receive items into
2. Pass this warehouse to Purchase Order items
3. Set warehouse in Purchase Receipt when receiving stock

---

## ✅ Solution Implemented

### 1. Added Target Warehouse Field

**Field Details:**
- **Field Name:** `target_warehouse`
- **Field Type:** Link
- **Options:** Warehouse
- **Label (Arabic):** المخزن المستهدف
- **Required:** Yes
- **Position:** After Status field, before column break

### 2. Updated Purchase Order Creation

```python
po.append("items", {
    "item_code": pharma_item.item_code,
    "qty": item.qty,
    "rate": item.rate,
    "warehouse": self.target_warehouse,  # ✅ Added
    "schedule_date": self.transaction_date
})
```

**Impact:**
- Purchase Order items now have the target warehouse set
- This becomes the default receiving warehouse

### 3. Updated Purchase Receipt Creation

```python
# Make PR from PO
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
pr = make_purchase_receipt(self.purchase_order)

# Set warehouse for all items
for item in pr.items:
    item.warehouse = self.target_warehouse  # ✅ Added

pr.flags.ignore_permissions = True
pr.insert()
pr.submit()
```

**Impact:**
- Purchase Receipt items automatically set to target warehouse
- Items received into the correct store location

---

## 📋 Files Modified

### 1. DocType JSON
**File:** `pharma_purchase_cycle.json`

**Changes:**
- ✅ Added `"target_warehouse"` to `field_order`
- ✅ Added field definition with Link to Warehouse

### 2. Python Controller
**File:** `pharma_purchase_cycle.py`

**Changes:**
- ✅ Added `warehouse: self.target_warehouse` to PO items
- ✅ Added loop to set warehouse on PR items

---

## 🎨 User Interface

### Form Layout:
```
┌─────────────────────────────────────────────────┐
│ البيانات الأساسية (Basic Data)                  │
├─────────────────────────────────────────────────┤
│ [Naming Series]  [Transaction Date]             │
│ [Pharma Supplier] [Status]                      │
│ [Supplier Name]   [Target Warehouse] ◄── NEW!   │
├─────────────────────────────────────────────────┤
│ [Purchase Order]                                │
│ [Purchase Receipt]                              │
│ [Purchase Invoice]                              │
└─────────────────────────────────────────────────┘
```

### Warehouse Dropdown:
- Shows all available warehouses from ERPNext
- Required field (must select before creating documents)
- Linked to standard ERPNext Warehouse DocType

---

## 🔄 Workflow Impact

### Before:
```
1. Create Pharma Purchase Cycle
2. Create Purchase Order → ❌ No warehouse specified
3. Create Purchase Receipt → ❌ Must manually set warehouse
```

### After:
```
1. Create Pharma Purchase Cycle
2. Select Target Warehouse ◄── NEW STEP
3. Create Purchase Order → ✅ Warehouse auto-set on items
4. Create Purchase Receipt → ✅ Warehouse auto-set, items received to correct store
```

---

## 📊 Example Usage

### Scenario: Receiving to Main Store

**Form Data:**
- Pharma Supplier: Ashraf Medical Co.
- Target Warehouse: **Stores - Main**
- Items: 1,200 qty × 20.00 rate

**Results:**
1. **Purchase Order created:**
   - Item: test
   - Qty: 1,200
   - Warehouse: **Stores - Main** ✅

2. **Purchase Receipt created:**
   - Item: test
   - Qty: 1,200
   - Accepted Warehouse: **Stores - Main** ✅
   - Stock increases in Main Store ✅

---

## ✅ Benefits

1. **Prevents Errors:**
   - No missing warehouse on Purchase Receipt
   - Items automatically received to correct location

2. **Saves Time:**
   - No manual warehouse selection needed
   - One-time configuration per cycle

3. **Improves Accuracy:**
   - Warehouse set once, used consistently
   - Reduces data entry mistakes

4. **Better Control:**
   - Can route purchases to different warehouses
   - Track which warehouse each purchase cycle targets

---

## 🧪 Testing Checklist

- [x] Field appears on form after Status
- [x] Warehouse dropdown shows all warehouses
- [x] Field is required (cannot save without it)
- [x] Purchase Order items get warehouse
- [x] Purchase Receipt items get warehouse
- [x] Stock increases in selected warehouse
- [x] Database migration successful
- [x] Cache cleared

---

## 🚀 Deployment Status

**Completed Steps:**
1. ✅ Added field to JSON (field_order + definition)
2. ✅ Updated PO creation logic (set warehouse on items)
3. ✅ Updated PR creation logic (set warehouse on items)
4. ✅ Ran `bench migrate` (added field to database)
5. ✅ Ran `bench clear-cache` (reloaded DocType)

**Ready to Use:**
- ✅ Refresh browser to see new field
- ✅ Select warehouse when creating new Pharma Purchase Cycle
- ✅ Purchase Order and Receipt will use selected warehouse

---

## 💡 Usage Instructions

### For New Purchase Cycles:

1. **Open Form:** Create new Pharma Purchase Cycle
2. **Fill Basic Data:**
   - Select Pharma Supplier
   - Set Transaction Date
3. **Select Target Warehouse:** ◄── IMPORTANT!
   - Choose warehouse from dropdown
   - Examples: "Stores - Main", "Pharmacy Store", etc.
4. **Add Items:**
   - Select Pharma Item
   - Enter Qty and Rate
5. **Create Documents:**
   - Click "إنشاء أمر شراء" (Create PO)
   - Click "إنشاء استلام مخزني" (Create PR)
   - Items automatically received to selected warehouse ✅

### For Existing Purchase Cycles:

- **Draft Documents:** Add warehouse before creating PO
- **Already Created PO/PR:** Warehouse may need manual adjustment if created before this update

---

## 🔍 Technical Details

### Field Schema:
```json
{
  "fieldname": "target_warehouse",
  "fieldtype": "Link",
  "label": "المخزن المستهدف",
  "options": "Warehouse",
  "reqd": 1
}
```

### Purchase Order Item Schema:
```python
{
    "item_code": pharma_item.item_code,
    "qty": item.qty,
    "rate": item.rate,
    "warehouse": self.target_warehouse,  # Links to Warehouse
    "schedule_date": self.transaction_date
}
```

### Purchase Receipt Item Update:
```python
for item in pr.items:
    item.warehouse = self.target_warehouse  # Sets accepted_warehouse
```

---

## 📝 Related Documentation

- [FIX_PHARMA_PURCHASE_CYCLE.md](./FIX_PHARMA_PURCHASE_CYCLE.md) - Button & Totals Fix
- [COMPLETE_LINK_FIELD_FIX.md](./COMPLETE_LINK_FIELD_FIX.md) - Link Field Validation
- [FIELD_MAPPING_CHEATSHEET.md](./FIELD_MAPPING_CHEATSHEET.md) - Field Mapping Reference

---

**Enhancement by:** GitHub Copilot  
**Date:** February 2, 2026  
**Status:** Production Ready ✅  
**Feature:** Warehouse Selection Working ✅
