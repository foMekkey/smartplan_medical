
import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    """
    Enable 'Allow in Quick Entry' for Item Batch and Expiry fields
    """
    fields_to_enable = [
        "has_batch_no",
        "has_expiry_date"
    ]

    for field in fields_to_enable:
        make_property_setter(
            "Item",
            field,
            "allow_in_quick_entry",
            1,
            "Check"
        )
        print(f"  ✅ Enabled Quick Entry for Item field: {field}")

    # Set Default UOM to 'Box'
    make_property_setter(
        "Item",
        "stock_uom",
        "default",
        "Box",
        "Data" # or Link? Default value is stored as Data/Small Text usually.
    )
    print("  ✅ Set Default Unit of Measure to 'Box'")

    # Set Default Shelf Life to 9000
    make_property_setter(
        "Item",
        "shelf_life_in_days",
        "default",
        "9000",
        "Int"
    )
    print("  ✅ Set Default Shelf Life to 9000")

    frappe.db.commit()
    print("\n🎉 Item Quick Entry updated!")
