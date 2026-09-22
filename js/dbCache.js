// Persistent CacheStorage helper for Blues Lab database and locales
window.bluesLabCache = {
    CACHE_NAME: 'blueslab-data-v1',

    // Checks if CacheStorage API is available
    isSupported: function () {
        return typeof window !== 'undefined' && 'caches' in window;
    },

    // Fetches JSON content with Cache-First + Stale-While-Revalidate strategy
    fetchJson: async function (url) {
        if (!this.isSupported()) {
            const fallback = await fetch(url);
            return await fallback.text();
        }

        try {
            const cache = await caches.open(this.CACHE_NAME);
            const cachedResponse = await cache.match(url);

            if (cachedResponse) {
                // Background revalidation: fetch latest in background and update cache silently
                this.revalidate(cache, url);
                return await cachedResponse.text();
            }

            // Not in cache, fetch from network and store
            const networkResponse = await fetch(url);
            if (networkResponse && networkResponse.ok) {
                const text = await networkResponse.text();
                // Store clone in cache
                try {
                    await cache.put(url, new Response(text, {
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
            console.warn('[BluesLab Cache] Cache fetch failed for', url, err);
            const fallback = await fetch(url);
            return await fallback.text();
        }
    },

    // Silent background revalidation
    revalidate: function (cache, url) {
        setTimeout(async () => {
            try {
                const res = await fetch(url, { cache: 'no-cache' });
                if (res && res.ok) {
                    const text = await res.text();
                    await cache.put(url, new Response(text, {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                }
            } catch (e) {
                // Silent fail for background revalidation (e.g. offline)
            }
        }, 100);
    },

    // Clears the cache if needed
    clear: async function () {
        if (this.isSupported()) {
            await caches.delete(this.CACHE_NAME);
        }
    }
};
