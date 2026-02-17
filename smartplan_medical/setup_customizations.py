"""
Setup all custom fields, property setters, and other customizations for smartplan_medical.
This runs on `after_migrate` so all customizations are managed via code,
not through the database UI.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def after_migrate():
    """Called after bench migrate — ensures all customizations exist."""
    create_sales_order_custom_fields()
    create_customer_custom_fields()
    create_supplier_custom_fields()
    create_purchase_order_custom_fields()
    create_batch_custom_fields()
    create_selling_settings_fields()
    create_stock_reservation_fields()
    create_property_setters()
    create_client_scripts()
    populate_egypt_regions()
    populate_customer_classifications()
    frappe.db.commit()


def create_sales_order_custom_fields():
    """Create all custom fields for Sales Order and Sales Order Item."""
    fields = {
        "Sales Order": [
            {
                "fieldname": "custom_customer_balance",
                "fieldtype": "Currency",
                "label": "Customer Balance",
                "insert_after": "customer",
                "read_only": 1,
            },
            {
                "fieldname": "custom_sales_person",
                "fieldtype": "Link",
                "label": "Sales Person",
                "options": "Employee",
                "insert_after": "delivery_date",
                "reqd": 1,
            },
            {
                "fieldname": "custom_total_before_discount",
                "fieldtype": "Currency",
                "label": "الإجمالي قبل الخصم",
                "insert_after": "total",
                "read_only": 1,
                "bold": 1,
            },
            {
                "fieldname": "custom_total_discount_amount",
                "fieldtype": "Currency",
                "label": "Total Discount Amount",
                "insert_after": "custom_total_before_discount",
                "read_only": 1,
            },
        ],
        "Sales Order Item": [
            {
                "fieldname": "custom_available_qty",
                "fieldtype": "Float",
                "label": "Available Qty",
                "insert_after": "stock_uom",
                "read_only": 1,
            },
            {
                "fieldname": "custom_reserved_qty",
                "fieldtype": "Float",
                "label": "Reserved Qty",
                "insert_after": "custom_available_qty",
                "read_only": 1,
            },
            {
                "fieldname": "custom_price_before_discount",
                "fieldtype": "Currency",
                "label": "السعر قبل الخصم",
                "insert_after": "rate",
                "read_only": 1,
                "bold": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "custom_discount_",
                "fieldtype": "Percent",
                "label": "Discount %",
                "insert_after": "custom_price_before_discount",
            },
        ],
    }

    create_custom_fields(fields, update=True)


def create_customer_custom_fields():
    """Create custom fields for Customer — region, commercial registration."""
    fields = {
        "Customer": [
            {
                "fieldname": "custom_section_region",
                "fieldtype": "Section Break",
                "label": "المنطقة / Region",
                "insert_after": "customer_group",
                "collapsible": 0,
            },
            {
                "fieldname": "custom_governorate",
                "fieldtype": "Link",
                "label": "المحافظة",
                "options": "Governorate",
                "insert_after": "custom_section_region",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "reqd": 1,
            },
            {
                "fieldname": "custom_city",
                "fieldtype": "Link",
                "label": "المدينة/المركز",
                "options": "City",
                "insert_after": "custom_governorate",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "reqd": 1,
            },
            {
                "fieldname": "custom_column_break_region",
                "fieldtype": "Column Break",
                "insert_after": "custom_city",
            },
            {
                "fieldname": "custom_commercial_registration",
                "fieldtype": "Data",
                "label": "السجل التجاري",
                "insert_after": "custom_column_break_region",
                "translatable": 0,
                "reqd": 1,
            },
            {
                "fieldname": "custom_classification",
                "fieldtype": "Link",
                "label": "تصنيف العميل (Classification)",
                "options": "Customer Classification",
                "insert_after": "custom_commercial_registration",
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
        ],
    }

    create_custom_fields(fields, update=True)


def create_supplier_custom_fields():
    """Create custom fields for Supplier — region, commercial registration, tax card, etc."""
    fields = {
        "Supplier": [
            {
                "fieldname": "custom_section_supplier_info",
                "fieldtype": "Section Break",
                "label": "بيانات المورد / Supplier Info",
                "insert_after": "supplier_group",
                "collapsible": 0,
            },
            {
                "fieldname": "custom_governorate",
                "fieldtype": "Link",
                "label": "المحافظة",
                "options": "Governorate",
                "insert_after": "custom_section_supplier_info",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "reqd": 1,
            },
            {
                "fieldname": "custom_city",
                "fieldtype": "Link",
                "label": "المدينة/المركز",
                "options": "City",
                "insert_after": "custom_governorate",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "reqd": 1,
            },
            {
                "fieldname": "custom_area",
                "fieldtype": "Data",
                "label": "المنطقة",
                "insert_after": "custom_city",
            },
            {
                "fieldname": "custom_column_break_supplier",
                "fieldtype": "Column Break",
                "insert_after": "custom_area",
            },
            {
                "fieldname": "custom_commercial_registration",
                "fieldtype": "Data",
                "label": "رقم السجل التجاري",
                "insert_after": "custom_column_break_supplier",
                "translatable": 0,
            },
            {
                "fieldname": "custom_tax_card",
                "fieldtype": "Data",
                "label": "رقم البطاقة الضريبية",
                "insert_after": "custom_commercial_registration",
                "translatable": 0,
            },
            {
                "fieldname": "custom_mobile",
                "fieldtype": "Data",
                "label": "رقم الجوال",
                "options": "Phone",
                "insert_after": "custom_tax_card",
            },
            {
                "fieldname": "custom_operating_license",
                "fieldtype": "Data",
                "label": "رقم رخصة التشغيل",
                "insert_after": "custom_mobile",
                "translatable": 0,
            },
        ],
    }

    create_custom_fields(fields, update=True)


def create_purchase_order_custom_fields():
    """Create custom fields for Purchase Order — discount, same as Sales Order."""
    fields = {
        "Purchase Order": [
            {
                "fieldname": "custom_total_before_discount",
                "fieldtype": "Currency",
                "label": "الإجمالي قبل الخصم",
                "insert_after": "total",
                "read_only": 1,
                "bold": 1,
            },
            {
                "fieldname": "custom_total_discount_amount",
                "fieldtype": "Currency",
                "label": "Total Discount Amount",
                "insert_after": "custom_total_before_discount",
                "read_only": 1,
            },
        ],
        "Purchase Order Item": [
            {
                "fieldname": "custom_price_before_discount",
                "fieldtype": "Currency",
                "label": "السعر قبل الخصم",
                "insert_after": "rate",
                "read_only": 1,
                "bold": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "custom_discount_",
                "fieldtype": "Percent",
                "label": "Discount %",
                "insert_after": "custom_price_before_discount",
            },
            {
                "fieldname": "custom_batch_no",
                "fieldtype": "Link",
                "label": "Batch No",
                "options": "Batch",
                "insert_after": "custom_discount_",
                "in_list_view": 1,
            },
            {
                "fieldname": "custom_serial_no",
                "fieldtype": "Data",
                "label": "Serial No",
                "insert_after": "custom_batch_no",
            },
        ],
    }

    create_custom_fields(fields, update=True)


def create_selling_settings_fields():
    """Add auto-cancel timeout setting to Selling Settings."""
    fields = {
        "Selling Settings": [
            {
                "fieldname": "custom_so_auto_cancel_section",
                "fieldtype": "Section Break",
                "label": "Auto-Cancel Draft Sales Orders",
                "insert_after": "close_opportunity_after_days",
            },
            {
                "fieldname": "custom_so_auto_cancel_hours",
                "fieldtype": "Float",
                "label": "Auto-Cancel After (Hours)",
                "default": "2",
                "description": "Draft Sales Orders will be auto-deleted and their reserved stock released after this many hours. Set 0 to disable.",
                "insert_after": "custom_so_auto_cancel_section",
            },
        ],
    }
    create_custom_fields(fields, update=True)


def create_batch_custom_fields():
    """Create custom fields for Batch — target warehouse."""
    fields = {
        "Batch": [
            {
                "fieldname": "custom_target_warehouse",
                "fieldtype": "Link",
                "label": "المخزن المستهدف (Target Warehouse)",
                "options": "Warehouse",
                "insert_after": "supplier",
                "reqd": 1,
                "in_list_view": 1,
            },
        ],
    }
    create_custom_fields(fields, update=True)


def create_stock_reservation_fields():
    """Add sales_order field to Stock Reservation DocType."""
    fields = {
        "Stock Reservation": [
            {
                "fieldname": "sales_order",
                "fieldtype": "Link",
                "label": "Sales Order",
                "options": "Sales Order",
                "insert_after": "sales_invoice",
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
        ],
    }
    create_custom_fields(fields, update=True)


def create_property_setters():
    """Create property setters for Sales Order and Customer."""
    # Make Set Source Warehouse required on Sales Order
    make_property_setter(
        "Sales Order", "set_warehouse", "reqd", 1, "Check",
        validate_fields_for_doctype=False
    )

    # Make Set Target Warehouse required on Purchase Order
    make_property_setter(
        "Purchase Order", "set_warehouse", "reqd", 1, "Check",
        validate_fields_for_doctype=False
    )

    # Make delivery_date NOT required on Sales Order Item
    make_property_setter(
        "Sales Order Item", "delivery_date", "reqd", 0, "Check",
        validate_fields_for_doctype=False
    )
    make_property_setter(
        "Sales Order Item", "delivery_date", "in_list_view", 0, "Check",
        validate_fields_for_doctype=False
    )
    # Also on parent Sales Order
    make_property_setter(
        "Sales Order", "delivery_date", "reqd", 0, "Check",
        validate_fields_for_doctype=False
    )

    # Remove unique constraint from tax_id on Customer
    make_property_setter(
        "Customer", "tax_id", "unique", 0, "Check",
        validate_fields_for_doctype=False
    )

    # Make Discount % required on Sales Order Item
    make_property_setter(
        "Sales Order Item", "custom_discount_", "reqd", 1, "Check",
        validate_fields_for_doctype=False
    )

    # Make Discount % required on Purchase Order Item
    make_property_setter(
        "Purchase Order Item", "custom_discount_", "reqd", 1, "Check",
        validate_fields_for_doctype=False
    )

    # ---- Batch Quick Entry: show all relevant fields ----
    batch_quick_fields = [
        "batch_id", "item", "manufacturing_date", "expiry_date",
        "supplier", "description", "custom_target_warehouse",
    ]
    for fn in batch_quick_fields:
        make_property_setter(
            "Batch", fn, "allow_in_quick_entry", 1, "Check",
            validate_fields_for_doctype=False
        )


def populate_egypt_regions():
    """Populate Egyptian governorates and cities if the DocTypes exist."""
    if not frappe.db.exists("DocType", "Governorate"):
        return
    if not frappe.db.exists("DocType", "City"):
        return

    # Only run if no governorates exist yet (first-time setup)
    if frappe.db.count("Governorate") > 0:
        return

    from smartplan_medical.populate_egypt_regions import populate
    populate()


def populate_customer_classifications():
    """Populate default customer classifications if none exist."""
    if not frappe.db.exists("DocType", "Customer Classification"):
        return
    if frappe.db.count("Customer Classification") > 0:
        return

    for name in ["Class A", "Class B", "Class C"]:
        doc = frappe.new_doc("Customer Classification")
        doc.classification_name = name
        doc.insert(ignore_permissions=True)
    frappe.db.commit()


def create_client_scripts():
    """Create/update Client Scripts managed from code."""
    customer_filter_script = """
