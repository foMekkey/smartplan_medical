import frappe
import json

def execute():
    """
    Create a professional Arabic Enterprise Workspace with Number Cards.
    """
    print("🚀 Creating Arabic Enterprise Workspace with Number Cards...")

    # 1. Cleanup
    for ws in frappe.get_all("Workspace", filters={"name": "Pharma Cycle Management"}):
        frappe.delete_doc("Workspace", ws.name, force=1)
        print(f"🗑️ Deleted: {ws.name}")

    frappe.db.commit()

    # 2. Create Number Cards (Arabic Labels)
    print("\n📊 Creating Number Cards...")
    
    cards_config = [
        # التشغيلية
        ("طلبات مسودة", "Tele Sales Order", "Draft", "blue", "draft_orders_card_ar"),
        ("طلبات معتمدة", "Tele Sales Order", "Approved", "green", "approved_orders_card_ar"),
        ("صرف مخزني مكتمل", "Warehouse Dispatch", "Completed", "orange", "dispatches_card_ar"),
        ("تحصيلات اليوم", "Customer Payment", None, "green", "today_collections_card_ar"),
        
        # الإغلاق اليومي
        ("مدفوعات الموردين اليوم", "Supplier Payment", None, "red", "today_supplier_payments_card_ar"),
        ("خزائن نشطة", "Cashbox", "Active", "yellow", "active_cashboxes_card_ar"),
        
        # استثنائية
        ("عمليات فاشلة", "Pharma Process Log", "Failed", "red", "failed_process_card_ar"),
        ("موافقات معلقة", "Pharma Approval Request", "Pending", "orange", "pending_approvals_card_ar"),
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
        card.color = color
        
        # Set filters
        filters = []
        if status_filter:
            filters.append([doctype, "status", "=", status_filter])
        
        # Date filter for collections and payments
        if "اليوم" in label:
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
    ws.label = "إدارة دورة شركة الأدوية"
    ws.title = "إدارة دورة شركة الأدوية"
    ws.module = "Smartplan Medical"
    ws.icon = "healthcare"
    ws.indicator_color = "blue"
    ws.public = 1
    ws.is_hidden = 0
    
    # 4. Content JSON with embedded Number Cards (Arabic)
    content = [
        # Banner for Rules
        {"type": "header", "data": {"text": "⚠️ قواعد صارمة: أقصى خصم 15% - سياسة FEFO مفعلة - ممنوع المخزون السالب", "col": 12}},
        
        # Operational Status
        {"type": "header", "data": {"text": "📊 الحالة التشغيلية", "col": 12}},
        {"type": "number_card", "data": {"number_card_name": "draft_orders_card_ar", "col": 3}},
        {"type": "number_card", "data": {"number_card_name": "approved_orders_card_ar", "col": 3}},
        {"type": "number_card", "data": {"number_card_name": "dispatches_card_ar", "col": 3}},
        {"type": "number_card", "data": {"number_card_name": "today_collections_card_ar", "col": 3}},
        {"type": "spacer", "data": {"col": 12}},

        # Exceptional Status
        {"type": "header", "data": {"text": "🚨 الحالات الاستثنائية", "col": 12}},
        {"type": "number_card", "data": {"number_card_name": "failed_process_card_ar", "col": 6}},
        {"type": "number_card", "data": {"number_card_name": "pending_approvals_card_ar", "col": 6}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Ownership / Operations
        {"type": "header", "data": {"text": "🏢 العمليات والملكية", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "المبيعات الهاتفية", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "إدارة المخازن", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "التوصيل والتحصيل", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Purchasing
        {"type": "header", "data": {"text": "🛍️ المشتريات والموردين", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "دورة الشراء", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "الموردين", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "سداد الموردين", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},

        # Daily Closing
        {"type": "header", "data": {"text": "💰 الإغلاق اليومي والخزينة", "col": 12}},
        {"type": "number_card", "data": {"number_card_name": "today_supplier_payments_card_ar", "col": 6}},
        {"type": "number_card", "data": {"number_card_name": "active_cashboxes_card_ar", "col": 6}},
        {"type": "shortcut", "data": {"shortcut_name": "الخزائن", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "الإغلاق اليومي", "col": 4}},
        {"type": "shortcut", "data": {"shortcut_name": "العمليات البنكية", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        
        # Reports
        {"type": "header", "data": {"text": "📈 التقارير", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير المخزون", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير العملاء", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "تقرير الموردين", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "ميزان المراجعة", "col": 3}},
    ]
    
    ws.content = json.dumps(content)

    # 5. Shortcuts (Labels in Arabic)
    shortcuts_config = [
        # Sales
        ("Tele Sales Order", "المبيعات الهاتفية", "Red", "DocType"),
        ("Delivery Collection", "التوصيل والتحصيل", "Green", "DocType"),
        
        # Inventory
        ("Pharma Warehouse", "إدارة المخازن", "Blue", "DocType"),
        
        # Purchasing
        ("Pharma Purchase Cycle", "دورة الشراء", "Orange", "DocType"),
        ("Pharma Supplier", "الموردين", "Orange", "DocType"),
        ("Supplier Payment", "سداد الموردين", "Red", "DocType"),
        
        # Finance
        ("Cashbox", "الخزائن", "Yellow", "DocType"),
        ("Daily Closing", "الإغلاق اليومي", "Purple", "DocType"),
        ("Bank Transaction", "العمليات البنكية", "Green", "DocType"), # Assuming this exists or falls back
        
        # Reports
        ("Stock Balance", "تقرير المخزون", "Blue", "Report"),
        ("Customer Aging Report", "تقرير العملاء", "Orange", "Report"),
        ("Supplier Aging Report", "تقرير الموردين", "Red", "Report"),
        ("General Ledger", "ميزان المراجعة", "Green", "Report"),
    ]

    for link_to, label, color, link_type in shortcuts_config:
        # Check if DocType/Report exists first to avoid errors
        if link_type == "DocType" and not frappe.db.exists("DocType", link_to):
             print(f"⚠️ Skipping Shortcut {label}: DocType {link_to} does not exist.")
             continue
        if link_type == "Report" and not frappe.db.exists("Report", link_to):
             print(f"⚠️ Skipping Shortcut {label}: Report {link_to} does not exist.")
             continue

        ws.append("shortcuts", {
            "type": link_type,
            "link_to": link_to,
            "label": label,
            "doc_view": "List" if link_type == "DocType" else "",
            "color": color
        })

    try:
        ws.insert(ignore_permissions=True)
        print(f"✅ Arabic Workspace created successfully!")
    except Exception as e:
        print(f"❌ Failed to create Workspace: {str(e)}")

    frappe.db.commit()
    frappe.clear_cache()
    print("\n✅ Done - Refresh your browser and check the workspace!")
