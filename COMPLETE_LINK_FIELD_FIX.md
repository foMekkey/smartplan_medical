# 🔧 COMPLETE FIX: All Link Field Validation Errors

**Date:** February 2, 2026  
**Status:** ✅ FULLY RESOLVED  
**Site:** reunion.eg-smartplan.solutions

---

## 🐛 Problems Encountered

### Error 1: Field not permitted in query: customer_name
```
frappe.exceptions.DataError: Field not permitted in query: customer_name
```

### Error 2: Field not permitted in query: sales_order
```
frappe.exceptions.DataError: Field not permitted in query: sales_order
```

Both errors occurred when:
- Creating new Warehouse Dispatch
- Creating new Delivery Collection
- Selecting customers/orders in link fields
- Form auto-fetch operations

---

## 🔍 Root Causes

### 1. Wrong fetch_from paths for customer_name
**Issue:** DocTypes referenced `customer.customer_name` but:
- `customer` field links to **Pharma Customer** (custom DocType)
- Pharma Customer has `legal_name`, NOT `customer_name`
- Frappe tried to query non-existent field

### 2. Wrong field name in sales_order fetch_from
**Issue:** Warehouse Dispatch referenced `tele_sales_order.sales_order` but:
- Tele Sales Order has field named `sales_order_reference`
- Not `sales_order`

