/**
 * SmartPlan Medical — Web PWA Registration
 * Lightweight script for login/website pages (non-Desk context).
 * Registers the service worker and handles install prompt on web pages.
 */

(function() {
    'use strict';

    // Register Service Worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/assets/smartplan_medical/js/service-worker.js', {
                scope: '/'
            }).then(function(reg) {
                console.log('[SmartPlan Web PWA] Service Worker registered');
            }).catch(function(err) {
                console.warn('[SmartPlan Web PWA] SW registration failed:', err);
            });
        });
    }

    // Inject manifest link
    if (!document.querySelector('link[rel="manifest"]')) {
        var link = document.createElement('link');
        link.rel = 'manifest';
        link.href = '/api/method/smartplan_medical.api.get_manifest';
        link.crossOrigin = 'use-credentials';
        document.head.appendChild(link);
    }

    // Handle install prompt on web pages
    var deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', function(e) {
        e.preventDefault();
        deferredPrompt = e;

        // Check if already dismissed
        var dismissed = localStorage.getItem('sp_install_dismissed');
        if (dismissed && Date.now() - parseInt(dismissed) < 7 * 24 * 60 * 60 * 1000) {
            return;
        }

        // Show a simple install button on login page
        var loginCard = document.querySelector('.page-card');
        if (loginCard && !document.getElementById('sp-web-install-btn')) {
            var btn = document.createElement('button');
            btn.id = 'sp-web-install-btn';
            btn.textContent = 'Install App';
            btn.style.cssText = 'width:100%;margin-top:16px;padding:12px;background:linear-gradient(135deg,#00BFA6,#00A58E);border:none;color:#0D1B2A;font-weight:700;border-radius:12px;cursor:pointer;font-size:15px;font-family:Inter,sans-serif;';
            btn.onclick = function() {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then(function() {
                        deferredPrompt = null;
                        btn.remove();
                    });
                }
            };
            loginCard.appendChild(btn);
        }
    });

    // Detect standalone mode
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
        document.documentElement.classList.add('sp-pwa-standalone');
    }
})();
