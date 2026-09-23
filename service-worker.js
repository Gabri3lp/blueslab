// Service Worker for Blues Lab - Caches App Shell & External Assets for instant startup
const CACHE_NAME = 'blueslab-shell-v1';

const STATIC_ASSETS = [
    './',
    'index.html',
    'css/app.css',
    'js/dbCache.js?v=3',
    'js/gridTooltip.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
    '_framework/blazor.webassembly.js'
];

self.addEventListener('install', event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            for (const asset of STATIC_ASSETS) {
                try {
                    await cache.add(new Request(asset, { cache: 'reload' }));
                } catch (e) {
                    console.warn('[SW] Failed to pre-cache asset:', asset, e);
                }
            }
        })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(k => k.startsWith('blueslab-shell-') && k !== CACHE_NAME)
                    .map(k => caches.delete(k))
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const req = event.request;
    const url = new URL(req.url);

    // Skip non-GET requests
    if (req.method !== 'GET') return;

    // Do not intercept data API or dynamic pair requests handled by dbCache
    if (url.pathname.includes('/data/') || url.pathname.includes('/locales/')) {
        return;
    }

    // Do not intercept _framework/ .wasm / .dat files which are managed by Blazor's own cache
    if (url.pathname.includes('/_framework/') && (url.pathname.endsWith('.wasm') || url.pathname.endsWith('.dat') || url.pathname.endsWith('.blat'))) {
        return;
    }

    // For index.html or root navigation: Network-First with Cache Fallback for instant offline/reload
    if (req.mode === 'navigate' || url.pathname.endsWith('index.html') || url.pathname.endsWith('/')) {
        event.respondWith(
            fetch(req)
                .then(networkResponse => {
                    if (networkResponse && networkResponse.ok) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(req, copy));
                    }
                    return networkResponse;
                })
                .catch(() => caches.match(req).then(cached => cached || caches.match('index.html')))
        );
        return;
    }

    // For CDN resources (Bootstrap, icons, fonts) and static JS/CSS: Cache-First + Stale-While-Revalidate
    if (url.origin.includes('jsdelivr.net') || url.origin.includes('googleapis.com') || url.origin.includes('gstatic.com') || url.pathname.endsWith('.css') || url.pathname.endsWith('.js')) {
        event.respondWith(
            caches.open(CACHE_NAME).then(async cache => {
                const cached = await cache.match(req);
                const fetchPromise = fetch(req).then(networkResponse => {
                    if (networkResponse && networkResponse.ok) {
                        cache.put(req, networkResponse.clone());
                    }
                    return networkResponse;
                }).catch(() => null);

                return cached || fetchPromise;
            })
        );
        return;
    }
});
