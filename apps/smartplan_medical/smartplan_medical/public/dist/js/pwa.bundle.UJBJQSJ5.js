(() => {
  // ../smartplan_medical/smartplan_medical/public/js/pwa/sw_register.js
  var SmartPlanSW = {
    SW_URL: "/assets/smartplan_medical/js/service-worker.js",
    registration: null,
    retryCount: 0,
    maxRetries: 3,
    async init() {
      if (!("serviceWorker" in navigator)) {
        console.warn("[PWA] Service Workers not supported");
        return;
      }
      try {
        this.registration = await navigator.serviceWorker.register(this.SW_URL, {
          scope: "/"
        });
        console.log("[PWA] Service Worker registered:", this.registration.scope);
        this.retryCount = 0;
        this.registration.addEventListener("updatefound", () => {
          const newWorker = this.registration.installing;
          if (!newWorker)
            return;
          newWorker.addEventListener("statechange", () => {
            if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
              this.showUpdateNotification();
            }
          });
        });
        setInterval(() => {
          this.registration.update();
        }, 30 * 60 * 1e3);
      } catch (error) {
        console.error("[PWA] SW registration failed:", error);
        if (this.retryCount < this.maxRetries) {
          this.retryCount++;
          const delay = Math.pow(2, this.retryCount) * 2e3;
          console.log(`[PWA] Retrying in ${delay / 1e3}s (attempt ${this.retryCount}/${this.maxRetries})`);
          setTimeout(() => this.init(), delay);
        }
      }
    },
    showUpdateNotification() {
      if (typeof frappe !== "undefined" && frappe.show_alert) {
        frappe.show_alert({
          message: __('A new version is available. <a onclick="location.reload(true)">Refresh</a> to update.'),
          indicator: "blue"
        }, 10);
      }
    }
  };
  var sw_register_default = SmartPlanSW;

  // ../smartplan_medical/smartplan_medical/public/js/pwa/install_prompt.js
  var SmartPlanInstall = {
    deferredPrompt: null,
    isInstalled: false,
    init() {
      if (window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone) {
        this.isInstalled = true;
        document.documentElement.classList.add("sp-pwa-standalone");
        console.log("[PWA] Running in standalone mode");
        return;
      }
      window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        this.deferredPrompt = e;
        console.log("[PWA] Install prompt captured");
        this.showInstallBanner();
      });
      window.addEventListener("appinstalled", () => {
        this.isInstalled = true;
        this.deferredPrompt = null;
        this.hideInstallBanner();
        document.documentElement.classList.add("sp-pwa-standalone");
        console.log("[PWA] App installed successfully");
        if (typeof frappe !== "undefined" && frappe.show_alert) {
          frappe.show_alert({
            message: __("App installed successfully! You can now access it from your home screen."),
            indicator: "green"
          }, 7);
        }
      });
      this.checkiOS();
    },
    showInstallBanner() {
      var _a, _b;
      const dismissed = localStorage.getItem("sp_install_dismissed");
      if (dismissed && Date.now() - parseInt(dismissed) < 7 * 24 * 60 * 60 * 1e3) {
        return;
      }
      const banner = document.createElement("div");
      banner.id = "sp-install-banner";
      banner.innerHTML = `
            <div class="sp-install-content">
                <div class="sp-install-icon">
                    <img src="/assets/smartplan_medical/icons/icon-96x96.png" alt="App Icon" width="48" height="48">
                </div>
                <div class="sp-install-text">
                    <strong>${__("Install SmartPlan")}</strong>
                    <span>${__("Add to home screen for quick access")}</span>
                </div>
                <div class="sp-install-actions">
                    <button class="sp-install-btn" id="sp-install-accept">${__("Install")}</button>
                    <button class="sp-install-dismiss" id="sp-install-dismiss">\u2715</button>
                </div>
            </div>
        `;
      document.body.appendChild(banner);
      requestAnimationFrame(() => {
        banner.classList.add("sp-install-visible");
      });
      (_a = document.getElementById("sp-install-accept")) == null ? void 0 : _a.addEventListener("click", () => {
        this.promptInstall();
      });
      (_b = document.getElementById("sp-install-dismiss")) == null ? void 0 : _b.addEventListener("click", () => {
        this.hideInstallBanner();
        localStorage.setItem("sp_install_dismissed", Date.now().toString());
      });
    },
    hideInstallBanner() {
      const banner = document.getElementById("sp-install-banner");
      if (banner) {
        banner.classList.remove("sp-install-visible");
        setTimeout(() => banner.remove(), 400);
      }
    },
    async promptInstall() {
      if (!this.deferredPrompt)
        return;
      this.deferredPrompt.prompt();
      const { outcome } = await this.deferredPrompt.userChoice;
      console.log("[PWA] Install prompt outcome:", outcome);
      this.deferredPrompt = null;
      this.hideInstallBanner();
    },
    checkiOS() {
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
      const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
      if (isIOS && isSafari && !window.navigator.standalone) {
        setTimeout(() => {
          this.showIOSInstructions();
        }, 1e4);
      }
    },
    showIOSInstructions() {
      const dismissed = localStorage.getItem("sp_ios_install_dismissed");
      if (dismissed && Date.now() - parseInt(dismissed) < 30 * 24 * 60 * 60 * 1e3) {
        return;
      }
      if (typeof frappe !== "undefined" && frappe.msgprint) {
        const d = frappe.msgprint({
          title: __("Install SmartPlan"),
          indicator: "blue",
          message: `
                    <div style="text-align: center; padding: 16px 0;">
                        <img src="/assets/smartplan_medical/icons/icon-96x96.png"
                             alt="App Icon" width="64" height="64"
                             style="border-radius: 14px; margin-bottom: 16px;">
                        <p style="font-size: 15px; margin-bottom: 20px;">
                            ${__("Install this app on your iPhone for the best experience:")}
                        </p>
                        <ol style="text-align: left; font-size: 14px; line-height: 2;">
                            <li>${__("Tap the <strong>Share</strong> button")} <span style="font-size: 18px;">\u2B06</span></li>
                            <li>${__('Scroll down and tap <strong>"Add to Home Screen"</strong>')}</li>
                            <li>${__('Tap <strong>"Add"</strong> in the top right')}</li>
                        </ol>
                    </div>
                `
        });
        if (d && d.$wrapper) {
          d.$wrapper.on("hidden.bs.modal", () => {
            localStorage.setItem("sp_ios_install_dismissed", Date.now().toString());
          });
        }
      }
    }
  };
  var install_prompt_default = SmartPlanInstall;

  // ../smartplan_medical/smartplan_medical/public/js/pwa/offline_handler.js
  var SmartPlanOffline = {
    isOnline: navigator.onLine,
    indicator: null,
    syncQueue: [],
    init() {
      window.addEventListener("online", () => this.handleOnline());
      window.addEventListener("offline", () => this.handleOffline());
      if (!navigator.onLine) {
        this.handleOffline();
      }
    },
    handleOnline() {
      this.isOnline = true;
      document.documentElement.classList.remove("sp-offline");
      document.documentElement.classList.add("sp-online");
      this.hideOfflineIndicator();
      if (typeof frappe !== "undefined" && frappe.show_alert) {
        frappe.show_alert({
          message: __("Back online \u2713"),
          indicator: "green"
        }, 3);
      }
      this.processQueue();
    },
    handleOffline() {
      this.isOnline = false;
      document.documentElement.classList.add("sp-offline");
      document.documentElement.classList.remove("sp-online");
      this.showOfflineIndicator();
      if (typeof frappe !== "undefined" && frappe.show_alert) {
        frappe.show_alert({
          message: __("You are offline. Some features may be limited."),
          indicator: "orange"
        }, 5);
      }
    },
    showOfflineIndicator() {
      if (this.indicator)
        return;
      this.indicator = document.createElement("div");
      this.indicator.id = "sp-offline-indicator";
      this.indicator.innerHTML = `
            <div class="sp-offline-content">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                    <line x1="3" y1="13" x2="13" y2="3" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <span>${__("Offline")}</span>
            </div>
        `;
      document.body.appendChild(this.indicator);
      requestAnimationFrame(() => {
        this.indicator.classList.add("sp-offline-visible");
      });
    },
    hideOfflineIndicator() {
      if (this.indicator) {
        this.indicator.classList.remove("sp-offline-visible");
        setTimeout(() => {
          var _a;
          (_a = this.indicator) == null ? void 0 : _a.remove();
          this.indicator = null;
        }, 400);
      }
    },
    queueSubmission(doctype, docname, data) {
      const entry = {
        id: `${doctype}-${docname}-${Date.now()}`,
        doctype,
        docname,
        data,
        timestamp: Date.now()
      };
      this.syncQueue.push(entry);
      localStorage.setItem("sp_sync_queue", JSON.stringify(this.syncQueue));
      if (typeof frappe !== "undefined" && frappe.show_alert) {
        frappe.show_alert({
          message: __("Changes will be saved when you're back online."),
          indicator: "blue"
        }, 5);
      }
      if ("serviceWorker" in navigator && "SyncManager" in window) {
        navigator.serviceWorker.ready.then((reg) => {
          return reg.sync.register("smartplan-form-sync");
        }).catch(console.warn);
      }
    },
    async processQueue() {
      const stored = localStorage.getItem("sp_sync_queue");
      if (stored) {
        try {
          this.syncQueue = JSON.parse(stored);
        } catch (e) {
          this.syncQueue = [];
        }
      }
      if (this.syncQueue.length === 0)
        return;
      console.log(`[PWA] Processing ${this.syncQueue.length} queued submissions`);
      const processed = [];
      for (const entry of this.syncQueue) {
        try {
          await frappe.call({
            method: "frappe.client.save",
            args: { doc: entry.data },
            async: true
          });
          processed.push(entry.id);
          console.log(`[PWA] Synced: ${entry.doctype}/${entry.docname}`);
        } catch (error) {
          console.warn(`[PWA] Failed to sync: ${entry.doctype}/${entry.docname}`, error);
        }
      }
      this.syncQueue = this.syncQueue.filter((e) => !processed.includes(e.id));
      localStorage.setItem("sp_sync_queue", JSON.stringify(this.syncQueue));
      if (processed.length > 0 && typeof frappe !== "undefined" && frappe.show_alert) {
        frappe.show_alert({
          message: __(`${processed.length} offline change(s) synced successfully.`),
          indicator: "green"
        }, 5);
      }
    }
  };
  var offline_handler_default = SmartPlanOffline;

  // ../smartplan_medical/smartplan_medical/public/js/pwa.bundle.js
  $(document).on("startup", function() {
    console.log("[SmartPlan PWA] Initializing...");
    sw_register_default.init();
    install_prompt_default.init();
    offline_handler_default.init();
    if (!document.querySelector('link[rel="manifest"]')) {
      const manifestLink = document.createElement("link");
      manifestLink.rel = "manifest";
      manifestLink.href = "/api/method/smartplan_medical.api.get_manifest";
      manifestLink.crossOrigin = "use-credentials";
      document.head.appendChild(manifestLink);
    }
    let themeColorMeta = document.querySelector('meta[name="theme-color"]');
    if (themeColorMeta) {
      themeColorMeta.content = "#0D1B2A";
    } else {
      themeColorMeta = document.createElement("meta");
      themeColorMeta.name = "theme-color";
      themeColorMeta.content = "#0D1B2A";
      document.head.appendChild(themeColorMeta);
    }
    const isMobile = window.innerWidth <= 768 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    const isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone;
    if (isMobile || isStandalone) {
      document.documentElement.classList.add("smartplan-pwa");
      document.documentElement.classList.add("sp-mobile");
    }
    const mobileQuery = window.matchMedia("(max-width: 768px)");
    mobileQuery.addEventListener("change", (e) => {
      document.documentElement.classList.toggle("sp-mobile", e.matches);
      document.documentElement.classList.toggle("smartplan-pwa", e.matches || isStandalone);
    });
    console.log("[SmartPlan PWA] Initialized successfully");
  });
  window.SmartPlanPWA = {
    SW: sw_register_default,
    Install: install_prompt_default,
    Offline: offline_handler_default
  };
})();
//# sourceMappingURL=pwa.bundle.UJBJQSJ5.js.map
