// Persistent CacheStorage & In-Memory Preloader for Blues Lab database and locales
window.bluesLabCache = {
    CACHE_NAME: 'blueslab-data-v2',
    _inMemoryCache: new Map(),

    // Checks if CacheStorage API is available
    isSupported: function () {
        return typeof window !== 'undefined' && 'caches' in window;
    },

    // Resolves url to absolute URL based on document.baseURI
    resolveUrl: function (url) {
        try {
            return new URL(url, document.baseURI).href;
        } catch (e) {
            return url;
        }
    },

    // Automatically cleans up outdated cache versions
    init: async function () {
        if (!this.isSupported()) return;
        try {
            const keys = await caches.keys();
            for (const key of keys) {
                if (key.startsWith('blueslab-data-') && key !== this.CACHE_NAME) {
                    console.log('[BluesLab Cache] Evicting outdated cache store:', key);
                    await caches.delete(key);
                }
            }
        } catch (e) {
            // Ignore in restricted environments
        }
    },

    // Preloads a JSON resource asynchronously into memory and CacheStorage
    preload: function (url) {
        const fullUrl = this.resolveUrl(url);
        if (this._inMemoryCache.has(fullUrl)) {
            return this._inMemoryCache.get(fullUrl);
        }

        const promise = (async () => {
            // 1. Try CacheStorage first
            if (this.isSupported()) {
                try {
                    const cache = await caches.open(this.CACHE_NAME);
                    const cachedResponse = await cache.match(fullUrl);
                    if (cachedResponse) {
                        const cachedText = await cachedResponse.text();
                        const trimmed = (cachedText || '').trim();
                        if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                            this.revalidate(cache, fullUrl);
                            return cachedText;
                        } else {
                            await cache.delete(fullUrl);
                        }
                    }
                } catch (e) {}
            }

            // 2. Fallback to network fetch
            try {
                const response = await fetch(fullUrl);
                if (response && response.ok) {
                    const text = await response.text();
                    const trimmed = (text || '').trim();
                    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                        if (this.isSupported()) {
                            try {
                                const cache = await caches.open(this.CACHE_NAME);
                                await cache.put(fullUrl, new Response(text, {
                                    status: 200,
                                    headers: { 'Content-Type': 'application/json' }
                                }));
                            } catch (e) {}
                        }
                        return text;
                    }
                }
            } catch (err) {
                console.warn('[BluesLab Cache] Preload fetch failed for', fullUrl, err);
            }
            return null;
        })();

        this._inMemoryCache.set(fullUrl, promise);
        return promise;
    },

    // Fetches JSON content with In-Memory + Cache-First + Stale-While-Revalidate strategy
    fetchJson: async function (url) {
        const fullUrl = this.resolveUrl(url);

        // 1. Check in-memory preloaded cache first (0ms latency)
        if (this._inMemoryCache.has(fullUrl)) {
            const preloaded = await this._inMemoryCache.get(fullUrl);
            if (preloaded) {
                return preloaded;
            }
        }

        if (!this.isSupported()) {
            try {
                const fallback = await fetch(fullUrl);
                if (fallback && fallback.ok) {
                    const text = await fallback.text();
                    const trimmed = text.trim();
                    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                        this._inMemoryCache.set(fullUrl, Promise.resolve(text));
                        return text;
                    }
                }
            } catch (e) {}
            return null;
        }

        try {
            const cache = await caches.open(this.CACHE_NAME);
            const cachedResponse = await cache.match(fullUrl);

            if (cachedResponse) {
                const cachedText = await cachedResponse.text();
                const trimmed = (cachedText || '').trim();
                if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                    // Valid JSON cached, trigger background revalidation
                    this.revalidate(cache, fullUrl);
                    this._inMemoryCache.set(fullUrl, Promise.resolve(cachedText));
                    return cachedText;
                } else {
                    // Cached item is corrupted or HTML fallback, evict it
                    console.warn('[BluesLab Cache] Evicting corrupted cache item for', fullUrl);
                    await cache.delete(fullUrl);
                }
            }

            // Not in cache (or evicted), fetch from network and store
            const networkResponse = await fetch(fullUrl);
            if (networkResponse && networkResponse.ok) {
                const text = await networkResponse.text();
                const trimmed = text.trim();
                // Ensure it's valid JSON and not an HTML 404 fallback
                if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) {
                    throw new Error('Server returned HTML or non-JSON for ' + fullUrl);
                }

                // Store clone in cache & memory
                try {
                    await cache.put(fullUrl, new Response(text, {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                } catch (e) {
                    // Ignore quota or private mode errors
                }
                this._inMemoryCache.set(fullUrl, Promise.resolve(text));
                return text;
            } else {
                throw new Error('Network response not ok: ' + (networkResponse ? networkResponse.status : 'unknown'));
            }
        } catch (err) {
            console.warn('[BluesLab Cache] Cache fetch failed for', fullUrl, err);
            try {
                const fallback = await fetch(fullUrl);
                if (fallback && fallback.ok) {
                    const fbText = await fallback.text();
                    const trimmedFb = fbText.trim();
                    if (trimmedFb.startsWith('{') || trimmedFb.startsWith('[')) {
                        this._inMemoryCache.set(fullUrl, Promise.resolve(fbText));
                        return fbText;
                    }
                }
            } catch (e2) {}
            return null;
        }
    },

    // Silent background revalidation
    revalidate: function (cache, fullUrl) {
        setTimeout(async () => {
            try {
                const res = await fetch(fullUrl, { cache: 'no-cache' });
                if (res && res.ok) {
                    const text = await res.text();
                    const trimmed = text.trim();
                    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                        await cache.put(fullUrl, new Response(text, {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        }));
                        this._inMemoryCache.set(fullUrl, Promise.resolve(text));
                    }
                }
            } catch (e) {
                // Silent fail for background revalidation
            }
        }, 200);
    },

    // Delete a specific URL from cache
    delete: async function (url) {
        const fullUrl = this.resolveUrl(url);
        this._inMemoryCache.delete(fullUrl);
        if (!this.isSupported()) return;
        try {
            const cache = await caches.open(this.CACHE_NAME);
            await cache.delete(fullUrl);
        } catch (e) {}
    },

    // Clears the cache completely
    clear: async function () {
        this._inMemoryCache.clear();
        if (this.isSupported()) {
            await caches.delete(this.CACHE_NAME);
        }
    }
};

// Initialize cache eviction
window.bluesLabCache.init();

// Auto-preload critical startup assets immediately while Blazor WASM engine is downloading & compiling
try {
    const lang = localStorage.getItem('blueslab_locale') || 'en';
    const qPair = new URLSearchParams(window.location.search).get('pair');
    const pairId = qPair || localStorage.getItem('blueslab_last_pair_id') || '10126100000';

    window.bluesLabCache.preload(`locales/common_${lang}.json`);
    window.bluesLabCache.preload('data/themes_database.json');
    window.bluesLabCache.preload(`data/pairs/${pairId}.json`);

    // Warm secondary assets right after initial batch
    setTimeout(() => {
        window.bluesLabCache.preload('data/damage_rules.json');
        window.bluesLabCache.preload('data/pairs_manifest.json');
    }, 120);
} catch (e) {
    console.warn('[BluesLab Cache] Startup preload warning:', e);
}
