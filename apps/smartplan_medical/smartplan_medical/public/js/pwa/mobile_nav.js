/**
 * SmartPlan Medical — Mobile Bottom Navigation
 * Premium bottom tab bar with modules popup, alerts, and profile.
 */

const SmartPlanNav = {
    container: null,
    modulesOpen: false,
    tabs: [
        { id: 'home', icon: 'home', label: 'Home', route: '' },
        { id: 'modules', icon: 'grid', label: 'Modules', action: 'modules' },
        { id: 'search', icon: 'search', label: 'Search', action: 'search' },
        { id: 'notifications', icon: 'bell', label: 'Alerts', action: 'notifications' },
        { id: 'profile', icon: 'user', label: 'Me', action: 'profile' },
    ],

    init() {
        if (!document.documentElement.classList.contains('sp-mobile')) return;
        this.render();
        this.updateActiveTab();

        if (typeof frappe !== 'undefined' && frappe.router) {
            frappe.router.on('change', () => this.updateActiveTab());
        }
    },

    render() {
        if (document.getElementById('sp-bottom-nav')) return;

        this.container = document.createElement('nav');
        this.container.id = 'sp-bottom-nav';
        this.container.className = 'sp-bottom-nav';

        const tabsHTML = this.tabs.map(tab => `
            <button class="sp-nav-tab" data-tab="${tab.id}" data-route="${tab.route || ''}" data-action="${tab.action || ''}">
                <div class="sp-nav-tab-icon">
                    ${this.getIcon(tab.icon)}
                    <span class="sp-nav-badge" id="sp-badge-${tab.id}" style="display:none;">0</span>
                </div>
                <span class="sp-nav-tab-label">${__(tab.label)}</span>
            </button>
        `).join('');

        this.container.innerHTML = tabsHTML;
        document.body.appendChild(this.container);
        document.body.style.paddingBottom = '68px';

        this.container.querySelectorAll('.sp-nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.handleTabClick(e, tab));
        });

        this.updateNotificationBadge();
        if (typeof frappe !== 'undefined' && frappe.realtime) {
            frappe.realtime.on('notification', () => this.updateNotificationBadge());
        }
    },

    handleTabClick(e, tab) {
        const action = tab.dataset.action;
        const route = tab.dataset.route;

        if (action === 'search') {
            if (typeof frappe !== 'undefined') {
                // Try Frappe's awesome bar
                let searchBar = document.querySelector('.search-bar input[type="text"]');
                if (searchBar) {
                    searchBar.focus();
                    searchBar.click();
                } else {
                    let navSearch = document.querySelector('#navbar-search');
                    if (navSearch) navSearch.click();
                }
            }
            return;
        }

        if (action === 'modules') {
            this.openModulesPopup();
            return;
        }

        if (action === 'notifications') {
            if (typeof frappe !== 'undefined') {
                frappe.set_route('List', 'Notification Log');
            }
            return;
        }

        if (action === 'profile') {
            if (typeof frappe !== 'undefined') {
                frappe.set_route('app/user');
            }
            return;
        }

        if (typeof frappe !== 'undefined') {
            frappe.set_route(route);
        }
    },

    /* ═══════════════════════════════════════
       MODULES POPUP — Dark fullscreen modal
       ═══════════════════════════════════════ */
    openModulesPopup() {
        if (document.getElementById('sp-modules-popup')) {
            this.closeModulesPopup();
            return;
        }

        const popup = document.createElement('div');
        popup.id = 'sp-modules-popup';
        popup.innerHTML = `
            <div class="sp-mod-header">
                <div>
                    <h2>${__('Modules')}</h2>
                    <span class="sp-mod-sub">SPS ERP · Smart Health System</span>
                </div>
                <button class="sp-mod-close" id="sp-mod-close">✕</button>
            </div>
            <div class="sp-mod-search">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" id="sp-mod-filter" placeholder="${__('Search modules...')}">
            </div>
            <div class="sp-mod-grid" id="sp-mod-grid">
                <div class="sp-mod-loading">${__('Loading...')}</div>
            </div>
        `;

        document.body.appendChild(popup);
        requestAnimationFrame(() => popup.classList.add('sp-mod-visible'));

        document.getElementById('sp-mod-close').addEventListener('click', () => this.closeModulesPopup());

        // Load workspaces
        this.loadWorkspaces();

        // Search filter
        document.getElementById('sp-mod-filter').addEventListener('input', (e) => {
            const q = e.target.value.toLowerCase();
            document.querySelectorAll('.sp-mod-item').forEach(item => {
                const name = item.dataset.name.toLowerCase();
                item.style.display = name.includes(q) ? '' : 'none';
            });
        });
    },

    closeModulesPopup() {
        const popup = document.getElementById('sp-modules-popup');
        if (popup) {
            popup.classList.remove('sp-mod-visible');
            setTimeout(() => popup.remove(), 300);
        }
    },

    async loadWorkspaces() {
        const grid = document.getElementById('sp-mod-grid');
        if (!grid || typeof frappe === 'undefined') return;

        try {
            const workspaces = frappe.boot.allowed_workspaces || [];
            if (!workspaces.length) {
                grid.innerHTML = `<div class="sp-mod-loading">${__('No modules found')}</div>`;
                return;
            }

            const colors = [
                '#E91E63', '#9C27B0', '#673AB7', '#3F51B5',
                '#2196F3', '#009688', '#4CAF50', '#FF9800',
                '#FF5722', '#795548', '#607D8B', '#00BCD4',
                '#8BC34A', '#FFC107', '#F44336', '#3DDC84',
            ];

            const icons = {
                'home': '🏠', 'dashboard': '📊', 'settings': '⚙️',
                'hr': '👥', 'accounting': '💰', 'stock': '📦',
                'selling': '🛒', 'buying': '🛍️', 'manufacturing': '🏭',
                'projects': '📋', 'crm': '🤝', 'support': '🎧',
                'healthcare': '🏥', 'website': '🌐', 'assets': '🏢',
                'quality': '✅', 'education': '🎓', 'pos': '💳',
                'pharmacy': '💊', 'lab': '🔬', 'blood': '🩸',
                'emergency': '🚑', 'surgery': '⚕️', 'radiology': '📡',
                'nutrition': '🥗', 'insurance': '🛡️', 'admission': '🛏️',
                'warehouse': '🏪', 'inventory': '📝', 'reports': '📈',
                'finance': '💵', 'ledger': '📒',
            };

            grid.innerHTML = workspaces.map((ws, i) => {
                const name = ws.name || ws.title || ws;
                const title = ws.title || name;
                const color = colors[i % colors.length];
                // Try to match an icon
                let emoji = '📁';
                const lower = (title + ' ' + name).toLowerCase();
                for (const [key, val] of Object.entries(icons)) {
                    if (lower.includes(key)) { emoji = val; break; }
                }

                return `
                    <a class="sp-mod-item" data-name="${title}" href="/app/${encodeURIComponent(name.toLowerCase().replace(/ /g, '-'))}">
                        <div class="sp-mod-icon" style="background:${color}">
                            <span>${emoji}</span>
                        </div>
                        <span class="sp-mod-name">${title}</span>
                    </a>
                `;
            }).join('');

            // Click handler
            grid.querySelectorAll('.sp-mod-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const name = item.dataset.name;
                    this.closeModulesPopup();
                    if (typeof frappe !== 'undefined') {
                        frappe.set_route(item.getAttribute('href').replace('/app/', ''));
                    }
                });
            });

        } catch (err) {
            console.error('[PWA] Failed to load workspaces:', err);
            grid.innerHTML = `<div class="sp-mod-loading">${__('Failed to load')}</div>`;
        }
    },

    updateActiveTab() {
        if (!this.container) return;
        this.container.querySelectorAll('.sp-nav-tab').forEach(tab => {
            tab.classList.remove('sp-nav-active');
        });
        const homeTab = this.container.querySelector('[data-tab="home"]');
        if (homeTab) homeTab.classList.add('sp-nav-active');
    },

    updateNotificationBadge() {
        if (typeof frappe === 'undefined') return;
        try {
            frappe.xcall('frappe.client.get_count', {
                doctype: 'Notification Log',
                filters: { read: 0 }
            }).then(count => {
                const badge = document.getElementById('sp-badge-notifications');
                if (badge && count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.style.display = 'flex';
                } else if (badge) {
                    badge.style.display = 'none';
                }
            }).catch(() => {});
        } catch (e) {}
    },

    getIcon(name) {
        const icons = {
            home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/></svg>',
            grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
            search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
            bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
            user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        };
        return icons[name] || '';
    },

    destroy() {
        if (this.container) {
            this.container.remove();
            document.body.style.paddingBottom = '';
        }
    },
};

export default SmartPlanNav;
