# 🎯 Quick Reference: Field Mapping Cheat Sheet

## Custom DocType Fields (smartplan_medical)

```
┌─────────────────────────────────────────────────────────────┐
│ DocType: Pharma Customer                                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ USE: legal_name                                          │
│ ❌ NOT: customer_name                                       │
│                                                              │
│ Example:                                                     │
│ "fetch_from": "customer.legal_name"                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DocType: Pharma Supplier                                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ USE: legal_name                                          │
│ ❌ NOT: supplier_name                                       │
│                                                              │
│ Example:                                                     │
│ "fetch_from": "pharma_supplier.legal_name"                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DocType: Tele Sales Order                                   │
├─────────────────────────────────────────────────────────────┤
│ ✅ USE: sales_order_reference (for Sales Order link)       │
│ ❌ NOT: sales_order                                         │
│                                                              │
│ ✅ USE: order_date                                          │
│ ❌ NOT: posting_date                                        │
│                                                              │
│ Example:                                                     │
│ "fetch_from": "tele_sales_order.sales_order_reference"      │
└─────────────────────────────────────────────────────────────┘
```

## Core ERPNext DocType Fields

```
┌─────────────────────────────────────────────────────────────┐
│ DocType: Customer (ERPNext Core)                            │
├─────────────────────────────────────────────────────────────┤
│ ✅ USE: customer_name                                       │
│                                                              │
│ ⚠️  WARNING: Only use when linking to core Customer,       │
│             NOT when linking to Pharma Customer!            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DocType: Supplier (ERPNext Core)                            │
├─────────────────────────────────────────────────────────────┤
│ ✅ USE: supplier_name                                       │
│                                                              │
│ ⚠️  WARNING: Only use when linking to core Supplier,       │
│             NOT when linking to Pharma Supplier!            │
└─────────────────────────────────────────────────────────────┘
```

## Common Mistakes & Fixes

```python
# ❌ WRONG - Linking to custom doctype but using core field name
{
  "fieldname": "customer",
  "options": "Pharma Customer",  # Custom DocType
  "fetch_from": "customer.customer_name"  # ❌ This field doesn't exist!
}

# ✅ CORRECT - Use actual field from custom doctype
{
  "fieldname": "customer",
  "options": "Pharma Customer",
  "fetch_from": "customer.legal_name"  # ✅ Correct!
}
```

```python
# ❌ WRONG - Using wrong field name in queries
orders = frappe.get_all(
    "Tele Sales Order",
    fields=["name", "posting_date"]  # ❌ doesn't exist
)

# ✅ CORRECT
orders = frappe.get_all(
    "Tele Sales Order",
    fields=["name", "order_date"]  # ✅ Correct!
)
```

```python
# ❌ WRONG - Querying wrong doctype for display name
customer_name = frappe.db.get_value(
    "Customer",  # ❌ Wrong! This is ERPNext core
    customer_id,
    "customer_name"
)

# ✅ CORRECT - Query the actual linked doctype
customer_name = frappe.db.get_value(
    "Pharma Customer",  # ✅ Custom doctype
    customer_id,
    "legal_name"  # ✅ Actual field name
)
```

## Quick Diagnostic Steps

```bash
# 1. Find which doctype the link points to
grep -A5 '"fieldname": "FIELDNAME"' path/to/doctype.json | grep options

# 2. Check what fields exist in that doctype
cat path/to/linked_doctype.json | grep fieldname | sort

# 3. Verify fetch_from path
grep -B2 -A2 '"fieldname": "FIELDNAME"' path/to/doctype.json

# 4. Test after fix
bench --site SITE migrate
bench --site SITE clear-cache
bench --site SITE execute smartplan_medical.smartplan_medical.test_all_links.execute
```

## Field Name Translation

| Arabic Label | English Field Name | DocType |
|--------------|-------------------|---------|
| الاسم القانوني | `legal_name` | Pharma Customer/Supplier |
| العميل | `customer` | Link field |
| اسم العميل | `customer_name` | Display field |
| تاريخ الطلب | `order_date` | Tele Sales Order |
| مرجع أمر البيع | `sales_order_reference` | Tele Sales Order |

## Remember

1. ✅ Always check the **actual DocType** a link field points to
2. ✅ Use field names from that **specific DocType**
3. ✅ Custom doctypes may have **different field names** than core
4. ✅ Test with `test_all_links.py` after any schema change
5. ✅ Clear cache after migrations

---

**Last Updated:** February 2, 2026  
**All fixes verified and tested ✅**
