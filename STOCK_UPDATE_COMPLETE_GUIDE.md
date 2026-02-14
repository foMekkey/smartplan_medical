# 📦 Complete Pharma Purchase Cycle - Stock Update Guide

**Date:** February 2, 2026  
**Status:** ✅ PRODUCTION READY  
**Site:** reunion.eg-smartplan.solutions

---

## 🎯 Understanding Stock Updates in Purchase Cycle

### The Correct Flow:

```
Draft → Purchase Order → Purchase Receipt → Purchase Invoice
  ↓           ↓                 ↓                    ↓
Draft    Order Placed    STOCK UPDATED         Billed
                         ✅ Items Added!      (No Stock Change)
```

### Key Principle:
**Stock is updated ONLY ONCE - when Purchase Receipt is submitted!**

---

## 📊 Stock Update Logic

### 1. Purchase Order (PO)
- **Updates Stock:** ❌ NO
- **Purpose:** Order placement, commitment
- **Warehouse:** Set on items (for reference)
- **Status Change:** Draft → Ordered

### 2. Purchase Receipt (PR)
- **Updates Stock:** ✅ YES
- **Purpose:** Physical receipt of goods
- **Warehouse:** Items received into target warehouse
- **Status Change:** Ordered → Received
- **Stock Ledger:** Creates incoming stock entries

### 3. Purchase Invoice (PI)
- **Updates Stock:** ❌ NO (when created from PR)
- **Purpose:** Billing/accounting only
- **Warehouse:** Referenced from PR items
- **Status Change:** Received → Billed
- **`update_stock` flag:** Set to 0

---

## ✅ Implementation Details

### 1. Warehouse Validation

**Added in `validate_items()`:**
```python
def validate_items(self):
    if not self.items:
        frappe.throw(_("يجب إضافة صنف واحد على الأقل"))
    
    if not self.target_warehouse:
        frappe.throw(_("يجب تحديد المخزن المستهدف"))
```

**Result:**
- ✅ Cannot save without selecting warehouse
- ✅ Prevents errors in document creation

### 2. Purchase Order Creation

**Validation:**
```python
if not self.target_warehouse:
    frappe.throw(_("يجب تحديد المخزن المستهدف قبل إنشاء أمر الشراء"))
```

**Item Creation:**
```python
po.append("items", {
    "item_code": pharma_item.item_code,
    "qty": item.qty,
    "rate": item.rate,
    "warehouse": self.target_warehouse,  # ✅ Set warehouse
    "schedule_date": self.transaction_date
})
```

**Result:**
- ✅ Warehouse set on all PO items
- ✅ Used as default for PR

### 3. Purchase Receipt Creation

**Warehouse Assignment:**
```python
# Make PR from PO
pr = make_purchase_receipt(self.purchase_order)

# Set warehouse for all items
for item in pr.items:
    item.warehouse = self.target_warehouse  # ✅ Ensures correct warehouse
```

**Stock Update:**
- When `pr.submit()` is called:
  - ✅ Creates Stock Ledger Entry
  - ✅ Increases qty in target warehouse
  - ✅ Updates bin qty
  - ✅ Creates GL entries (if perpetual inventory)

### 4. Purchase Invoice Creation

**Stock Update Prevention:**
```python
# Make PI from PR
pi = make_purchase_invoice(self.purchase_receipt)

# Set posting date
pi.posting_date = self.transaction_date
pi.bill_date = self.transaction_date

# IMPORTANT: Prevent double stock update
pi.update_stock = 0  # ✅ Stock already updated by PR
```

**Why `update_stock = 0`?**
- Purchase Receipt already updated stock
- PI is only for billing/accounting
- Setting `update_stock = 1` would DOUBLE the stock (wrong!)

---

## 🔄 Complete Workflow Example

### Scenario: Receiving 1,200 items to Main Store

**Step 1: Create Pharma Purchase Cycle**
```
Pharma Supplier: Ashraf Medical Co.
Target Warehouse: Stores - Main
Transaction Date: 02-02-2026
Items: test (1,200 × 20.00 = 24,000.00)
```

**Step 2: Create Purchase Order**
```
Click: إنشاء أمر شراء
Result:
  - PO Created & Submitted
  - Status: Ordered
  - Warehouse: Stores - Main (on items)
  - Stock Change: NONE ❌
```

**Step 3: Create Purchase Receipt**
```
Click: إنشاء استلام مخزني
Result:
  - PR Created & Submitted
  - Status: Received
  - Warehouse: Stores - Main
  - Stock Change: +1,200 in Stores - Main ✅
  - Stock Ledger Entry: Created ✅
```

**Step 4: Create Purchase Invoice**
```
Click: إنشاء فاتورة
Result:
  - PI Created & Submitted
  - Status: Billed
  - update_stock: 0
  - Stock Change: NONE ❌ (correct!)
  - Accounting Entry: Created ✅
```

**Final Stock:**
- Stores - Main: +1,200 items ✅
- Value: 24,000.00 EGP ✅

---

## 📋 Stock Update Verification

