/**
 * SmartPlan Medical — Install Prompt Handler
 * Captures the beforeinstallprompt event and provides custom install UI.
 */

const SmartPlanInstall = {
    deferredPrompt: null,
    isInstalled: false,

    init() {
        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
            this.isInstalled = true;
            document.documentElement.classList.add('sp-pwa-standalone');
            console.log('[PWA] Running in standalone mode');
            return;
        }

        // Capture the install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            console.log('[PWA] Install prompt captured');
            this.showInstallBanner();
        });

        // Track successful installation
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.deferredPrompt = null;
            this.hideInstallBanner();
            document.documentElement.classList.add('sp-pwa-standalone');
            console.log('[PWA] App installed successfully');

            if (typeof frappe !== 'undefined' && frappe.show_alert) {
                frappe.show_alert({
                    message: __('App installed successfully! You can now access it from your home screen.'),
                    indicator: 'green',
                }, 7);
            }
        });

        // iOS detection
        this.checkiOS();
    },

    showInstallBanner() {
        // Don't show if user dismissed it recently
        const dismissed = localStorage.getItem('sp_install_dismissed');
        if (dismissed && Date.now() - parseInt(dismissed) < 7 * 24 * 60 * 60 * 1000) {
            return;
        }

        // Create install banner
        const banner = document.createElement('div');
        banner.id = 'sp-install-banner';
        banner.innerHTML = `
            <div class="sp-install-content">
                <div class="sp-install-icon">
                    <img src="/assets/smartplan_medical/icons/icon-96x96.png" alt="App Icon" width="48" height="48">
                </div>
                <div class="sp-install-text">
                    <strong>${__('Install SmartPlan')}</strong>
                    <span>${__('Add to home screen for quick access')}</span>
                </div>
                <div class="sp-install-actions">
                    <button class="sp-install-btn" id="sp-install-accept">${__('Install')}</button>
                    <button class="sp-install-dismiss" id="sp-install-dismiss">✕</button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // Animate in
        requestAnimationFrame(() => {
            banner.classList.add('sp-install-visible');
        });

        // Bind events
        document.getElementById('sp-install-accept')?.addEventListener('click', () => {
            this.promptInstall();
        });

        document.getElementById('sp-install-dismiss')?.addEventListener('click', () => {
            this.hideInstallBanner();
            localStorage.setItem('sp_install_dismissed', Date.now().toString());
        });
    },

    hideInstallBanner() {
        const banner = document.getElementById('sp-install-banner');
        if (banner) {
            banner.classList.remove('sp-install-visible');
            setTimeout(() => banner.remove(), 400);
        }
    },

    async promptInstall() {
        if (!this.deferredPrompt) return;

        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;

        console.log('[PWA] Install prompt outcome:', outcome);
        this.deferredPrompt = null;
        this.hideInstallBanner();
    },

    checkiOS() {
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
        const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);

        if (isIOS && isSafari && !window.navigator.standalone) {
            // Show iOS instructions after a delay
            setTimeout(() => {
                this.showIOSInstructions();
            }, 10000);
        }
    },

    showIOSInstructions() {
        const dismissed = localStorage.getItem('sp_ios_install_dismissed');
        if (dismissed && Date.now() - parseInt(dismissed) < 30 * 24 * 60 * 60 * 1000) {
            return;
        }

        if (typeof frappe !== 'undefined' && frappe.msgprint) {
            const d = frappe.msgprint({
                title: __('Install SmartPlan'),
                indicator: 'blue',
                message: `
                    <div style="text-align: center; padding: 16px 0;">
                        <img src="/assets/smartplan_medical/icons/icon-96x96.png"
                             alt="App Icon" width="64" height="64"
                             style="border-radius: 14px; margin-bottom: 16px;">
                        <p style="font-size: 15px; margin-bottom: 20px;">
                            ${__('Install this app on your iPhone for the best experience:')}
                        </p>
                        <ol style="text-align: left; font-size: 14px; line-height: 2;">
                            <li>${__('Tap the <strong>Share</strong> button')} <span style="font-size: 18px;">⬆</span></li>
                            <li>${__('Scroll down and tap <strong>"Add to Home Screen"</strong>')}</li>
                            <li>${__('Tap <strong>"Add"</strong> in the top right')}</li>
                        </ol>
                    </div>
                `,
            });

            if (d && d.$wrapper) {
                d.$wrapper.on('hidden.bs.modal', () => {
                    localStorage.setItem('sp_ios_install_dismissed', Date.now().toString());
                });
            }
        }
    },
};

export default SmartPlanInstall;