### 3. Wrong field names in Python queries
**Issue:** Python code used incorrect field names:
- Used `posting_date` (doesn't exist) instead of `order_date`
- Queried `Customer` DocType instead of `Pharma Customer`
- Requested `customer_name` instead of `legal_name`

---

## ✅ Complete Solution

### 1. Fixed DocType JSON Files

#### warehouse_dispatch.json
```json
// BEFORE (❌ WRONG)
{
  "fetch_from": "customer.customer_name",  // ❌ customer_name doesn't exist
  "fieldname": "customer_name"
}
{
  "fetch_from": "tele_sales_order.sales_order",  // ❌ sales_order doesn't exist
  "fieldname": "sales_order"
}

// AFTER (✅ FIXED)
{
  "fetch_from": "customer.legal_name",  // ✅ Correct!
  "fieldname": "customer_name"
}
{
  "fetch_from": "tele_sales_order.sales_order_reference",  // ✅ Correct!
  "fieldname": "sales_order"
}
```

#### delivery_collection.json
```json
// BEFORE (❌ WRONG)
{
  "fetch_from": "customer.customer_name",
  "fieldname": "customer_name"
}

// AFTER (✅ FIXED)
{
  "fetch_from": "customer.legal_name",
  "fieldname": "customer_name"
}
```

### 2. Fixed Python Code

#### warehouse_dispatch.py - get_pending_tele_sales_orders()

```python
# BEFORE (❌ WRONG)
orders = frappe.get_all(
    "Tele Sales Order",
    filters=filters,
    fields=["name", "customer", "posting_date", "net_amount"],  # ❌ posting_date doesn't exist
    order_by="posting_date desc"
)

for o in orders:
    o["customer_name"] = frappe.db.get_value(
        "Customer",  # ❌ Wrong DocType
        o.get("customer"), 
        "customer_name"  # ❌ Wrong field
    )

# AFTER (✅ FIXED)
orders = frappe.get_all(
    "Tele Sales Order",
    filters=filters,
    fields=["name", "customer", "order_date", "net_amount"],  # ✅ order_date
    order_by="order_date desc"
)

for o in orders:
    o["customer_name"] = frappe.db.get_value(
        "Pharma Customer",  # ✅ Correct DocType
        o.get("customer"), 
        "legal_name"  # ✅ Correct field
    )
```

#### delivery_collection.py - get_pending_dispatches()

```python
# BEFORE (❌ WRONG)
for d in dispatches:
    d["customer_name"] = frappe.db.get_value(
        "Customer", d.get("customer"), "customer_name"  # ❌ Wrong
    )

# AFTER (✅ FIXED)
for d in dispatches:
    d["customer_name"] = frappe.db.get_value(
        "Pharma Customer", d.get("customer"), "legal_name"  # ✅ Correct
    )
```

---

## 📋 Files Modified

### DocType JSON Files
1. `warehouse_dispatch.json` - Fixed 2 fetch_from paths
   - `customer_name`: customer.customer_name → customer.legal_name
   - `sales_order`: tele_sales_order.sales_order → tele_sales_order.sales_order_reference

2. `delivery_collection.json` - Fixed 1 fetch_from path
   - `customer_name`: customer.customer_name → customer.legal_name

### Python Files
3. `warehouse_dispatch.py` - Fixed query function
   - Changed field: posting_date → order_date
   - Changed DocType: Customer → Pharma Customer
   - Changed field: customer_name → legal_name

4. `delivery_collection.py` - Fixed query function
   - Changed DocType: Customer → Pharma Customer
   - Changed field: customer_name → legal_name

---

## 🧪 Verification Results

### Automated Test Suite
Created comprehensive test script: `test_all_links.py`

```
======================================================================
📊 TEST SUMMARY
======================================================================
✅ PASS   Pharma Customer.legal_name
✅ PASS   TSO.customer_name fetch_from
✅ PASS   TSO.sales_order_reference
✅ PASS   WD.sales_order fetch_from
✅ PASS   WD.customer_name fetch_from
✅ PASS   DC.customer_name fetch_from
✅ PASS   Link validation (Pharma Customer)
----------------------------------------------------------------------
Total Tests: 7
✅ Passed:   7
❌ Failed:   0
⚠️  Skipped:  0
----------------------------------------------------------------------

🎉 ALL TESTS PASSED! 🎉
```

### Sample Data Verification
```python
# Successfully returns correct data:
{
  'name': 'TSO-2026-0001',
  'customer': 'fouad',
  'order_date': datetime.date(2026, 2, 1),
  'net_amount': 180.0,
  'customer_name': 'fouad'  # ✅ Correctly populated from legal_name
}
```

---

## 🚀 Deployment Steps Completed

1. ✅ Updated all JSON DocType definitions
2. ✅ Updated all Python query code
3. ✅ Ran `bench --site reunion.eg-smartplan.solutions migrate`
4. ✅ Ran `bench --site reunion.eg-smartplan.solutions clear-cache` (multiple times)
5. ✅ Restarted all services: `sudo supervisorctl restart all`
6. ✅ Verified with comprehensive automated test suite
7. ✅ All 7 tests passed

---

## 📊 Field Mapping Reference

### Custom DocTypes (smartplan_medical)
| DocType | Display Name Field | Used For |
|---------|-------------------|----------|
| **Pharma Customer** | `legal_name` | Customer names |
| **Pharma Supplier** | `legal_name` | Supplier names |
| **Pharma Item** | `item_name` | Item names |
| **Tele Sales Order** | `sales_order_reference` | Link to Sales Order |

### Core DocTypes (erpnext)
| DocType | Display Name Field |
|---------|-------------------|
| Customer | `customer_name` |
| Supplier | `supplier_name` |
| Item | `item_name` |
| Sales Order | `name` |

### Correct fetch_from Patterns

```python
# ✅ CUSTOM DOCTYPE LINKS
"fetch_from": "customer.legal_name"        # Pharma Customer
"fetch_from": "pharma_supplier.legal_name" # Pharma Supplier
"fetch_from": "item_code.item_name"        # Pharma Item
"fetch_from": "tele_sales_order.sales_order_reference"  # TSO -> SO

# ✅ CORE DOCTYPE LINKS
"fetch_from": "supplier.supplier_name"     # ERPNext Supplier
"fetch_from": "customer.customer_name"     # ERPNext Customer (NOT Pharma Customer!)
```

---

## 💡 Key Learnings

### 1. Custom vs Core DocTypes
- **Never assume** custom doctypes have same fields as core doctypes
- Always check actual field names in custom doctypes
- Use correct field names in fetch_from paths

### 2. Field Name Consistency
- Pharma Customer → `legal_name` (الاسم القانوني)
- ERPNext Customer → `customer_name`
- These are different fields on different doctypes!

### 3. Link Field Validation
- `fetch_from` paths are validated at runtime
- Invalid paths cause "Field not permitted in query" errors
- Always test link field selections after schema changes

### 4. Query Field Names
- Check actual field names in DocType JSON
- Don't use generic names like `posting_date` without verification
- Use DocType-specific field names (e.g., `order_date` in Tele Sales Order)

---

## ✅ Final Result

- ✅ No more "Field not permitted in query" errors
- ✅ All forms load correctly
- ✅ Customer names display properly
- ✅ Sales order references work
- ✅ Link field auto-fetch works
- ✅ All pending order queries return correct data
- ✅ 100% test pass rate (7/7 tests)

---

## 🔧 Troubleshooting Guide

If similar errors appear in future:

### Step 1: Identify the Field
Look at error message:
```
Field not permitted in query: FIELD_NAME
```

### Step 2: Check fetch_from Path
Find the field in DocType JSON:
```bash
grep -r "FIELD_NAME" apps/smartplan_medical/**/*.json
```

### Step 3: Verify Source DocType
Check what DocType the link field points to:
```json
{
  "fieldname": "customer",
  "fieldtype": "Link",
  "options": "Pharma Customer"  // ← This is the source DocType
}
```

### Step 4: Check Source Field Exists
Open the source DocType JSON and verify the field exists:
```bash
cat apps/smartplan_medical/.../pharma_customer/pharma_customer.json | grep legal_name
```

### Step 5: Update fetch_from
Fix the path to use the actual field name from source DocType

### Step 6: Migrate & Clear Cache
```bash
bench --site SITENAME migrate
bench --site SITENAME clear-cache
sudo supervisorctl restart all
```

---

## 📞 Support

**Test Scripts Available:**
- `test_all_links.py` - Comprehensive link validation test
- `test_customer_name_fix.py` - Customer name specific tests

**Documentation:**
- `FIX_CUSTOMER_NAME_ERROR.md` - Customer name fix details
- This document - Complete solution

**Quick Check Command:**
```bash
bench --site reunion.eg-smartplan.solutions execute \
  smartplan_medical.smartplan_medical.test_all_links.execute
```

---

**Fixed by:** GitHub Copilot  
**Date:** February 2, 2026  
**Status:** Production Ready ✅
