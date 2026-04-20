/**
 * SmartPlan Medical — Offline Handler
 * Detects online/offline state, shows indicators, and queues form submissions.
 */

const SmartPlanOffline = {
    isOnline: navigator.onLine,
    indicator: null,
    syncQueue: [],

    init() {
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Set initial state
        if (!navigator.onLine) {
            this.handleOffline();
        }
    },

    handleOnline() {
        this.isOnline = true;
        document.documentElement.classList.remove('sp-offline');
        document.documentElement.classList.add('sp-online');
        this.hideOfflineIndicator();

        if (typeof frappe !== 'undefined' && frappe.show_alert) {
            frappe.show_alert({
                message: __('Back online ✓'),
                indicator: 'green',
            }, 3);
        }

        // Attempt to sync queued submissions
        this.processQueue();
    },

    handleOffline() {
        this.isOnline = false;
        document.documentElement.classList.add('sp-offline');
        document.documentElement.classList.remove('sp-online');
        this.showOfflineIndicator();

        if (typeof frappe !== 'undefined' && frappe.show_alert) {
            frappe.show_alert({
                message: __('You are offline. Some features may be limited.'),
                indicator: 'orange',
            }, 5);
        }
    },

    showOfflineIndicator() {
        if (this.indicator) return;

        this.indicator = document.createElement('div');
        this.indicator.id = 'sp-offline-indicator';
        this.indicator.innerHTML = `
            <div class="sp-offline-content">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                    <line x1="3" y1="13" x2="13" y2="3" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <span>${__('Offline')}</span>
            </div>
        `;
        document.body.appendChild(this.indicator);

        requestAnimationFrame(() => {
            this.indicator.classList.add('sp-offline-visible');
        });
    },

    hideOfflineIndicator() {
        if (this.indicator) {
            this.indicator.classList.remove('sp-offline-visible');
            setTimeout(() => {
                this.indicator?.remove();
                this.indicator = null;
            }, 400);
        }
    },

    /**
     * Queue a form submission for later sync.
     * Called when user tries to save while offline.
     */
    queueSubmission(doctype, docname, data) {
        const entry = {
            id: `${doctype}-${docname}-${Date.now()}`,
            doctype,
            docname,
            data,
            timestamp: Date.now(),
        };

        this.syncQueue.push(entry);
        localStorage.setItem('sp_sync_queue', JSON.stringify(this.syncQueue));

        if (typeof frappe !== 'undefined' && frappe.show_alert) {
            frappe.show_alert({
                message: __('Changes will be saved when you\'re back online.'),
                indicator: 'blue',
            }, 5);
        }

        // Register background sync if supported
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            navigator.serviceWorker.ready.then((reg) => {
                return reg.sync.register('smartplan-form-sync');
            }).catch(console.warn);
        }
    },

    /**
     * Process the offline queue when back online.
     */
    async processQueue() {
        const stored = localStorage.getItem('sp_sync_queue');
        if (stored) {
            try {
                this.syncQueue = JSON.parse(stored);
            } catch (e) {
                this.syncQueue = [];
            }
        }

        if (this.syncQueue.length === 0) return;

        console.log(`[PWA] Processing ${this.syncQueue.length} queued submissions`);

        const processed = [];
        for (const entry of this.syncQueue) {
            try {
                await frappe.call({
                    method: 'frappe.client.save',
                    args: { doc: entry.data },
                    async: true,
                });
                processed.push(entry.id);
                console.log(`[PWA] Synced: ${entry.doctype}/${entry.docname}`);
            } catch (error) {
                console.warn(`[PWA] Failed to sync: ${entry.doctype}/${entry.docname}`, error);
            }
        }

        // Remove processed entries
        this.syncQueue = this.syncQueue.filter((e) => !processed.includes(e.id));
        localStorage.setItem('sp_sync_queue', JSON.stringify(this.syncQueue));

        if (processed.length > 0 && typeof frappe !== 'undefined' && frappe.show_alert) {
            frappe.show_alert({
                message: __(`${processed.length} offline change(s) synced successfully.`),
                indicator: 'green',
            }, 5);
        }
    },
};

export default SmartPlanOffline;
