# 🔧 Fix: Field Not Permitted in Query - customer_name

**Date:** February 2, 2026  
**Status:** ✅ RESOLVED  
**Site:** reunion.eg-smartplan.solutions

---

## 🐛 Problem

Users encountered runtime error when opening forms:
```
frappe.exceptions.DataError: Field not permitted in query: customer_name
```

The error appeared when:
- Creating new Warehouse Dispatch
- Creating new Delivery Collection  
- Selecting customers in forms

---

## 🔍 Root Cause

**Issue 1: Wrong fetch_from path**
- DocTypes had `fetch_from: "customer.customer_name"`
- But `customer` field links to **Pharma Customer** (custom DocType)
- Pharma Customer has field `legal_name`, NOT `customer_name`
- This caused Frappe to try querying a non-existent field

**Issue 2: Wrong field names in queries**
- Python code used `posting_date` but Tele Sales Order has `order_date`
- Python code queried `Customer` DocType instead of `Pharma Customer`

---

## ✅ Solution Applied

### 1. Fixed DocType JSON files
Changed `fetch_from` in:
- **warehouse_dispatch.json**
  ```json
  "fetch_from": "customer.legal_name"  // was: customer.customer_name
  ```
- **delivery_collection.json**
  ```json
  "fetch_from": "customer.legal_name"  // was: customer.customer_name
  ```

### 2. Fixed Python queries
**warehouse_dispatch.py** - `get_pending_tele_sales_orders()`:
- Changed `posting_date` → `order_date`
- Changed query from `Customer` → `Pharma Customer`
- Fetch `legal_name` instead of `customer_name`

**delivery_collection.py** - `get_pending_dispatches()`:
- Changed query from `Customer` → `Pharma Customer`
- Fetch `legal_name` instead of `customer_name`

---

## 📋 Files Changed

1. `/apps/smartplan_medical/.../doctype/warehouse_dispatch/warehouse_dispatch.json`
2. `/apps/smartplan_medical/.../doctype/warehouse_dispatch/warehouse_dispatch.py`
3. `/apps/smartplan_medical/.../doctype/delivery_collection/delivery_collection.json`
4. `/apps/smartplan_medical/.../doctype/delivery_collection/delivery_collection.py`

---

## 🧪 Verification

Test script confirms all fixes working:
```
✅ legal_name field exists in Pharma Customer
✅ Warehouse Dispatch fetch_from: customer.legal_name
✅ Delivery Collection fetch_from: customer.legal_name
✅ frappe.client.get_value works without errors
✅ get_pending_tele_sales_orders() returns correct data
```

Sample output:
```python
{
  'name': 'TSO-2026-0001',
  'customer': 'fouad',
  'order_date': datetime.date(2026, 2, 1),
  'net_amount': 180.0,
  'customer_name': 'fouad'  # ✅ Populated correctly
}
```

---

## 🚀 Deployment Steps Completed

1. ✅ Updated JSON DocType definitions
2. ✅ Updated Python code
3. ✅ Ran `bench clear-cache`
4. ✅ Ran `bench migrate` 
5. ✅ Restarted all services (`supervisorctl restart all`)
6. ✅ Verified with test script

---

## 💡 Key Learnings

**Custom vs Core DocTypes:**
- When linking to custom doctypes (Pharma Customer), use their actual field names
- Don't assume custom doctypes have same fields as core doctypes
- Pharma Customer uses `legal_name` (الاسم القانوني)
- Core Customer uses `customer_name`

**Field Permissions:**
- `fetch_from` must reference fields that exist in the linked DocType
- Frappe validates field permissions at runtime
- Wrong field paths cause "Field not permitted" errors

---

## ✅ Result

- ✅ Forms load without errors
- ✅ Customer names display correctly
- ✅ All pending order queries work
- ✅ No more "Field not permitted" errors

---

## 📞 Support

If similar errors appear for other fields, check:
1. The linked DocType's actual field names
2. Use `legal_name` for Pharma Customer
3. Use `customer_name` only for core Customer DocType

---

**Fixed by:** GitHub Copilot  
**Verified:** February 2, 2026
