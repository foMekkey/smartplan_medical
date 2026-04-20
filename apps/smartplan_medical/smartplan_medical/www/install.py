no_cache = 1
no_sitemap = 0

import frappe


def get_context(context):
    """Build context for the PWA install page."""
    app_name = (
        frappe.get_website_settings("app_name")
        or frappe.get_system_settings("app_name")
        or "SmartPlan Medical"
    )
    site_url = frappe.utils.get_url()

    context.update({
        "title": f"تحميل {app_name}",
        "app_name": app_name,
        "site_url": site_url,
        "no_cache": 1,
        "no_header": 1,
        "no_breadcrumbs": 1,
    })
