import { CostQuota, QuotaResult, UsageStats } from "./types";

interface CostEntry {
  daily: number;
  monthly: number;
  dailyResetAt: Date;
  monthlyResetAt: Date;
}

export class CostQuotaTracker {
  private storage: Map<string, CostEntry> = new Map();
  private quotas: Map<string, CostQuota>;

  constructor(quotas: Map<string, CostQuota>) {
    this.quotas = quotas;
  }

  async checkQuota(userId: string, estimatedCost: number): Promise<QuotaResult> {
    const now = new Date();
    const quota = this.quotas.get(userId) || this.quotas.get("default");

    if (!quota) {
      return {
        allowed: false,
        currentSpend: 0,
        quota: 0,
        remaining: 0,
        resetAt: now,
      };
    }

    const entry = this.getOrCreateEntry(userId, now);

    // Check daily quota
    if (entry.daily + estimatedCost > quota.maxCostPerDay) {
      return {
        allowed: false,
        currentSpend: entry.daily,
        quota: quota.maxCostPerDay,
        remaining: quota.maxCostPerDay - entry.daily,
        resetAt: entry.dailyResetAt,
      };
    }

    // Check monthly quota
    if (entry.monthly + estimatedCost > quota.maxCostPerMonth) {
      return {
        allowed: false,
        currentSpend: entry.monthly,
        quota: quota.maxCostPerMonth,
        remaining: quota.maxCostPerMonth - entry.monthly,
        resetAt: entry.monthlyResetAt,
      };
    }

    return {
      allowed: true,
      currentSpend: entry.daily,
      quota: quota.maxCostPerDay,
      remaining: quota.maxCostPerDay - entry.daily - estimatedCost,
      resetAt: entry.dailyResetAt,
    };
  }

  async trackCost(userId: string, actualCost: number): Promise<void> {
    const now = new Date();
    const entry = this.getOrCreateEntry(userId, now);
    
    entry.daily += actualCost;
    entry.monthly += actualCost;
  }

  async resetQuota(userId: string, period: "day" | "month"): Promise<void> {
    const entry = this.storage.get(userId);
    if (!entry) return;

    const now = new Date();
    if (period === "day") {
      entry.daily = 0;
      entry.dailyResetAt = this.getNextDayReset(now);
    } else {
      entry.monthly = 0;
      entry.monthlyResetAt = this.getNextMonthReset(now);
    }
  }

  async getUsage(userId: string): Promise<UsageStats> {
    const quota = this.quotas.get(userId) || this.quotas.get("default");
    const entry = this.storage.get(userId);

    if (!entry || !quota) {
      return {
        requestsToday: 0,
        requestsThisMonth: 0,
        costToday: 0,
        costThisMonth: 0,
        quotaDaily: quota?.maxCostPerDay || 0,
        quotaMonthly: quota?.maxCostPerMonth || 0,
      };
    }

    return {
      requestsToday: 0, // Would need to track separately
      requestsThisMonth: 0,
      costToday: entry.daily,
      costThisMonth: entry.monthly,
      quotaDaily: quota.maxCostPerDay,
      quotaMonthly: quota.maxCostPerMonth,
    };
  }

  private getOrCreateEntry(userId: string, now: Date): CostEntry {
    let entry = this.storage.get(userId);

    if (!entry) {
      entry = {
        daily: 0,
        monthly: 0,
        dailyResetAt: this.getNextDayReset(now),
        monthlyResetAt: this.getNextMonthReset(now),
      };
      this.storage.set(userId, entry);
    }

    // Reset if needed
    if (now >= entry.dailyResetAt) {
      entry.daily = 0;
      entry.dailyResetAt = this.getNextDayReset(now);
    }
    if (now >= entry.monthlyResetAt) {
      entry.monthly = 0;
      entry.monthlyResetAt = this.getNextMonthReset(now);
    }

    return entry;
  }

  private getNextDayReset(now: Date): Date {
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    return tomorrow;
  }

  private getNextMonthReset(now: Date): Date {
    const nextMonth = new Date(now);
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    nextMonth.setDate(1);
    nextMonth.setHours(0, 0, 0, 0);
    return nextMonth;
  }
}
