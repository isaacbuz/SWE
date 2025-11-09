/**
 * Rate Limiter
 *
 * Implements token bucket rate limiting for tool execution.
 */

export interface RateLimitResult {
  allowed: boolean;
  message?: string;
  remaining?: number;
  resetAt?: number;
}

export interface RateLimitConfig {
  /** Maximum requests per window */
  maxRequests: number;

  /** Time window in milliseconds */
  windowMs: number;
}

export class RateLimiter {
  private limits: Map<string, RateLimitConfig> = new Map();
  private buckets: Map<string, { tokens: number; lastRefill: number }> =
    new Map();

  /**
   * Set rate limit for a tool
   */
  setLimit(toolName: string, config: RateLimitConfig): void {
    this.limits.set(toolName, config);

    // Initialize bucket if not exists
    if (!this.buckets.has(toolName)) {
      this.buckets.set(toolName, {
        tokens: config.maxRequests,
        lastRefill: Date.now(),
      });
    }
  }

  /**
   * Check if request is allowed
   */
  async checkLimit(toolName: string): Promise<RateLimitResult> {
    const config = this.limits.get(toolName);

    // No limit configured, allow
    if (!config) {
      return { allowed: true };
    }

    const bucket = this.buckets.get(toolName) || {
      tokens: config.maxRequests,
      lastRefill: Date.now(),
    };

    const now = Date.now();
    const timePassed = now - bucket.lastRefill;

    // Refill tokens based on time passed
    const tokensToAdd = Math.floor(
      (timePassed / config.windowMs) * config.maxRequests,
    );
    const newTokens = Math.min(bucket.tokens + tokensToAdd, config.maxRequests);

    // Update bucket
    const updatedBucket = {
      tokens: newTokens,
      lastRefill: now,
    };
    this.buckets.set(toolName, updatedBucket);

    // Check if we have tokens
    if (updatedBucket.tokens >= 1) {
      updatedBucket.tokens -= 1;
      this.buckets.set(toolName, updatedBucket);

      return {
        allowed: true,
        remaining: updatedBucket.tokens,
        resetAt: now + config.windowMs,
      };
    }

    return {
      allowed: false,
      message: `Rate limit exceeded. Max ${config.maxRequests} requests per ${config.windowMs}ms`,
      remaining: 0,
      resetAt: bucket.lastRefill + config.windowMs,
    };
  }

  /**
   * Reset rate limit for a tool
   */
  reset(toolName: string): void {
    const config = this.limits.get(toolName);
    if (config) {
      this.buckets.set(toolName, {
        tokens: config.maxRequests,
        lastRefill: Date.now(),
      });
    }
  }

  /**
   * Clear all rate limits
   */
  clear(): void {
    this.limits.clear();
    this.buckets.clear();
  }
}
