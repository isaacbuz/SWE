import { RateLimitConfig, RateLimitStatus } from './types';

/**
 * Rate limit state
 */
interface RateLimitState {
  count: number;
  resetAt: Date;
}

/**
 * Rate Limiter
 * 
 * Implements rate limiting per identifier (user, IP, tool, etc.)
 * with sliding window algorithm.
 */
export class RateLimiter {
  private limits: Map<string, RateLimitState> = new Map();

  /**
   * Check if request is within rate limit
   */
  checkLimit(config: RateLimitConfig): RateLimitStatus {
    const key = this.getKey(config);
    const now = new Date();
    const state = this.limits.get(key);

    if (!state || now >= state.resetAt) {
      // Reset window
      const resetAt = new Date(now.getTime() + config.windowMs);
      this.limits.set(key, {
        count: 1,
        resetAt,
      });

      return {
        exceeded: false,
        remaining: config.maxRequests - 1,
        resetAt,
        current: 1,
      };
    }

    // Increment count
    state.count++;

    const exceeded = state.count > config.maxRequests;

    return {
      exceeded,
      remaining: Math.max(0, config.maxRequests - state.count),
      resetAt: state.resetAt,
      current: state.count,
    };
  }

  /**
   * Get rate limit status without incrementing
   */
  getStatus(config: RateLimitConfig): RateLimitStatus {
    const key = this.getKey(config);
    const now = new Date();
    const state = this.limits.get(key);

    if (!state || now >= state.resetAt) {
      return {
        exceeded: false,
        remaining: config.maxRequests,
        resetAt: new Date(now.getTime() + config.windowMs),
        current: 0,
      };
    }

    return {
      exceeded: state.count >= config.maxRequests,
      remaining: Math.max(0, config.maxRequests - state.count),
      resetAt: state.resetAt,
      current: state.count,
    };
  }

  /**
   * Reset rate limit for identifier
   */
  reset(config: RateLimitConfig): void {
    const key = this.getKey(config);
    this.limits.delete(key);
  }

  /**
   * Get storage key
   */
  private getKey(config: RateLimitConfig): string {
    return `${config.identifier}:${config.windowMs}`;
  }
}

