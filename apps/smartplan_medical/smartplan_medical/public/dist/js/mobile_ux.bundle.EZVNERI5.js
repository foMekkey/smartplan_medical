(() => {
  // ../smartplan_medical/smartplan_medical/public/js/pwa/mobile_nav.js
  var SmartPlanNav = {
    container: null,
    modulesOpen: false,
    tabs: [
      { id: "home", icon: "home", label: "Home", route: "" },
      { id: "modules", icon: "grid", label: "Modules", action: "modules" },
      { id: "search", icon: "search", label: "Search", action: "search" },
      { id: "notifications", icon: "bell", label: "Alerts", action: "notifications" },
      { id: "profile", icon: "user", label: "Me", action: "profile" }
    ],
    init() {
      if (!document.documentElement.classList.contains("sp-mobile"))
        return;
      this.render();
      this.updateActiveTab();
      if (typeof frappe !== "undefined" && frappe.router) {
        frappe.router.on("change", () => this.updateActiveTab());
      }
    },
    render() {
      if (document.getElementById("sp-bottom-nav"))
        return;
      this.container = document.createElement("nav");
      this.container.id = "sp-bottom-nav";
      this.container.className = "sp-bottom-nav";
      const tabsHTML = this.tabs.map((tab) => `
            <button class="sp-nav-tab" data-tab="${tab.id}" data-route="${tab.route || ""}" data-action="${tab.action || ""}">
                <div class="sp-nav-tab-icon">
                    ${this.getIcon(tab.icon)}
                    <span class="sp-nav-badge" id="sp-badge-${tab.id}" style="display:none;">0</span>
                </div>
                <span class="sp-nav-tab-label">${__(tab.label)}</span>
            </button>
        `).join("");
      this.container.innerHTML = tabsHTML;
      document.body.appendChild(this.container);
      document.body.style.paddingBottom = "68px";
      this.container.querySelectorAll(".sp-nav-tab").forEach((tab) => {
        tab.addEventListener("click", (e) => this.handleTabClick(e, tab));
      });
      this.updateNotificationBadge();
      if (typeof frappe !== "undefined" && frappe.realtime) {
        frappe.realtime.on("notification", () => this.updateNotificationBadge());
      }
    },
    handleTabClick(e, tab) {
      const action = tab.dataset.action;
      const route = tab.dataset.route;
      if (action === "search") {
        if (typeof frappe !== "undefined") {
          let searchBar = document.querySelector('.search-bar input[type="text"]');
          if (searchBar) {
            searchBar.focus();
            searchBar.click();
          } else {
            let navSearch = document.querySelector("#navbar-search");
            if (navSearch)
              navSearch.click();
          }
        }
        return;
      }
      if (action === "modules") {
        this.openModulesPopup();
        return;
      }
      if (action === "notifications") {
        if (typeof frappe !== "undefined") {
          frappe.set_route("List", "Notification Log");
        }
        return;
      }
      if (action === "profile") {
        if (typeof frappe !== "undefined") {
          frappe.set_route("app/user");
        }
        return;
      }
      if (typeof frappe !== "undefined") {
        frappe.set_route(route);
      }
    },
    openModulesPopup() {
      if (document.getElementById("sp-modules-popup")) {
        this.closeModulesPopup();
        return;
      }
      const popup = document.createElement("div");
      popup.id = "sp-modules-popup";
      popup.innerHTML = `
            <div class="sp-mod-header">
                <div>
                    <h2>${__("Modules")}</h2>
                    <span class="sp-mod-sub">SPS ERP \xB7 Smart Health System</span>
                </div>
                <button class="sp-mod-close" id="sp-mod-close">\u2715</button>
            </div>
            <div class="sp-mod-search">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" id="sp-mod-filter" placeholder="${__("Search modules...")}">
            </div>
            <div class="sp-mod-grid" id="sp-mod-grid">
                <div class="sp-mod-loading">${__("Loading...")}</div>
            </div>
        `;
      document.body.appendChild(popup);
      requestAnimationFrame(() => popup.classList.add("sp-mod-visible"));
      document.getElementById("sp-mod-close").addEventListener("click", () => this.closeModulesPopup());
      this.loadWorkspaces();
      document.getElementById("sp-mod-filter").addEventListener("input", (e) => {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll(".sp-mod-item").forEach((item) => {
          const name = item.dataset.name.toLowerCase();
          item.style.display = name.includes(q) ? "" : "none";
        });
      });
    },
    closeModulesPopup() {
      const popup = document.getElementById("sp-modules-popup");
      if (popup) {
        popup.classList.remove("sp-mod-visible");
        setTimeout(() => popup.remove(), 300);
      }
    },
    async loadWorkspaces() {
      const grid = document.getElementById("sp-mod-grid");
      if (!grid || typeof frappe === "undefined")
        return;
      try {
        const workspaces = frappe.boot.allowed_workspaces || [];
        if (!workspaces.length) {
          grid.innerHTML = `<div class="sp-mod-loading">${__("No modules found")}</div>`;
          return;
        }
        const colors = [
          "#E91E63",
          "#9C27B0",
          "#673AB7",
          "#3F51B5",
          "#2196F3",
          "#009688",
          "#4CAF50",
          "#FF9800",
          "#FF5722",
          "#795548",
          "#607D8B",
          "#00BCD4",
          "#8BC34A",
          "#FFC107",
          "#F44336",
          "#3DDC84"
        ];
        const icons = {
          "home": "\u{1F3E0}",
          "dashboard": "\u{1F4CA}",
          "settings": "\u2699\uFE0F",
          "hr": "\u{1F465}",
          "accounting": "\u{1F4B0}",
          "stock": "\u{1F4E6}",
          "selling": "\u{1F6D2}",
          "buying": "\u{1F6CD}\uFE0F",
          "manufacturing": "\u{1F3ED}",
          "projects": "\u{1F4CB}",
          "crm": "\u{1F91D}",
          "support": "\u{1F3A7}",
          "healthcare": "\u{1F3E5}",
          "website": "\u{1F310}",
          "assets": "\u{1F3E2}",
          "quality": "\u2705",
          "education": "\u{1F393}",
          "pos": "\u{1F4B3}",
          "pharmacy": "\u{1F48A}",
          "lab": "\u{1F52C}",
          "blood": "\u{1FA78}",
          "emergency": "\u{1F691}",
          "surgery": "\u2695\uFE0F",
          "radiology": "\u{1F4E1}",
          "nutrition": "\u{1F957}",
          "insurance": "\u{1F6E1}\uFE0F",
          "admission": "\u{1F6CF}\uFE0F",
          "warehouse": "\u{1F3EA}",
          "inventory": "\u{1F4DD}",
          "reports": "\u{1F4C8}",
          "finance": "\u{1F4B5}",
          "ledger": "\u{1F4D2}"
        };
        grid.innerHTML = workspaces.map((ws, i) => {
          const name = ws.name || ws.title || ws;
          const title = ws.title || name;
          const color = colors[i % colors.length];
          let emoji = "\u{1F4C1}";
          const lower = (title + " " + name).toLowerCase();
          for (const [key, val] of Object.entries(icons)) {
            if (lower.includes(key)) {
              emoji = val;
              break;
            }
          }
          return `
                    <a class="sp-mod-item" data-name="${title}" href="/app/${encodeURIComponent(name.toLowerCase().replace(/ /g, "-"))}">
                        <div class="sp-mod-icon" style="background:${color}">
                            <span>${emoji}</span>
                        </div>
                        <span class="sp-mod-name">${title}</span>
                    </a>
                `;
        }).join("");
        grid.querySelectorAll(".sp-mod-item").forEach((item) => {
          item.addEventListener("click", (e) => {
            e.preventDefault();
            const name = item.dataset.name;
            this.closeModulesPopup();
            if (typeof frappe !== "undefined") {
              frappe.set_route(item.getAttribute("href").replace("/app/", ""));
            }
          });
        });
      } catch (err) {
        console.error("[PWA] Failed to load workspaces:", err);
        grid.innerHTML = `<div class="sp-mod-loading">${__("Failed to load")}</div>`;
      }
    },
    updateActiveTab() {
      if (!this.container)
        return;
      this.container.querySelectorAll(".sp-nav-tab").forEach((tab) => {
        tab.classList.remove("sp-nav-active");
      });
      const homeTab = this.container.querySelector('[data-tab="home"]');
      if (homeTab)
        homeTab.classList.add("sp-nav-active");
    },
    updateNotificationBadge() {
      if (typeof frappe === "undefined")
        return;
      try {
        frappe.xcall("frappe.client.get_count", {
          doctype: "Notification Log",
          filters: { read: 0 }
        }).then((count) => {
          const badge = document.getElementById("sp-badge-notifications");
          if (badge && count > 0) {
            badge.textContent = count > 99 ? "99+" : count;
            badge.style.display = "flex";
          } else if (badge) {
            badge.style.display = "none";
          }
        }).catch(() => {
        });
      } catch (e) {
      }
    },
    getIcon(name) {
      const icons = {
        home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/></svg>',
        grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
        search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
        user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
      };
      return icons[name] || "";
    },
    destroy() {
      if (this.container) {
        this.container.remove();
        document.body.style.paddingBottom = "";
      }
    }
  };
  var mobile_nav_default = SmartPlanNav;

  // ../smartplan_medical/smartplan_medical/public/js/pwa/touch_gestures.js
  var SmartPlanGestures = {
    init() {
      if (!document.documentElement.classList.contains("sp-mobile"))
        return;
      this.setupSwipeBack();
    },
    setupSwipeBack() {
      let startX = 0;
      let startY = 0;
      let swiping = false;
      document.addEventListener("touchstart", (e) => {
        if (e.touches[0].clientX > 30)
          return;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        swiping = true;
      }, { passive: true });
      document.addEventListener("touchmove", (e) => {
        if (!swiping)
          return;
        const deltaY = Math.abs(e.touches[0].clientY - startY);
        if (deltaY > 50)
          swiping = false;
      }, { passive: true });
      document.addEventListener("touchend", (e) => {
        if (!swiping)
          return;
        swiping = false;
        const deltaX = e.changedTouches[0].clientX - startX;
        if (deltaX > 100) {
          window.history.back();
        }
      }, { passive: true });
    }
  };
  var touch_gestures_default = SmartPlanGestures;

  // ../smartplan_medical/smartplan_medical/public/js/pwa/form_enhancer.js
  var SmartPlanForms = {
    fab: null,
    init() {
      this.enhanceForms();
      this.createFAB();
      this.bindFormEvents();
    },
    enhanceForms() {
      var _a, _b;
      if (typeof frappe === "undefined")
        return;
      const originalMakeControl = (_b = (_a = frappe.ui.form.ControlTable) == null ? void 0 : _a.prototype) == null ? void 0 : _b.make;
      if (originalMakeControl) {
        const self = this;
        frappe.ui.form.ControlTable.prototype.make = function() {
          originalMakeControl.call(this);
          if (document.documentElement.classList.contains("sp-mobile")) {
            self.enhanceTable(this);
          }
        };
      }
    },
    enhanceTable(control) {
      if (!control.$wrapper)
        return;
      const toggleBtn = $(`
            <button class="btn btn-xs sp-table-toggle" title="${__("Toggle card view")}">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                    <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
                </svg>
            </button>
        `);
      control.$wrapper.find(".grid-heading-row .row-index").prepend(toggleBtn);
      toggleBtn.on("click", (e) => {
        e.stopPropagation();
        control.$wrapper.toggleClass("sp-card-view");
      });
      if (window.innerWidth <= 576) {
        control.$wrapper.addClass("sp-card-view");
      }
      control.$wrapper.find('.frappe-control[data-fieldtype="Table"] .form-group').addClass("sp-table-scroll");
    },
    createFAB() {
      var _a;
      if (!document.documentElement.classList.contains("sp-mobile"))
        return;
      if (document.getElementById("sp-fab-container"))
        return;
      const fabContainer = document.createElement("div");
      fabContainer.id = "sp-fab-container";
      fabContainer.className = "sp-fab-container";
      fabContainer.innerHTML = `
            <div class="sp-fab-actions" id="sp-fab-actions" style="display:none;">
                <button class="sp-fab-action" data-action="save" title="${__("Save")}">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                        <polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
                    </svg>
                    <span>${__("Save")}</span>
                </button>
                <button class="sp-fab-action sp-fab-submit" data-action="submit" title="${__("Submit")}">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>${__("Submit")}</span>
                </button>
                <button class="sp-fab-action" data-action="new" title="${__("New")}">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    <span>${__("New")}</span>
                </button>
            </div>
            <button class="sp-fab-main" id="sp-fab-main" aria-label="${__("Actions")}">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
            </button>
        `;
      document.body.appendChild(fabContainer);
      (_a = document.getElementById("sp-fab-main")) == null ? void 0 : _a.addEventListener("click", () => {
        fabContainer.classList.toggle("sp-fab-open");
        const actionsEl = document.getElementById("sp-fab-actions");
        if (actionsEl) {
          actionsEl.style.display = fabContainer.classList.contains("sp-fab-open") ? "flex" : "none";
        }
      });
      fabContainer.querySelectorAll(".sp-fab-action").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          const action = btn.dataset.action;
          this.handleFABAction(action);
          fabContainer.classList.remove("sp-fab-open");
          document.getElementById("sp-fab-actions").style.display = "none";
        });
      });
      this.fab = fabContainer;
    },
    handleFABAction(action) {
      if (typeof frappe === "undefined")
        return;
      switch (action) {
        case "save":
          if (cur_frm) {
            cur_frm.save();
          } else if (cur_list) {
            cur_list.make_new_doc();
          }
          break;
        case "submit":
          if (cur_frm && cur_frm.doc.docstatus === 0) {
            cur_frm.submit();
          }
          break;
        case "new":
          if (cur_frm) {
            frappe.new_doc(cur_frm.doctype);
          } else if (cur_list) {
            cur_list.make_new_doc();
          }
          break;
      }
    },
    updateFABVisibility() {
      var _a;
      if (!this.fab)
        return;
      const isMobile = document.documentElement.classList.contains("sp-mobile");
      const isForm = !!cur_frm;
      const isList = !!cur_list;
      if (isMobile && (isForm || isList)) {
        this.fab.style.display = "block";
        const submitBtn = this.fab.querySelector('[data-action="submit"]');
        if (submitBtn) {
          const canSubmit = isForm && cur_frm.doc.docstatus === 0 && ((_a = cur_frm.perm[0]) == null ? void 0 : _a.submit);
          submitBtn.style.display = canSubmit ? "flex" : "none";
        }
      } else {
        this.fab.style.display = "none";
      }
    },
    bindFormEvents() {
      if (typeof frappe === "undefined")
        return;
      if (frappe.router) {
        frappe.router.on("change", () => {
          setTimeout(() => this.updateFABVisibility(), 300);
        });
      }
      $(document).on("form-load form-refresh", () => {
        setTimeout(() => this.updateFABVisibility(), 300);
      });
      $(document).on("form-load", () => {
        if (!document.documentElement.classList.contains("sp-mobile"))
          return;
        this.addStickyHeaders();
      });
    },
    addStickyHeaders() {
      document.querySelectorAll(".section-head").forEach((header) => {
        header.classList.add("sp-sticky-section");
      });
    }
  };
  var form_enhancer_default = SmartPlanForms;

  // ../smartplan_medical/smartplan_medical/public/js/mobile_ux.bundle.js
  $(document).on("startup", function() {
    const isMobile = window.innerWidth <= 768 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    if (isMobile) {
      console.log("[SmartPlan UX] Initializing mobile enhancements...");
      mobile_nav_default.init();
      touch_gestures_default.init();
      form_enhancer_default.init();
      $("body").addClass("sp-sidebar-collapsed");
      frappe.router.on("change", () => {
        const route = frappe.get_route();
        document.body.dataset.spRoute = route ? route[0] : "home";
      });
      console.log("[SmartPlan UX] Mobile enhancements initialized");
    }
    enhanceDialogs();
    enhanceLists();
  });
  function enhanceDialogs() {
    const originalShow = frappe.ui.Dialog.prototype.show;
    if (originalShow) {
      frappe.ui.Dialog.prototype.show = function() {
        originalShow.call(this);
        if (document.documentElement.classList.contains("sp-mobile")) {
          this.$wrapper.addClass("sp-mobile-dialog");
        }
      };
    }
  }
  function enhanceLists() {
    if (!document.documentElement.classList.contains("sp-mobile"))
      return;
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          var _a;
          if (node.nodeType === 1 && ((_a = node.classList) == null ? void 0 : _a.contains("list-row"))) {
            node.classList.add("sp-list-card");
          }
        });
      });
    });
    const listContainer = document.querySelector("#page-List, .page-container");
    if (listContainer) {
      observer.observe(listContainer, { childList: true, subtree: true });
    }
    if (typeof frappe !== "undefined" && frappe.router) {
      frappe.router.on("change", () => {
        setTimeout(() => {
          const newContainer = document.querySelector(".result, .list-rows");
          if (newContainer) {
            observer.observe(newContainer, { childList: true, subtree: true });
          }
        }, 500);
      });
    }
  }
  window.SmartPlanUX = {
    Nav: mobile_nav_default,
    Gestures: touch_gestures_default,
    Forms: form_enhancer_default
  };
})();
//# sourceMappingURL=mobile_ux.bundle.EZVNERI5.js.map
