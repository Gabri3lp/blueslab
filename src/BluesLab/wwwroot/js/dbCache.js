// Persistent CacheStorage helper for Blues Lab database and locales
window.bluesLabCache = {
    CACHE_NAME: 'blueslab-data-v1',

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

    // Fetches JSON content with Cache-First + Stale-While-Revalidate strategy
    fetchJson: async function (url) {
        const fullUrl = this.resolveUrl(url);

        if (!this.isSupported()) {
            const fallback = await fetch(fullUrl);
            return await fallback.text();
        }

        try {
            const cache = await caches.open(this.CACHE_NAME);
            const cachedResponse = await cache.match(fullUrl);

            if (cachedResponse) {
                // Background revalidation: fetch latest in background and update cache silently
                this.revalidate(cache, fullUrl);
                return await cachedResponse.text();
            }

            // Not in cache, fetch from network and store
            const networkResponse = await fetch(fullUrl);
            if (networkResponse && networkResponse.ok) {
                const text = await networkResponse.text();
                // Ensure it's valid JSON and not an HTML 404 fallback
                if (text.trim().startsWith('<')) {
                    throw new Error('Server returned HTML instead of JSON for ' + fullUrl);
                }

                // Store clone in cache
                try {
                    await cache.put(fullUrl, new Response(text, {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                } catch (e) {
                    // Ignore quota or private mode errors
                }
                return text;
            } else {
                throw new Error('Network response not ok: ' + (networkResponse ? networkResponse.status : 'unknown'));
            }
        } catch (err) {
            console.warn('[BluesLab Cache] Cache fetch failed for', fullUrl, err);
            const fallback = await fetch(fullUrl);
            return await fallback.text();
        }
    },

    // Silent background revalidation
    revalidate: function (cache, fullUrl) {
        setTimeout(async () => {
            try {
                const res = await fetch(fullUrl, { cache: 'no-cache' });
                if (res && res.ok) {
                    const text = await res.text();
                    if (!text.trim().startsWith('<')) {
                        await cache.put(fullUrl, new Response(text, {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        }));
                    }
                }
            } catch (e) {
                // Silent fail for background revalidation
            }
        }, 200);
    },

    // Clears the cache if needed
    clear: async function () {
        if (this.isSupported()) {
            await caches.delete(this.CACHE_NAME);
        }
    }
};
