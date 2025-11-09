/**
 * Enhanced Rate Limiter with User Limits and Cost Quotas
 * 
 * Implements rate limiting and cost quotas for tool execution.
 * Supports per-user, per-tool, and global limits.
 */

export interface RateLimit {
  /** Maximum requests */
  maxRequests: number;
  
  /** Time window in milliseconds */
  windowMs: number;
  
  /** Scope: user, tool, or global */
  per: "user" | "tool" | "global";
}

export interface CostQuota {
  /** Maximum cost per day */
  maxCostPerDay: number;
  
  /** Maximum cost per month */
  maxCostPerMonth: number;
  
  /** User ID (optional, for per-user quotas) */
  userId?: string;
  
  /** Team ID (optional, for per-team quotas) */
  teamId?: string;
}

export interface RateLimitResult {
  allowed: boolean;
  message?: string;
  remaining?: number;
  resetAt?: Date;
  retryAfter?: number; // seconds
}

export interface QuotaResult {
  allowed: boolean;
  currentSpend: number;
  quota: number;
  remaining: number;
  resetAt: Date;
}

export interface UsageStats {
  requestsToday: number;
  requestsThisMonth: number;
  costToday: number;
  costThisMonth: number;
  quotaDaily: number;
  quotaMonthly: number;
}

export interface RateLimitStorage {
  /** Get current count for a key */
  getCount(key: string): Promise<number>;
  
  /** Increment count for a key */
  increment(key: string, ttl: number): Promise<number>;
  
  /** Get cost for a period */
  getCost(key: string): Promise<number>;
  
  /** Add cost for a period */
  addCost(key: string, cost: number, ttl: number): Promise<number>;
  
  /** Reset counter/cost */
  reset(key: string): Promise<void>;
}

/**
 * In-memory storage implementation (for testing/single-instance)
 * In production, use Redis or similar
 */
export class InMemoryRateLimitStorage implements RateLimitStorage {
  private counters: Map<string, { count: number; expiresAt: number }> = new Map();
  private costs: Map<string, { cost: number; expiresAt: number }> = new Map();

  async getCount(key: string): Promise<number> {
    const entry = this.counters.get(key);
    if (!entry) {
      return 0;
    }

    if (Date.now() > entry.expiresAt) {
      this.counters.delete(key);
      return 0;
    }

    return entry.count;
  }

  async increment(key: string, ttl: number): Promise<number> {
    const entry = this.counters.get(key);
    const now = Date.now();
    const expiresAt = now + ttl;

    if (!entry || now > entry.expiresAt) {
      this.counters.set(key, { count: 1, expiresAt });
      return 1;
    }

    entry.count += 1;
    return entry.count;
  }

  async getCost(key: string): Promise<number> {
    const entry = this.costs.get(key);
    if (!entry) {
      return 0;
    }

    if (Date.now() > entry.expiresAt) {
      this.costs.delete(key);
      return 0;
    }

    return entry.cost;
  }

  async addCost(key: string, cost: number, ttl: number): Promise<number> {
    const entry = this.costs.get(key);
    const now = Date.now();
    const expiresAt = now + ttl;

    if (!entry || now > entry.expiresAt) {
      this.costs.set(key, { cost, expiresAt });
      return cost;
    }

    entry.cost += cost;
    return entry.cost;
  }

  async reset(key: string): Promise<void> {
    this.counters.delete(key);
    this.costs.delete(key);
  }
}

export class EnhancedRateLimiter {
  private limits: Map<string, RateLimit> = new Map();
  private quotas: Map<string, CostQuota> = new Map();
  private storage: RateLimitStorage;

  constructor(storage?: RateLimitStorage) {
    this.storage = storage || new InMemoryRateLimitStorage();
    this.loadDefaultLimits();
  }

  /**
   * Load default rate limits
   */
  private loadDefaultLimits(): void {
    // Per-user limits
    this.setLimit("user", {
      maxRequests: 1000,
      windowMs: 60 * 60 * 1000, // 1 hour
      per: "user",
    });

    // Per-tool limits
    this.setLimit("github/createIssues", {
      maxRequests: 100,
      windowMs: 60 * 60 * 1000, // 100/hour
      per: "tool",
    });

    this.setLimit("github/createPR", {
      maxRequests: 50,
      windowMs: 60 * 60 * 1000, // 50/hour
      per: "tool",
    });

    this.setLimit("gsa/searchEntities", {
      maxRequests: 200,
      windowMs: 60 * 60 * 1000, // 200/hour
      per: "tool",
    });

    // Global limits
    this.setLimit("global", {
      maxRequests: 10000,
      windowMs: 60 * 60 * 1000, // 10k/hour total
      per: "global",
    });
  }

  /**
   * Set rate limit
   */
  setLimit(key: string, limit: RateLimit): void {
    this.limits.set(key, limit);
  }

  /**
   * Set cost quota
   */
  setQuota(key: string, quota: CostQuota): void {
    this.quotas.set(key, quota);
  }

