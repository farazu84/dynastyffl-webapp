class APICache {
    constructor(ttl = 30000) { // 30 seconds default TTL
        this.cache = new Map();
        this.ttl = ttl; // Time to live in milliseconds
    }

    // Generate cache key from URL and params
    getCacheKey(url, params = {}) {
        const paramString = Object.keys(params).length > 0 
            ? '?' + new URLSearchParams(params).toString() 
            : '';
        return url + paramString;
    }

    get(url, params = {}) {
        const key = this.getCacheKey(url, params);
        const cached = this.cache.get(key);
        
        if (!cached) return null;
        
        if (Date.now() - cached.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }
        
        return cached.data;
    }

    set(url, data, params = {}) {
        const key = this.getCacheKey(url, params);
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    // Clear cache
    clear() {
        this.cache.clear();
    }

    // Get cache stats
    getStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys())
        };
    }
}

export const apiCache = new APICache(30000);

export const cachedFetch = async (url, options = {}) => {
    const method = options.method || 'GET';
    
    if (method.toUpperCase() !== 'GET') {
        return fetch(url, options);
    }
    
    // Check cache first
    const cached = apiCache.get(url);
    if (cached) {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(cached)
        });
    }
    
    try {
        const response = await fetch(url, options);
        
        if (response.ok) {
            const data = await response.json();
            apiCache.set(url, data);
            
            // Return new response object with cached data
            return {
                ok: true,
                json: () => Promise.resolve(data)
            };
        }
        
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
};

export default apiCache;
