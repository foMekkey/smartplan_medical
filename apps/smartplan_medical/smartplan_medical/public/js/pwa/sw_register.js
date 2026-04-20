/**
 * SmartPlan Medical — Service Worker Registration
 * Registers the SW, handles updates, and manages lifecycle.
 */

const SmartPlanSW = {
    SW_URL: '/assets/smartplan_medical/js/service-worker.js',
    registration: null,

    async init() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[PWA] Service Workers not supported');
            return;
        }

        try {
            this.registration = await navigator.serviceWorker.register(this.SW_URL, {
                scope: '/',
            });

            console.log('[PWA] Service Worker registered:', this.registration.scope);

            // Handle updates
            this.registration.addEventListener('updatefound', () => {
                const newWorker = this.registration.installing;
                if (!newWorker) return;

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.showUpdateNotification();
                    }
                });
            });

            // Check for updates periodically (every 30 minutes)
            setInterval(() => {
                this.registration.update();
            }, 30 * 60 * 1000);

        } catch (error) {
            console.error('[PWA] SW registration failed:', error);
        }
    },

    showUpdateNotification() {
        if (typeof frappe !== 'undefined' && frappe.show_alert) {
            frappe.show_alert({
                message: __('A new version is available. <a onclick="location.reload(true)">Refresh</a> to update.'),
                indicator: 'blue',
            }, 10);
        }
    },
};

export default SmartPlanSW;
