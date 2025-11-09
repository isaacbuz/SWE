/**
 * Rate limiter for external APIs
 */

interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
}

interface RateLimitState {
  count: number;
  resetAt: Date;
}

export class RateLimiter {
  private limits: Map<string, RateLimitState> = new Map();
  private configs: Map<string, RateLimitConfig> = new Map();

  /**
   * Set rate limit configuration for a service
   */
  setLimit(service: string, config: RateLimitConfig): void {
    this.configs.set(service, config);
  }

  /**
   * Check if request is within rate limit
   * @throws Error if rate limit exceeded
   */
  async checkLimit(service: string): Promise<void> {
    const config = this.configs.get(service);
    if (!config) {
      return; // No limit configured
    }

    const now = new Date();
    const state = this.limits.get(service);

    if (!state || now >= state.resetAt) {
      // Reset window
      this.limits.set(service, {
        count: 1,
        resetAt: new Date(now.getTime() + config.windowMs),
      });
      return;
    }

    if (state.count >= config.maxRequests) {
      const retryAfter = Math.ceil((state.resetAt.getTime() - now.getTime()) / 1000);
      throw new Error(
        `Rate limit exceeded for ${service}. Retry after ${retryAfter} seconds.`
      );
    }

    // Increment count
    state.count++;
  }

  /**
   * Get current rate limit status
   */
  getStatus(service: string): { remaining: number; resetAt: Date } | null {
    const config = this.configs.get(service);
    const state = this.limits.get(service);

    if (!config || !state) {
      return null;
    }

    return {
      remaining: Math.max(0, config.maxRequests - state.count),
      resetAt: state.resetAt,
    };
  }
}

