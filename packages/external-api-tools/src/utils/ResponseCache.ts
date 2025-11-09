/**
 * Response Cache
 * 
 * Caches API responses to reduce external API calls.
 */

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class ResponseCache {
  private cache: Map<string, CacheEntry<unknown>> = new Map();
  private defaultTTL: number;

  constructor(defaultTTL: number = 300000) {
    // Default TTL: 5 minutes
    this.defaultTTL = defaultTTL;
  }

  /**
   * Generate cache key from URL and parameters
   */
  private generateKey(url: string, params?: Record<string, unknown>): string {
    const paramStr = params
      ? Object.entries(params)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
          .join("&")
      : "";
    return `${url}?${paramStr}`;
  }

  /**
   * Get cached response
   */
  get<T>(url: string, params?: Record<string, unknown>): T | undefined {
    const key = this.generateKey(url, params);
    const entry = this.cache.get(key);

    if (!entry) {
      return undefined;
    }

    // Check if expired
    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return undefined;
    }

    return entry.data as T;
  }

  /**
   * Set cached response
   */
  set<T>(
    url: string,
    data: T,
    params?: Record<string, unknown>,
    ttl?: number
  ): void {
    const key = this.generateKey(url, params);
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
    };

    this.cache.set(key, entry as CacheEntry<unknown>);
  }

  /**
   * Clear cache for a specific URL pattern
   */
  clear(urlPattern?: string): void {
    if (!urlPattern) {
      this.cache.clear();
      return;
    }

    for (const key of this.cache.keys()) {
      if (key.includes(urlPattern)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Clear expired entries
   */
  cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    size: number;
    entries: Array<{ key: string; age: number; ttl: number }>;
  } {
    const now = Date.now();
    return {
      size: this.cache.size,
      entries: Array.from(this.cache.entries()).map(([key, entry]) => ({
        key,
        age: now - entry.timestamp,
        ttl: entry.ttl,
      })),
    };
  }
}