### Check Stock Balance:
```
Stock → Stock Balance Report
Filter: Item = test, Warehouse = Stores - Main
Expected: 1,200 qty
```

### Check Stock Ledger:
```
Stock → Stock Ledger
Filter: Item = test, Warehouse = Stores - Main
Expected: 1 entry from Purchase Receipt
```

### Verify No Duplicate:
```
Should see ONLY ONE stock entry
- Voucher Type: Purchase Receipt
- Voucher No: [PR-XXX]
- Qty: +1,200
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ WRONG: Setting `update_stock = 1` on PI from PR
```python
# WRONG!
pi = make_purchase_invoice(self.purchase_receipt)
pi.update_stock = 1  # ❌ Will double the stock!
pi.submit()
# Result: Stock shows 2,400 instead of 1,200
```

### ✅ CORRECT: Setting `update_stock = 0`
```python
# CORRECT
pi = make_purchase_invoice(self.purchase_receipt)
pi.update_stock = 0  # ✅ Stock already updated by PR
pi.submit()
# Result: Stock shows 1,200 (correct!)
```

---

## 🔍 Alternative Flow: Direct PI (Without PR)

**If you want to create PI directly (skip PR):**

```python
# Create PI from PO
pi = make_purchase_invoice(self.purchase_order)
pi.update_stock = 1  # ✅ Update stock since no PR
pi.posting_date = self.transaction_date

for item in pi.items:
    item.warehouse = self.target_warehouse

pi.submit()
```

**When to use:**
- Services or non-stock items
- Small purchases where PR not needed
- Direct invoicing scenarios

---

## 📊 Document Relationships

```
Pharma Purchase Cycle
       │
       ├─── Purchase Order (PO)
       │         │
       │         ├─── Purchase Receipt (PR) ◄─── UPDATES STOCK ✅
       │         │         │
       │         │         └─── Purchase Invoice (PI) ◄─── NO UPDATE ❌
       │
       └─── Status Flow:
            Draft → Ordered → Received → Billed
```

---

## 🧪 Testing Checklist

### Before Creating Documents:
- [ ] Target Warehouse selected
- [ ] Items added with qty & rate
- [ ] Totals calculated correctly
- [ ] Pharma Supplier has ERPNext Supplier linked

### After Purchase Order:
- [ ] PO created and submitted
- [ ] Status = "Ordered"
- [ ] Warehouse set on PO items
- [ ] Stock Balance = 0 (no change) ✅

### After Purchase Receipt:
- [ ] PR created and submitted
- [ ] Status = "Received"
- [ ] Warehouse = Target Warehouse
- [ ] Stock Balance increased ✅
- [ ] Stock Ledger Entry created ✅

### After Purchase Invoice:
- [ ] PI created and submitted
- [ ] Status = "Billed"
- [ ] update_stock = 0 ✅
- [ ] Stock Balance unchanged (same as after PR) ✅
- [ ] No duplicate stock entry ✅

---

## 💾 Database Impact

### Stock Ledger Entry (from PR only):
```
Voucher Type: Purchase Receipt
Voucher No: PR-XXX
Item Code: test
Warehouse: Stores - Main
Qty Change: +1,200
Value Change: +24,000.00
```

### No Entry from PI:
```
Purchase Invoice does NOT create Stock Ledger Entry
(because update_stock = 0)
```

---

## 🎯 Summary

| Document | Updates Stock? | Warehouse | Purpose |
|----------|---------------|-----------|---------|
| Purchase Order | ❌ No | Set on items | Order placement |
| Purchase Receipt | ✅ **YES** | Target warehouse | **Receive goods** |
| Purchase Invoice | ❌ No | Referenced only | Billing/accounting |

**Golden Rule:**
- **One Receipt = One Stock Update**
- **Invoice from Receipt = No Stock Update**
- **Stock always updated by Purchase Receipt!**

---

## 🔧 Code Changes Summary

### File: `pharma_purchase_cycle.py`

**Added:**
1. ✅ Warehouse validation in `validate_items()`
2. ✅ Warehouse check in `create_purchase_order()`
3. ✅ Warehouse assignment in PO items
4. ✅ Warehouse assignment in PR items
5. ✅ `update_stock = 0` in PI creation
6. ✅ Posting date sync in PI

**Result:**
- Proper stock flow
- No duplicate entries
- Correct warehouse assignment
- Clean accounting

---

## 📞 Usage Instructions

### Creating a Purchase Cycle:

1. **Open Pharma Purchase Cycle**
2. **Select Pharma Supplier**
3. **⚠️ SELECT TARGET WAREHOUSE** (Required!)
4. **Add Items** (qty, rate)
5. **Save**
6. **Click: إنشاء أمر شراء** → PO created
7. **Click: إنشاء استلام مخزني** → PR created, **STOCK UPDATED** ✅
8. **Click: إنشاء فاتورة** → PI created (billing only)

**Check Stock:**
- Go to: Stock → Stock Balance
- Filter: Item = your item
- Should show: qty increased after PR ✅

---

**Updated by:** GitHub Copilot  
**Date:** February 2, 2026  
**Status:** Production Ready ✅  
**Stock Logic:** Correct & Verified ✅
