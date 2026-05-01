/**
 * SmartPlan Medical — Mobile Bottom Navigation
 * Clean, working bottom tab bar using only verified Frappe routes.
 */

const SmartPlanNav = {
    container: null,
    tabs: [
        { id: 'home', icon: 'home', label: 'Home', route: '' },
        { id: 'modules', icon: 'grid', label: 'Modules', action: 'toggle-sidebar' },
        { id: 'search', icon: 'search', label: 'Search', action: 'search' },
        { id: 'notifications', icon: 'bell', label: 'Alerts', action: 'notifications' },
        { id: 'profile', icon: 'user', label: 'Me', action: 'profile' },
    ],

    init() {
        if (!document.documentElement.classList.contains('sp-mobile')) return;
        this.render();
        this.updateActiveTab();

        // Listen for route changes
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

        // Bind clicks
        this.container.querySelectorAll('.sp-nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.handleTabClick(e, tab));
        });

        // Update notification count
        this.updateNotificationBadge();
        if (typeof frappe !== 'undefined' && frappe.realtime) {
            frappe.realtime.on('notification', () => this.updateNotificationBadge());
        }
    },

    handleTabClick(e, tab) {
        const action = tab.dataset.action;
        const route = tab.dataset.route;

        if (action === 'search') {
            // Use the Frappe Control+K / Awesome Bar
            if (typeof frappe !== 'undefined') {
                let searchBar = document.querySelector('.search-bar input[type="text"]');
                if (searchBar) {
                    searchBar.focus();
                    searchBar.click();
                } else {
                    // Try the navbar search
                    let navSearch = document.querySelector('#navbar-search');
                    if (navSearch) navSearch.click();
                }
            }
            return;
        }

        if (action === 'toggle-sidebar') {
            const html = document.documentElement;
            const isOpen = html.classList.contains('sp-sidebar-open');

            if (isOpen) {
                html.classList.remove('sp-sidebar-open');
                const overlay = document.querySelector('.sp-sidebar-overlay');
                if (overlay) overlay.remove();
            } else {
                html.classList.add('sp-sidebar-open');
                // Create overlay
                if (!document.querySelector('.sp-sidebar-overlay')) {
                    const overlay = document.createElement('div');
                    overlay.className = 'sp-sidebar-overlay';
                    overlay.addEventListener('click', () => {
                        html.classList.remove('sp-sidebar-open');
                        overlay.remove();
                    });
                    document.body.appendChild(overlay);
                }
            }
            return;
        }

        if (action === 'notifications') {
            // Open the notification dropdown instead of navigating
            if (typeof frappe !== 'undefined') {
                let bellBtn = document.querySelector('.notifications-icon, .navbar-icon[data-original-title="Notifications"], a.nav-link[title="Notifications"], .dropdown-notifications .dropdown-toggle');
                if (bellBtn) {
                    bellBtn.click();
                } else {
                    // Fallback: open notification log list
                    frappe.set_route('List', 'Notification Log');
                }
            }
            return;
        }

        if (action === 'profile') {
            if (typeof frappe !== 'undefined') {
                // Open the user dropdown menu
                let userMenu = document.querySelector('.navbar-icon-text.avatar, .avatar.avatar-medium, #navbar-user, .dropdown-user .dropdown-toggle');
                if (userMenu) {
                    userMenu.click();
                } else {
                    frappe.set_route('');
                }
            }
            return;
        }

        // Route navigation
        if (typeof frappe !== 'undefined') {
            frappe.set_route(route);
        }
    },

    updateActiveTab() {
        if (!this.container) return;
        const path = window.location.pathname + window.location.hash;
        this.container.querySelectorAll('.sp-nav-tab').forEach(tab => {
            tab.classList.remove('sp-nav-active');
        });
        // Default to home
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
