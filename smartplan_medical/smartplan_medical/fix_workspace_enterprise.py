import frappe
import json

def execute():
    """
    Create a professional Enterprise Workspace with Number Cards in English.
    """
    print("🚀 Creating English Enterprise Workspace with Number Cards...")

    # 1. Cleanup
    for ws in frappe.get_all("Workspace", filters={"name": "Pharma Cycle Management"}):
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ Deleted: {ws.name}")

    frappe.db.commit()

    # 2. Create Number Cards
    print("\n📊 Creating Number Cards...")
    
    cards_config = [
        ("Draft Orders", "Tele Sales Order", "Draft", "blue", "draft_orders_card"),
        ("Approved Orders", "Tele Sales Order", "Approved", "green", "approved_orders_card"),
        ("Dispatches", "Warehouse Dispatch", "Completed", "orange", "dispatches_card"),
        ("Today's Collections", "Customer Payment", None, "green", "today_collections_card"),
        ("Today's Supplier Payments", "Supplier Payment", None, "red", "today_supplier_payments_card"),
        ("Active Cashboxes", "Cashbox", "Active", "yellow", "active_cashboxes_card"),
    ]
    
    created_cards = []
    
    for label, doctype, status_filter, color, card_id in cards_config:
        # Delete card if exists
        if frappe.db.exists("Number Card", card_id):
            frappe.delete_doc("Number Card", card_id, force=1)
        
        card = frappe.new_doc("Number Card")
        card.name = card_id
        card.label = label
        card.document_type = doctype
        card.function = "Count"
        card.is_public = 1
        card.show_percentage_stats = 1
        card.stats_time_interval = "Daily"
        
        # Set filters
        filters = []
        if status_filter:
            filters.append([doctype, "status", "=", status_filter])
        
        # Date filter for collections and payments
        if "Today" in label or "اليوم" in label:
            filters.append([doctype, "posting_date", "=", "Today"])
        
        if filters:
            card.filters_json = json.dumps(filters)
        
        try:
            card.insert(ignore_permissions=True)
            created_cards.append(card_id)
            print(f"   ✅ {label} -> {card_id}")
        except Exception as e:
            print(f"   ❌ Failed {label}: {str(e)}")

    frappe.db.commit()

    # 3. Create Workspace
    print("\n🏢 Creating Workspace...")
    
    ws = frappe.new_doc("Workspace")
    ws.name = "Pharma Cycle Management"
    ws.label = "Pharma Cycle Management"
    ws.title = "Pharma Cycle Management"
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.indicator_color = "blue"
    ws.public = 1
    ws.is_hidden = 0
    
    # 4. Content JSON with embedded Number Cards (English)
    content = [
        # Dashboard Section
        {"type": "header", "data": {"text": "📊 Dashboard", "col": 12}},
        {"type": "number_card", "data": {"number_card_name": "draft_orders_card", "col": 4}},
        {"type": "number_card", "data": {"number_card_name": "approved_orders_card", "col": 4}},
        {"type": "number_card", "data": {"number_card_name": "dispatches_card", "col": 4}},
        {"type": "number_card", "data": {"number_card_name": "today_collections_card", "col": 4}},
        {"type": "number_card", "data": {"number_card_name": "today_supplier_payments_card", "col": 4}},
        {"type": "number_card", "data": {"number_card_name": "active_cashboxes_card", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Sales Operations
        {"type": "header", "data": {"text": "🛒 Sales Operations", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Tele Sales Orders", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Inventory Dispatch", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Delivery & Collection", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Inventory Management
        {"type": "header", "data": {"text": "📦 Inventory Management", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Warehouses", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Pharma Items", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Customers & Sales
        {"type": "header", "data": {"text": "👥 Customers & Sales", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Customers", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Sales Team", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Commission Calculation", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Financial Management
        {"type": "header", "data": {"text": "💰 Financial Management", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Customer Payments", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Supplier Payments", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Cashboxes", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Daily Closing", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Reports
        {"type": "header", "data": {"text": "📈 Reports", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Sales By Employee", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Customer Aging", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "Supplier Aging", "col": 4}},
    ]
    
    ws.content = json.dumps(content)

    # 5. Shortcuts (Labels updated to English)
    shortcuts_config = [
        ("Tele Sales Order", "Tele Sales Orders", "Red", "DocType"),
        ("Warehouse Dispatch", "Inventory Dispatch", "Orange", "DocType"),
        ("Delivery Collection", "Delivery & Collection", "Green", "DocType"),
        ("Pharma Warehouse", "Warehouses", "Blue", "DocType"),
        ("Pharma Item", "Pharma Items", "Purple", "DocType"),
        ("Pharma Customer", "Customers", "Green", "DocType"),
        ("Tele Sales Team", "Sales Team", "Orange", "DocType"),
        ("Commission Calculation", "Commission Calculation", "Blue", "DocType"),
        ("Customer Payment", "Customer Payments", "Green", "DocType"),
        ("Supplier Payment", "Supplier Payments", "Red", "DocType"),
        ("Cashbox", "Cashboxes", "Yellow", "DocType"),
        ("Daily Closing", "Daily Closing", "Purple", "DocType"),
        ("Sales By Employee Report", "Sales By Employee", "Green", "Report"),
        ("Customer Aging Report", "Customer Aging", "Orange", "Report"),
        ("Supplier Aging Report", "Supplier Aging", "Red", "Report"),
    ]

    for link_to, label, color, link_type in shortcuts_config:
        ws.append("shortcuts", {
            "type": link_type,
            "link_to": link_to,
            "label": label,
            "doc_view": "List" if link_type == "DocType" else "",
            "color": color
        })

    try:
        ws.insert(ignore_permissions=True)
        print(f"✅ English Workspace created successfully!")
    except Exception as e:
        print(f"❌ Failed to create Workspace: {str(e)}")

    frappe.db.commit()
    frappe.clear_cache()
    print("\n✅ Done - Refresh your browser and check the workspace!")
