/**
 * SmartPlan Medical — Service Worker
 * Production-grade caching strategies for ERPNext PWA
 *
 * Strategies:
 *   Static assets (JS/CSS/fonts/images) → Cache First
 *   API calls (/api/) → Network First with 5s timeout
 *   HTML pages → Network First
 *   Offline fallback → Cache Only (pre-cached)
 */

const CACHE_VERSION = 'smartplan-pwa-v2';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const API_CACHE = `${CACHE_VERSION}-api`;

// Assets to pre-cache on install
const PRECACHE_URLS = [
    '/assets/smartplan_medical/offline.html',
    '/assets/smartplan_medical/icons/icon-192x192.png',
    '/assets/smartplan_medical/icons/icon-512x512.png',
];

// ─── INSTALL ─────────────────────────────────────
self.addEventListener('install', (event) => {
    console.log('[SW] Installing SmartPlan PWA Service Worker...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Pre-caching offline assets');
                return cache.addAll(PRECACHE_URLS);
            })
            .then(() => self.skipWaiting())
            .catch((err) => {
                console.warn('[SW] Pre-cache failed (non-fatal):', err);
                return self.skipWaiting();
            })
    );
});

// ─── ACTIVATE ────────────────────────────────────
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating SmartPlan PWA Service Worker...');
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name.startsWith('smartplan-pwa-') && name !== STATIC_CACHE && name !== DYNAMIC_CACHE && name !== API_CACHE)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// ─── FETCH ───────────────────────────────────────
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests (POST/PUT/DELETE go straight to network)
    if (request.method !== 'GET') {
        return;
    }

    // Skip WebSocket and realtime connections
    if (url.pathname.startsWith('/socket.io') || url.protocol === 'ws:' || url.protocol === 'wss:') {
        return;
    }

    // Skip Chrome extension requests
    if (url.protocol === 'chrome-extension:') {
        return;
    }

    // ── API CALLS: Network First with timeout ──
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstWithTimeout(request, API_CACHE, 5000));
        return;
    }

    // ── STATIC ASSETS: Cache First ──
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
        return;
    }

    // ── HTML / NAVIGATION: Network First ──
    if (request.headers.get('accept')?.includes('text/html') || url.pathname.startsWith('/app')) {
        event.respondWith(networkFirstHTML(request));
        return;
    }

    // ── EVERYTHING ELSE: Network First ──
    event.respondWith(networkFirstWithTimeout(request, DYNAMIC_CACHE, 5000));
});

// ─── BACKGROUND SYNC (for offline form submissions) ──
self.addEventListener('sync', (event) => {
    if (event.tag === 'smartplan-form-sync') {
        console.log('[SW] Background sync: processing queued form submissions');
        event.waitUntil(processQueuedSubmissions());
    }
});

// ─── PUSH NOTIFICATIONS ──────────────────────────
self.addEventListener('push', (event) => {
    if (!event.data) return;

    try {
        const data = event.data.json();
        const options = {
            body: data.body || '',
            icon: '/assets/smartplan_medical/icons/icon-192x192.png',
            badge: '/assets/smartplan_medical/icons/icon-72x72.png',
            vibrate: [100, 50, 100],
            data: {
                url: data.click_action || data.url || '/app',
            },
            actions: data.actions || [],
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'SmartPlan Medical', options)
        );
    } catch (e) {
        console.warn('[SW] Push parse error:', e);
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.url || '/app';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clients) => {
                // Focus existing window if available
                for (const client of clients) {
                    if (client.url.includes(url) && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (self.clients.openWindow) {
                    return self.clients.openWindow(url);
                }
            })
    );
});


// ═══════════════════════════════════════════════
// CACHING STRATEGIES
// ═══════════════════════════════════════════════

/**
 * Cache First — Serve from cache, fallback to network.
 * Best for versioned static assets.
 */
async function cacheFirst(request, cacheName) {
    try {
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        const networkResponse = await fetch(request);
        if (networkResponse.status === 200) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.warn('[SW] Cache First failed:', error);
        return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
    }
}

/**
 * Network First with timeout — Try network, fall back to cache.
 * Best for API calls and dynamic content.
 */
async function networkFirstWithTimeout(request, cacheName, timeoutMs) {
    try {
        const networkPromise = fetch(request);
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Network timeout')), timeoutMs)
        );

        const response = await Promise.race([networkPromise, timeoutPromise]);

        if (response.status === 200) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Network failed or timed out — try cache
        const cached = await caches.match(request);
        if (cached) {
            console.log('[SW] Serving from cache (network failed):', request.url);
            return cached;
        }
        return new Response(JSON.stringify({ exc: 'Offline' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' },
        });
    }
}

/**
 * Network First for HTML — Serve from network, offline fallback.
 */
async function networkFirstHTML(request) {
    try {
        const response = await fetch(request);
        if (response.status === 200) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Try cached version first
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        // Serve offline page
        const offlinePage = await caches.match('/assets/smartplan_medical/offline.html');
        if (offlinePage) {
            return offlinePage;
        }
        return new Response('<h1>Offline</h1><p>Please check your connection.</p>', {
            headers: { 'Content-Type': 'text/html' },
        });
    }
}

/**
 * Check if a URL is a static asset that should be cache-first.
 */
function isStaticAsset(pathname) {
    const staticExtensions = [
        '.js', '.css', '.woff', '.woff2', '.ttf', '.eot',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico',
        '.mp3', '.wav',
    ];
    // Assets directory
    if (pathname.startsWith('/assets/')) {
        return staticExtensions.some(ext => pathname.endsWith(ext));
    }
    // Google Fonts
    if (pathname.includes('fonts.googleapis.com') || pathname.includes('fonts.gstatic.com')) {
        return true;
    }
    return false;
}

/**
 * Process queued form submissions (Background Sync)
 */
async function processQueuedSubmissions() {
    // Read from IndexedDB queue
    // This is a placeholder — the actual implementation uses the
    // offline_handler.js queue mechanism on the client side
    console.log('[SW] Background sync: No pending submissions');
}