  /**
   * Check rate limit
   */
  async checkLimit(
    userId: string,
    toolName: string
  ): Promise<RateLimitResult> {
    const now = Date.now();
    const results: RateLimitResult[] = [];

    // Check per-user limit
    const userLimit = this.limits.get("user");
    if (userLimit) {
      const key = `rate_limit:user:${userId}`;
      const count = await this.storage.getCount(key);
      
      if (count >= userLimit.maxRequests) {
        const resetAt = new Date(now + userLimit.windowMs);
        return {
          allowed: false,
          message: `User rate limit exceeded. Max ${userLimit.maxRequests} requests per hour`,
          remaining: 0,
          resetAt,
          retryAfter: Math.ceil(userLimit.windowMs / 1000),
        };
      }

      await this.storage.increment(key, userLimit.windowMs);
      results.push({
        allowed: true,
        remaining: userLimit.maxRequests - count - 1,
        resetAt: new Date(now + userLimit.windowMs),
      });
    }

    // Check per-tool limit
    const toolLimit = this.limits.get(toolName);
    if (toolLimit) {
      const key = `rate_limit:tool:${toolName}`;
      const count = await this.storage.getCount(key);
      
      if (count >= toolLimit.maxRequests) {
        const resetAt = new Date(now + toolLimit.windowMs);
        return {
          allowed: false,
          message: `Tool rate limit exceeded for '${toolName}'. Max ${toolLimit.maxRequests} requests per hour`,
          remaining: 0,
          resetAt,
          retryAfter: Math.ceil(toolLimit.windowMs / 1000),
        };
      }

      await this.storage.increment(key, toolLimit.windowMs);
    }

    // Check global limit
    const globalLimit = this.limits.get("global");
    if (globalLimit) {
      const key = `rate_limit:global`;
      const count = await this.storage.getCount(key);
      
      if (count >= globalLimit.maxRequests) {
        const resetAt = new Date(now + globalLimit.windowMs);
        return {
          allowed: false,
          message: `Global rate limit exceeded. Max ${globalLimit.maxRequests} requests per hour`,
          remaining: 0,
          resetAt,
          retryAfter: Math.ceil(globalLimit.windowMs / 1000),
        };
      }

      await this.storage.increment(key, globalLimit.windowMs);
    }

    // All checks passed
    return results[0] || { allowed: true };
  }

  /**
   * Check cost quota
   */
  async checkQuota(
    userId: string,
    estimatedCost: number
  ): Promise<QuotaResult> {
    const now = Date.now();
    const today = new Date(now).toISOString().split("T")[0];
    const month = new Date(now).toISOString().slice(0, 7); // YYYY-MM

    // Get quota (default or user-specific)
    const quotaKey = userId || "default";
    const quota = this.quotas.get(quotaKey) || {
      maxCostPerDay: 10.0,
      maxCostPerMonth: 200.0,
    };

    // Check daily quota
    const dailyKey = `quota:user:${userId}:day:${today}`;
    const dailyCost = await this.storage.getCost(dailyKey);
    const newDailyCost = dailyCost + estimatedCost;

    if (newDailyCost > quota.maxCostPerDay) {
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0);

      return {
        allowed: false,
        currentSpend: dailyCost,
        quota: quota.maxCostPerDay,
        remaining: Math.max(0, quota.maxCostPerDay - dailyCost),
        resetAt: tomorrow,
      };
    }

    // Check monthly quota
    const monthlyKey = `quota:user:${userId}:month:${month}`;
    const monthlyCost = await this.storage.getCost(monthlyKey);
    const newMonthlyCost = monthlyCost + estimatedCost;

    if (newMonthlyCost > quota.maxCostPerMonth) {
      const nextMonth = new Date(now);
      nextMonth.setMonth(nextMonth.getMonth() + 1);
      nextMonth.setDate(1);
      nextMonth.setHours(0, 0, 0, 0);

      return {
        allowed: false,
        currentSpend: monthlyCost,
        quota: quota.maxCostPerMonth,
        remaining: Math.max(0, quota.maxCostPerMonth - monthlyCost),
        resetAt: nextMonth,
      };
    }

    // Record cost
    const dayTTL = 24 * 60 * 60 * 1000; // 24 hours
    const monthTTL = 30 * 24 * 60 * 60 * 1000; // 30 days

    await this.storage.addCost(dailyKey, estimatedCost, dayTTL);
    await this.storage.addCost(monthlyKey, estimatedCost, monthTTL);

    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);

    return {
      allowed: true,
      currentSpend: newDailyCost,
      quota: quota.maxCostPerDay,
      remaining: quota.maxCostPerDay - newDailyCost,
      resetAt: tomorrow,
    };
  }

  /**
   * Reset quota for a period
   */
  async resetQuota(
    userId: string,
    period: "day" | "month"
  ): Promise<void> {
    const now = Date.now();
    
    if (period === "day") {
      const today = new Date(now).toISOString().split("T")[0];
      const key = `quota:user:${userId}:day:${today}`;
      await this.storage.reset(key);
    } else {
      const month = new Date(now).toISOString().slice(0, 7);
      const key = `quota:user:${userId}:month:${month}`;
      await this.storage.reset(key);
    }
  }

  /**
   * Get usage statistics
   */
  async getUsage(userId: string): Promise<UsageStats> {
    const now = Date.now();
    const today = new Date(now).toISOString().split("T")[0];
    const month = new Date(now).toISOString().slice(0, 7);

    const quotaKey = userId || "default";
    const quota = this.quotas.get(quotaKey) || {
      maxCostPerDay: 10.0,
      maxCostPerMonth: 200.0,
    };

    const dailyKey = `quota:user:${userId}:day:${today}`;
    const monthlyKey = `quota:user:${userId}:month:${month}`;

    const costToday = await this.storage.getCost(dailyKey);
    const costThisMonth = await this.storage.getCost(monthlyKey);

    // Get request counts (simplified - would need separate tracking)
    const requestsToday = await this.storage.getCount(`requests:user:${userId}:day:${today}`);
    const requestsThisMonth = await this.storage.getCount(`requests:user:${userId}:month:${month}`);

    return {
      requestsToday,
      requestsThisMonth,
      costToday,
      costThisMonth,
      quotaDaily: quota.maxCostPerDay,
      quotaMonthly: quota.maxCostPerMonth,
    };
  }
}

