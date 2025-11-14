/**
 * Simple in-memory cache for API data
 * Prevents unnecessary reloads when navigating between pages
 */

const cache = {
  trips: null,
  vehicles: null,
  drivers: null,
  stops: null,
  paths: null,
  routes: null,
  deployments: null,
  cacheTime: 5 * 60 * 1000, // 5 minutes
  timestamps: {}
}

export const dataCache = {
  get: (key) => {
    const cached = cache[key]
    const timestamp = cache.timestamps[key]
    
    if (!cached || !timestamp) {
      return null
    }
    
    // Check if cache is stale
    const age = Date.now() - timestamp
    if (age > cache.cacheTime) {
      cache[key] = null
      cache.timestamps[key] = null
      return null
    }
    
    return cached
  },
  
  set: (key, data) => {
    cache[key] = data
    cache.timestamps[key] = Date.now()
  },
  
  clear: (key) => {
    if (key) {
      cache[key] = null
      cache.timestamps[key] = null
    } else {
      // Clear all
      Object.keys(cache).forEach(k => {
        if (k !== 'cacheTime' && k !== 'timestamps') {
          cache[k] = null
          cache.timestamps[k] = null
        }
      })
    }
  },
  
  clearAll: () => {
    Object.keys(cache).forEach(k => {
      if (k !== 'cacheTime' && k !== 'timestamps') {
        cache[k] = null
        cache.timestamps[k] = null
      }
    })
  }
}

