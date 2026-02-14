"""
Setup script to create Reunion Sales Invoice Print Format
"""
import frappe
import os


def execute():
    """Create or update the Reunion Sales Invoice Print Format"""

    print_format_name = "Reunion Sales Invoice"

    # Read the HTML template
    app_path = frappe.get_app_path("smartplan_medical")
    html_path = os.path.join(app_path, "print_formats", "reunion_sales_invoice.html")

    if not os.path.exists(html_path):
        frappe.throw(f"HTML template not found at {html_path}")

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Check if print format already exists
    if frappe.db.exists("Print Format", print_format_name):
        print(f"  ℹ️  Print Format '{print_format_name}' already exists. Updating...")
        pf = frappe.get_doc("Print Format", print_format_name)
        pf.html = html_content
        pf.save()
        print(f"  ✅ Updated Print Format: {print_format_name}")
    else:
        print(f"  ℹ️  Creating new Print Format: {print_format_name}")
        pf = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": print_format_name,
                "doc_type": "Sales Invoice",
                "module": "Smartplan Medical",
                "standard": "No",
                "custom_format": 1,
                "html": html_content,
                "print_format_type": "Jinja",
                "print_format_builder": 0,
                "align_labels_right": 1,
                "show_section_headings": 0,
                "line_breaks": 0,
            }
        )
        pf.insert()
        print(f"  ✅ Created Print Format: {print_format_name}")

    frappe.db.commit()
    print(f"\n🎉 Reunion Sales Invoice Print Format is ready!")
    print(f"   Go to any Sales Invoice → Print → Select '{print_format_name}'")
