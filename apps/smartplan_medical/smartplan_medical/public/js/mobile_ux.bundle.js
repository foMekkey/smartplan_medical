/**
 * SmartPlan Medical — Mobile UX Bundle
 * Bottom navigation, touch gestures, and form enhancements.
 * Injected into Frappe Desk via hooks.py app_include_js.
 */

import SmartPlanNav from './pwa/mobile_nav';
import SmartPlanGestures from './pwa/touch_gestures';
import SmartPlanForms from './pwa/form_enhancer';

$(document).on('startup', function () {
    // Only initialize mobile enhancements on mobile devices
    const isMobile = window.innerWidth <= 768 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

    if (isMobile) {
        console.log('[SmartPlan UX] Initializing mobile enhancements...');

        // Bottom navigation
        SmartPlanNav.init();

        // Touch gestures (pull-to-refresh, swipe-back)
        SmartPlanGestures.init();

        // Form enhancements (FAB, card views, sticky headers)
        SmartPlanForms.init();

        // Hide desktop sidebar on mobile by default
        $('body').addClass('sp-sidebar-collapsed');

        // Add mobile-specific class to workspace views
        frappe.router.on('change', () => {
            const route = frappe.get_route();
            document.body.dataset.spRoute = route ? route[0] : 'home';
        });

        console.log('[SmartPlan UX] Mobile enhancements initialized');
    }

    // Universal enhancements (desktop + mobile)
    enhanceDialogs();
    enhanceLists();
});

/**
 * Enhance Frappe dialogs for mobile (larger buttons, bottom sheet behavior)
 */
function enhanceDialogs() {
    // Hook into dialog show
    const originalShow = frappe.ui.Dialog.prototype.show;
    if (originalShow) {
        frappe.ui.Dialog.prototype.show = function () {
            originalShow.call(this);
            if (document.documentElement.classList.contains('sp-mobile')) {
                this.$wrapper.addClass('sp-mobile-dialog');
            }
        };
    }
}

/**
 * Enhance list views for mobile (card layout)
 */
function enhanceLists() {
    if (!document.documentElement.classList.contains('sp-mobile')) return;

    // Monitor for list view rendering
    const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1 && node.classList?.contains('list-row')) {
                    node.classList.add('sp-list-card');
                }
            });
        });
    });

    const listContainer = document.querySelector('#page-List, .page-container');
    if (listContainer) {
        observer.observe(listContainer, { childList: true, subtree: true });
    }

    // Re-observe on route changes
    if (typeof frappe !== 'undefined' && frappe.router) {
        frappe.router.on('change', () => {
            setTimeout(() => {
                const newContainer = document.querySelector('.result, .list-rows');
                if (newContainer) {
                    observer.observe(newContainer, { childList: true, subtree: true });
                }
            }, 500);
        });
    }
}

// Export for external access
window.SmartPlanUX = {
    Nav: SmartPlanNav,
    Gestures: SmartPlanGestures,
    Forms: SmartPlanForms,
};