frappe.ui.form.on("Customer", {
    setup(frm) {
        frm.set_query("custom_city", function () {
            if (frm.doc.custom_governorate) {
                return {
                    filters: {
                        governorate: frm.doc.custom_governorate
                    }
                };
            }
            return {};
        });
    },

    refresh(frm) {
        frm.set_query("custom_city", function () {
            if (frm.doc.custom_governorate) {
                return {
                    filters: {
                        governorate: frm.doc.custom_governorate
                    }
                };
            }
            return {};
        });
    },

    custom_governorate(frm) {
        frm.set_value("custom_city", "");
    }
});
""".strip()

    _upsert_client_script("SPS - Customer Region Filter", "Customer", customer_filter_script)

    # Supplier region filter script (same pattern as Customer)
    supplier_filter_script = """
frappe.ui.form.on("Supplier", {
    setup(frm) {
        frm.set_query("custom_city", function () {
            if (frm.doc.custom_governorate) {
                return {
                    filters: {
                        governorate: frm.doc.custom_governorate
                    }
                };
            }
            return {};
        });
    },

    refresh(frm) {
        frm.set_query("custom_city", function () {
            if (frm.doc.custom_governorate) {
                return {
                    filters: {
                        governorate: frm.doc.custom_governorate
                    }
                };
            }
            return {};
        });
    },

    custom_governorate(frm) {
        frm.set_value("custom_city", "");
    }
});
""".strip()

    _upsert_client_script("SPS - Supplier Region Filter", "Supplier", supplier_filter_script)


def _upsert_client_script(script_name, doctype, script_content):
    """Create or update a Client Script."""
    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = script_content
        doc.enabled = 1
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "name": script_name,
            "dt": doctype,
            "view": "Form",
            "enabled": 1,
            "script": script_content,
        })
        doc.insert(ignore_permissions=True)
