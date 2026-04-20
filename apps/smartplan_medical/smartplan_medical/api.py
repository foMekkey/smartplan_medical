"""
SmartPlan Medical — PWA API Layer
Extends Frappe bootinfo, provides dynamic manifest, and PWA utilities.
"""

import json
import frappe
from frappe import _


@frappe.whitelist(methods=["GET"], allow_guest=True)
def get_manifest():
    """
    Serve a dynamic manifest.json from site settings.
    This allows the manifest to reflect real-time changes to app name, colors, etc.
    """
    site_name = frappe.utils.get_url()
    app_name = (
        frappe.get_website_settings("app_name")
        or frappe.get_system_settings("app_name")
        or "SmartPlan Medical"
    )

    manifest = {
        "name": app_name,
        "short_name": app_name[:12] if len(app_name) > 12 else app_name,
        "description": f"{app_name} — Enterprise Resource Planning",
        "start_url": "/app",
        "scope": "/",
        "display": "standalone",
        "orientation": "any",
        "theme_color": "#0D1B2A",
        "background_color": "#0D1B2A",
        "categories": ["business", "medical", "productivity"],
        "lang": frappe.local.lang or "en",
        "dir": "rtl" if frappe.local.lang == "ar" else "ltr",
        "icons": [
            {
                "src": "/assets/smartplan_medical/icons/icon-72x72.png",
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/assets/smartplan_medical/icons/icon-96x96.png",
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/assets/smartplan_medical/icons/icon-128x128.png",
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/assets/smartplan_medical/icons/icon-144x144.png",
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/assets/smartplan_medical/icons/icon-152x152.png",
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/assets/smartplan_medical/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/assets/smartplan_medical/icons/icon-384x384.png",
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/assets/smartplan_medical/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            },
        ],
        "shortcuts": [
            {
                "name": "Sales",
                "short_name": "Sales",
                "url": "/app/selling",
                "icons": [{"src": "/assets/smartplan_medical/icons/icon-96x96.png", "sizes": "96x96"}]
            },
            {
                "name": "Purchase",
                "short_name": "Purchase",
                "url": "/app/buying",
                "icons": [{"src": "/assets/smartplan_medical/icons/icon-96x96.png", "sizes": "96x96"}]
            },
            {
                "name": "Stock",
                "short_name": "Stock",
                "url": "/app/stock",
                "icons": [{"src": "/assets/smartplan_medical/icons/icon-96x96.png", "sizes": "96x96"}]
            },
        ],
        "prefer_related_applications": False,
    }

    frappe.response["type"] = "json"
    frappe.response["message"] = manifest
    return manifest


def extend_bootinfo(bootinfo):
    """
    Called during boot — injects PWA configuration into the client-side
    frappe.boot object so JS can access it without extra API calls.
    """
    app_name = (
        frappe.get_website_settings("app_name")
        or frappe.get_system_settings("app_name")
        or "SmartPlan Medical"
    )

    bootinfo["pwa_config"] = {
        "app_name": app_name,
        "short_name": app_name[:12] if len(app_name) > 12 else app_name,
        "theme_color": "#0D1B2A",
        "accent_color": "#00BFA6",
        "is_pwa_enabled": True,
        "sw_url": "/assets/smartplan_medical/js/service-worker.js",
        "manifest_url": "/api/method/smartplan_medical.api.get_manifest",
        "offline_url": "/assets/smartplan_medical/offline.html",
        "sw_version": "1.0.0",
        "cache_name": "smartplan-pwa-v1",
    }


def update_website_context(context):
    """
    Inject PWA meta tags into ALL pages (Desk + Website).
    This injects manifest link, apple-touch-icon, and theme-color overrides
    into the <head> via Frappe's head_html mechanism.
    """
    pwa_head = get_pwa_meta_tags()
    if context.get("head_html"):
        context["head_html"] += pwa_head
    else:
        context["head_html"] = pwa_head


def get_pwa_meta_tags():
    """
    Returns the HTML meta tags needed for PWA support.
    Injected into <head> of all pages.
    """
    return """
<!-- SmartPlan Medical PWA Meta Tags -->
<link rel="manifest" href="/api/method/smartplan_medical.api.get_manifest" crossorigin="use-credentials">
<meta name="theme-color" content="#0D1B2A">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="SmartPlan Medical">
<link rel="apple-touch-icon" href="/assets/smartplan_medical/icons/icon-152x152.png">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/smartplan_medical/icons/icon-192x192.png">
<link rel="apple-touch-startup-image" href="/assets/smartplan_medical/icons/icon-512x512.png">
<meta name="msapplication-TileImage" content="/assets/smartplan_medical/icons/icon-144x144.png">
<meta name="msapplication-TileColor" content="#0D1B2A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
"""


def after_install():
    """Post-installation setup for SmartPlan Medical PWA."""
    frappe.logger().info("SmartPlan Medical PWA installed successfully.")

    # Set default website settings if not already set
    try:
        ws = frappe.get_doc("Website Settings")
        if not ws.app_name:
            ws.app_name = "SmartPlan Medical"
            ws.save(ignore_permissions=True)
            frappe.db.commit()
    except Exception:
        pass
