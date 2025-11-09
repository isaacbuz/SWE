import { QuotaConfig, QuotaStatus } from './types';

/**
 * Quota state
 */
interface QuotaState {
  cost: number;
  resetAt: Date;
}

/**
 * Quota Manager
 * 
 * Manages cost quotas per identifier (user, team, etc.)
 * with periodic reset.
 */
export class QuotaManager {
  private quotas: Map<string, QuotaState> = new Map();

  /**
   * Check if cost is within quota
   */
  checkQuota(config: QuotaConfig, cost: number): QuotaStatus {
    const key = this.getKey(config);
    const now = new Date();
    const state = this.quotas.get(key);

    if (!state || now >= state.resetAt) {
      // Reset period
      const resetAt = new Date(now.getTime() + config.periodMs);
      this.quotas.set(key, {
        cost,
        resetAt,
      });

      return {
        exceeded: cost > config.maxCost,
        remaining: Math.max(0, config.maxCost - cost),
        resetAt,
        current: cost,
      };
    }

    // Add to existing cost
    state.cost += cost;

    return {
      exceeded: state.cost > config.maxCost,
      remaining: Math.max(0, config.maxCost - state.cost),
      resetAt: state.resetAt,
      current: state.cost,
    };
  }

  /**
   * Get quota status
   */
  getStatus(config: QuotaConfig): QuotaStatus {
    const key = this.getKey(config);
    const now = new Date();
    const state = this.quotas.get(key);

    if (!state || now >= state.resetAt) {
      return {
        exceeded: false,
        remaining: config.maxCost,
        resetAt: new Date(now.getTime() + config.periodMs),
        current: 0,
      };
    }

    return {
      exceeded: state.cost >= config.maxCost,
      remaining: Math.max(0, config.maxCost - state.cost),
      resetAt: state.resetAt,
      current: state.cost,
    };
  }

  /**
   * Reset quota for identifier
   */
  reset(config: QuotaConfig): void {
    const key = this.getKey(config);
    this.quotas.delete(key);
  }

  /**
   * Get storage key
   */
  private getKey(config: QuotaConfig): string {
    return `${config.identifier}:${config.periodMs}`;
  }
}

