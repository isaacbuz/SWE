export interface RateLimit {
  maxRequests: number;
  windowMs: number;
  per: "user" | "tool" | "global";
}

export interface CostQuota {
  maxCostPerDay: number;
  maxCostPerMonth: number;
  userId?: string;
  teamId?: string;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: Date;
  retryAfter?: number;
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

export interface RateLimitConfig {
  userLimit: RateLimit;
  toolLimits: Map<string, RateLimit>;
  globalLimit: RateLimit;
  quotas: Map<string, CostQuota>;
}
