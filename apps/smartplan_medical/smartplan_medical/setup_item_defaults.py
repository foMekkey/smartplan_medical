"""
Setup Property Setters for ERPNext Item DocType:
1. has_batch_no -> default = 1
2. has_expiry_date -> default = 1
3. serial_nos_and_batches section -> always expanded (collapsible = 0)
"""
import frappe


def execute():
    """Apply Property Setters to customize Item DocType for this site only."""

    property_setters = [
        {
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": "Item",
            "field_name": "has_batch_no",
            "property": "default",
            "value": "1",
            "property_type": "Text",
            "name": "Item-has_batch_no-default",
        },
        {
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": "Item",
            "field_name": "has_expiry_date",
            "property": "default",
            "value": "1",
            "property_type": "Text",
            "name": "Item-has_expiry_date-default",
        },
        {
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": "Item",
            "field_name": "serial_nos_and_batches",
            "property": "collapsible",
            "value": "0",
            "property_type": "Check",
            "name": "Item-serial_nos_and_batches-collapsible",
        },
        {
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": "Item",
            "field_name": "serial_nos_and_batches",
            "property": "collapsible_depends_on",
            "value": "",
            "property_type": "Data",
            "name": "Item-serial_nos_and_batches-collapsible_depends_on",
        },
    ]

    for ps in property_setters:
        if frappe.db.exists("Property Setter", ps["name"]):
            doc = frappe.get_doc("Property Setter", ps["name"])
            doc.value = ps["value"]
            doc.save()
            print(f"  ✅ Updated: {ps['name']} = {ps['value']}")
        else:
            doc = frappe.get_doc(ps)
            doc.insert()
            print(f"  ✅ Created: {ps['name']} = {ps['value']}")

    frappe.db.commit()
    print("\n🎉 All Property Setters applied successfully!")
    print("   - has_batch_no: default = 1 (checked)")
    print("   - has_expiry_date: default = 1 (checked)")
    print("   - Serial Nos and Batches section: always expanded")
