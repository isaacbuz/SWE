import { RateLimit, RateLimitResult, RateLimitConfig } from "./types";

interface RateLimitEntry {
  count: number;
  resetAt: Date;
}

export class RateLimiter {
  private storage: Map<string, RateLimitEntry> = new Map();
  private config: RateLimitConfig;

  constructor(config: RateLimitConfig) {
    this.config = config;
  }

  async checkLimit(userId: string, toolName: string): Promise<RateLimitResult> {
    const now = new Date();

    // Check user limit
    const userKey = `user:${userId}`;
    const userResult = this.checkSingleLimit(userKey, this.config.userLimit, now);
    if (!userResult.allowed) {
      return userResult;
    }

    // Check tool-specific limit
    const toolLimit = this.config.toolLimits.get(toolName);
    if (toolLimit) {
      const toolKey = `tool:${toolName}:${userId}`;
      const toolResult = this.checkSingleLimit(toolKey, toolLimit, now);
      if (!toolResult.allowed) {
        return toolResult;
      }
    }

    // Check global limit
    const globalKey = `global`;
    const globalResult = this.checkSingleLimit(globalKey, this.config.globalLimit, now);
    if (!globalResult.allowed) {
      return globalResult;
    }

    // Increment counters
    this.incrementCounter(userKey, this.config.userLimit, now);
    if (toolLimit) {
      const toolKey = `tool:${toolName}:${userId}`;
      this.incrementCounter(toolKey, toolLimit, now);
    }
    this.incrementCounter(globalKey, this.config.globalLimit, now);

    return userResult;
  }

  private checkSingleLimit(key: string, limit: RateLimit, now: Date): RateLimitResult {
    const entry = this.storage.get(key);
    
    if (!entry || now >= entry.resetAt) {
      // Reset window
      const resetAt = new Date(now.getTime() + limit.windowMs);
      return {
        allowed: true,
        remaining: limit.maxRequests - 1,
        resetAt,
      };
    }

    if (entry.count >= limit.maxRequests) {
      const retryAfter = Math.ceil((entry.resetAt.getTime() - now.getTime()) / 1000);
      return {
        allowed: false,
        remaining: 0,
        resetAt: entry.resetAt,
        retryAfter,
      };
    }

    return {
      allowed: true,
      remaining: limit.maxRequests - entry.count - 1,
      resetAt: entry.resetAt,
    };
  }

  private incrementCounter(key: string, limit: RateLimit, now: Date): void {
    const entry = this.storage.get(key);
    
    if (!entry || now >= entry.resetAt) {
      this.storage.set(key, {
        count: 1,
        resetAt: new Date(now.getTime() + limit.windowMs),
      });
    } else {
      entry.count++;
    }
  }

  async getUsage(userId: string): Promise<{ requests: number; resetAt: Date }> {
    const key = `user:${userId}`;
    const entry = this.storage.get(key);
    
    if (!entry) {
      return { requests: 0, resetAt: new Date() };
    }

    return {
      requests: entry.count,
      resetAt: entry.resetAt,
    };
  }
}
