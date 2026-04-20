from . import __version__ as app_version

app_name = "smartplan_medical"
app_title = "SmartPlan Medical"
app_publisher = "SmartPlan Solutions"
app_description = "Production-grade Progressive Web App layer for ERPNext"
app_email = "dev@eg-smartplan.solutions"
app_license = "MIT"

required_apps = ["frappe", "erpnext"]

# ──────────────────────────────────────────────
# PWA INCLUDES — Injected into Desk <head>
# ──────────────────────────────────────────────

app_include_js = [
    "pwa.bundle.js",
    "mobile_ux.bundle.js",
]

app_include_css = [
    "smartplan_pwa.bundle.css",
]

# ──────────────────────────────────────────────
# WEBSITE / LOGIN PAGE INCLUDES
# ──────────────────────────────────────────────

web_include_css = [
    "/assets/smartplan_medical/css/smartplan_login.css",
]

web_include_js = [
    "/assets/smartplan_medical/js/smartplan_web_pwa.js",
]

# ──────────────────────────────────────────────
# BRANDING CONTEXT (favicon, splash)
# ──────────────────────────────────────────────

website_context = {
    "favicon": "/assets/smartplan_medical/icons/icon-192x192.png",
    "splash_image": "/assets/smartplan_medical/icons/icon-512x512.png",
}

# ──────────────────────────────────────────────
# EXTEND BOOT INFO (inject PWA config to client)
# ──────────────────────────────────────────────

extend_bootinfo = "smartplan_medical.api.extend_bootinfo"

# ──────────────────────────────────────────────
# OVERRIDE app.html — Inject manifest + SW registration
# via Jinja override
# ──────────────────────────────────────────────

override_doctype_class = {}

doctype_js = {
    "Sales Order": "public/js/sales_order_custom.js",
    "Purchase Order": "public/js/purchase_order_custom.js",
    "Customer": "public/js/customer_custom.js"
}
# Inject PWA <head> content via website_context
update_website_context = "smartplan_medical.api.update_website_context"

# ──────────────────────────────────────────────
# APP ICONS
# ──────────────────────────────────────────────

app_logo_url = "/assets/smartplan_medical/icons/icon-192x192.png"

# ──────────────────────────────────────────────
# JINJA — Make PWA helpers available in templates
# ──────────────────────────────────────────────

jinja = {
    "methods": [
        "smartplan_medical.api.get_pwa_meta_tags",
    ],
}

# ──────────────────────────────────────────────
# AFTER INSTALL — Setup PWA assets
# ──────────────────────────────────────────────

after_install = "smartplan_medical.api.after_install"

# ──────────────────────────────────────────────
# STANDARD HOOKS (template — kept for future use)
# ──────────────────────────────────────────────

# Home Pages
# home_page = "login"

# Desk Notifications
# notification_config = "smartplan_medical.notifications.get_notification_config"

# ──────────────────────────────────────────────
# DOCUMENT EVENTS (restored from original app)
# ──────────────────────────────────────────────

doc_events = {
    "Warehouse Dispatch": {
        "on_submit": "smartplan_medical.smartplan_medical.doctype.pharma_process_log.pharma_process_log.create_process_log_on_dispatch",
        "validate": "smartplan_medical.smartplan_medical.utils.validate_dispatch"
    },
    "Delivery Collection": {
        "on_submit": "smartplan_medical.smartplan_medical.doctype.pharma_process_log.pharma_process_log.create_process_log_on_collection",
        "validate": "smartplan_medical.smartplan_medical.utils.validate_collection"
    },
    "Tele Sales Order": {
        "validate": "smartplan_medical.smartplan_medical.utils.validate_tele_sales_order"
    },
    "Sales Order": {
        "before_validate": "smartplan_medical.sales_order_events.before_validate",
        "before_save": "smartplan_medical.sales_order_events.before_save",
        "after_save": "smartplan_medical.sales_order_events.after_save",
        "on_submit": "smartplan_medical.sales_order_events.on_submit",
        "after_cancel": "smartplan_medical.sales_order_events.after_cancel",
        "before_insert": "smartplan_medical.sales_order_events.before_insert"
    },
    "Purchase Order": {
        "before_save": "smartplan_medical.purchase_order_events.before_save",
        "before_insert": "smartplan_medical.purchase_order_events.before_insert",
        "on_submit": "smartplan_medical.purchase_order_events.on_submit"
    },
    "Customer": {
        "after_save": "smartplan_medical.customer_events.after_save"
    },
    "Purchase Invoice": {
        "on_submit": "smartplan_medical.realtime_events.on_stock_change",
        "on_cancel": "smartplan_medical.realtime_events.on_stock_change"
    },
    "Sales Invoice": {
        "on_submit": "smartplan_medical.realtime_events.on_stock_change",
        "on_cancel": "smartplan_medical.realtime_events.on_stock_change"
    },
    "Stock Entry": {
        "on_submit": "smartplan_medical.realtime_events.on_stock_change",
        "on_cancel": "smartplan_medical.realtime_events.on_stock_change"
    },
    "Delivery Note": {
        "on_submit": "smartplan_medical.realtime_events.on_stock_change",
        "on_cancel": "smartplan_medical.realtime_events.on_stock_change"
    },
    "Purchase Receipt": {
        "on_submit": "smartplan_medical.realtime_events.on_stock_change",
        "on_cancel": "smartplan_medical.realtime_events.on_stock_change"
    }
}

# ──────────────────────────────────────────────
# SCHEDULED TASKS (restored from original app)
# ──────────────────────────────────────────────

scheduler_events = {
    "cron": {
        "*/15 * * * *": [
            "smartplan_medical.auto_cancel_orders.auto_cancel_expired_orders"
        ]
    },
    "daily": [
        "smartplan_medical.smartplan_medical.tasks.check_expiring_batches",
        "smartplan_medical.smartplan_medical.tasks.escalate_pending_approvals"
    ],
    "hourly": [
        "smartplan_medical.smartplan_medical.tasks.retry_failed_processes"
    ]
}

# Permissions
# permission_query_conditions = {}
# has_permission = {}

# Testing
# before_tests = "smartplan_medical.install.before_tests"

export_python_type_annotations = True
