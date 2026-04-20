/**
 * SmartPlan Medical — Form Enhancer
 * Transforms ERPNext forms for mobile: table→card view, sticky headers, FAB.
 */

const SmartPlanForms = {
    fab: null,

    init() {
        this.enhanceForms();
        this.createFAB();
        this.bindFormEvents();
    },

    enhanceForms() {
        // Hook into Frappe's form render
        if (typeof frappe === 'undefined') return;

        // Override table rendering for mobile
        const originalMakeControl = frappe.ui.form.ControlTable?.prototype?.make;
        if (originalMakeControl) {
            const self = this;
            frappe.ui.form.ControlTable.prototype.make = function () {
                originalMakeControl.call(this);
                if (document.documentElement.classList.contains('sp-mobile')) {
                    self.enhanceTable(this);
                }
            };
        }
    },

    enhanceTable(control) {
        if (!control.$wrapper) return;

        // Add card toggle button
        const toggleBtn = $(`
            <button class="btn btn-xs sp-table-toggle" title="${__('Toggle card view')}">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                    <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
                </svg>
            </button>
        `);

        control.$wrapper.find('.grid-heading-row .row-index').prepend(toggleBtn);

        toggleBtn.on('click', (e) => {
            e.stopPropagation();
            control.$wrapper.toggleClass('sp-card-view');
        });

        // Auto-enable card view on very small screens
        if (window.innerWidth <= 576) {
            control.$wrapper.addClass('sp-card-view');
        }

        // Make the table horizontally scrollable
        control.$wrapper.find('.frappe-control[data-fieldtype="Table"] .form-group').addClass('sp-table-scroll');
    },

    createFAB() {
        if (!document.documentElement.classList.contains('sp-mobile')) return;
        if (document.getElementById('sp-fab-container')) return;

        const fabContainer = document.createElement('div');
        fabContainer.id = 'sp-fab-container';
        fabContainer.className = 'sp-fab-container';
        fabContainer.innerHTML = `
            <div class="sp-fab-actions" id="sp-fab-actions" style="display:none;">
                <button class="sp-fab-action" data-action="save" title="${__('Save')}">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                        <polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
                    </svg>
                    <span>${__('Save')}</span>
                </button>
                <button class="sp-fab-action sp-fab-submit" data-action="submit" title="${__('Submit')}">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>${__('Submit')}</span>
                </button>
                <button class="sp-fab-action" data-action="new" title="${__('New')}">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    <span>${__('New')}</span>
                </button>
            </div>
            <button class="sp-fab-main" id="sp-fab-main" aria-label="${__('Actions')}">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
            </button>
        `;

        document.body.appendChild(fabContainer);

        // Toggle FAB menu
        document.getElementById('sp-fab-main')?.addEventListener('click', () => {
            fabContainer.classList.toggle('sp-fab-open');
            const actionsEl = document.getElementById('sp-fab-actions');
            if (actionsEl) {
                actionsEl.style.display = fabContainer.classList.contains('sp-fab-open') ? 'flex' : 'none';
            }
        });

        // FAB actions
        fabContainer.querySelectorAll('.sp-fab-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                this.handleFABAction(action);
                fabContainer.classList.remove('sp-fab-open');
                document.getElementById('sp-fab-actions').style.display = 'none';
            });
        });

        this.fab = fabContainer;
    },

    handleFABAction(action) {
        if (typeof frappe === 'undefined') return;

        switch (action) {
            case 'save':
                if (cur_frm) {
                    cur_frm.save();
                } else if (cur_list) {
                    // In list view, create new
                    cur_list.make_new_doc();
                }
                break;

            case 'submit':
                if (cur_frm && cur_frm.doc.docstatus === 0) {
                    cur_frm.submit();
                }
                break;

            case 'new':
                if (cur_frm) {
                    frappe.new_doc(cur_frm.doctype);
                } else if (cur_list) {
                    cur_list.make_new_doc();
                }
                break;
        }
    },

    updateFABVisibility() {
        if (!this.fab) return;

        const isMobile = document.documentElement.classList.contains('sp-mobile');
        const isForm = !!cur_frm;
        const isList = !!cur_list;

        if (isMobile && (isForm || isList)) {
            this.fab.style.display = 'block';

            // Show/hide submit based on form state
            const submitBtn = this.fab.querySelector('[data-action="submit"]');
            if (submitBtn) {
                const canSubmit = isForm && cur_frm.doc.docstatus === 0 && cur_frm.perm[0]?.submit;
                submitBtn.style.display = canSubmit ? 'flex' : 'none';
            }
        } else {
            this.fab.style.display = 'none';
        }
    },

    bindFormEvents() {
        if (typeof frappe === 'undefined') return;

        // Update FAB on route change
        if (frappe.router) {
            frappe.router.on('change', () => {
                setTimeout(() => this.updateFABVisibility(), 300);
            });
        }

        // Update FAB on form load
        $(document).on('form-load form-refresh', () => {
            setTimeout(() => this.updateFABVisibility(), 300);
        });

        // Add sticky headers to form sections
        $(document).on('form-load', () => {
            if (!document.documentElement.classList.contains('sp-mobile')) return;
            this.addStickyHeaders();
        });
    },

    addStickyHeaders() {
        // Make section headings sticky on mobile
        document.querySelectorAll('.section-head').forEach(header => {
            header.classList.add('sp-sticky-section');
        });
    },
};

export default SmartPlanForms;
