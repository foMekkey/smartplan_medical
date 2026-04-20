/**
 * SmartPlan Medical — PWA Core Bundle
 * Registers service worker, handles install prompt, and manages offline state.
 * Injected into Frappe Desk via hooks.py app_include_js.
 */

import SmartPlanSW from './pwa/sw_register';
import SmartPlanInstall from './pwa/install_prompt';
import SmartPlanOffline from './pwa/offline_handler';

// Initialize PWA when Desk is ready
$(document).on('startup', function () {
    console.log('[SmartPlan PWA] Initializing...');

    // Register Service Worker
    SmartPlanSW.init();

    // Setup Install Prompt
    SmartPlanInstall.init();

    // Setup Offline Handler
    SmartPlanOffline.init();

    // Inject manifest link if not present
    if (!document.querySelector('link[rel="manifest"]')) {
        const manifestLink = document.createElement('link');
        manifestLink.rel = 'manifest';
        manifestLink.href = '/api/method/smartplan_medical.api.get_manifest';
        manifestLink.crossOrigin = 'use-credentials';
        document.head.appendChild(manifestLink);
    }

    // Override theme-color meta
    let themeColorMeta = document.querySelector('meta[name="theme-color"]');
    if (themeColorMeta) {
        themeColorMeta.content = '#0D1B2A';
    } else {
        themeColorMeta = document.createElement('meta');
        themeColorMeta.name = 'theme-color';
        themeColorMeta.content = '#0D1B2A';
        document.head.appendChild(themeColorMeta);
    }

    // Detect mobile or standalone PWA
    const isMobile = window.innerWidth <= 768 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;

    // Only apply dark theme on mobile or installed PWA — desktop web keeps default theme
    if (isMobile || isStandalone) {
        document.documentElement.classList.add('smartplan-pwa');
        document.documentElement.classList.add('sp-mobile');
    }

    // Listen for viewport changes
    const mobileQuery = window.matchMedia('(max-width: 768px)');
    mobileQuery.addEventListener('change', (e) => {
        document.documentElement.classList.toggle('sp-mobile', e.matches);
        document.documentElement.classList.toggle('smartplan-pwa', e.matches || isStandalone);
    });

    console.log('[SmartPlan PWA] Initialized successfully');
});

// Export for external access
window.SmartPlanPWA = {
    SW: SmartPlanSW,
    Install: SmartPlanInstall,
    Offline: SmartPlanOffline,
};
