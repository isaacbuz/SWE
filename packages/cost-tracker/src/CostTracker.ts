/**
 * Cost Tracking Service
 * 
 * Tracks and calculates costs for LLM provider usage, tool execution, and infrastructure.
 */
import { PrometheusMetrics } from '@ai-company/observability';

/**
 * Cost Entry
 */
export interface CostEntry {
  timestamp: Date;
  service: string;
  provider?: string;
  model?: string;
  operation: string;
  costUSD: number;
  metadata?: Record<string, any>;
}

/**
 * Cost Summary
 */
export interface CostSummary {
  totalCost: number;
  period: {
    start: Date;
    end: Date;
  };
  byService: Record<string, number>;
  byProvider: Record<string, number>;
  byModel: Record<string, number>;
  count: number;
}

/**
 * LLM Provider Pricing
 */
export interface LLMProviderPricing {
  [model: string]: {
    promptPricePer1kTokens: number;
    completionPricePer1kTokens: number;
  };
}

/**
 * Default LLM Provider Pricing (per 1K tokens)
 */
const DEFAULT_PRICING: Record<string, LLMProviderPricing> = {
  openai: {
    'gpt-4': {
      promptPricePer1kTokens: 0.03,
      completionPricePer1kTokens: 0.06,
    },
    'gpt-4-turbo': {
      promptPricePer1kTokens: 0.01,
      completionPricePer1kTokens: 0.03,
    },
    'gpt-3.5-turbo': {
      promptPricePer1kTokens: 0.0015,
      completionPricePer1kTokens: 0.002,
    },
  },
  anthropic: {
    'claude-3-opus': {
      promptPricePer1kTokens: 0.015,
      completionPricePer1kTokens: 0.075,
    },
    'claude-3-sonnet': {
      promptPricePer1kTokens: 0.003,
      completionPricePer1kTokens: 0.015,
    },
    'claude-3-haiku': {
      promptPricePer1kTokens: 0.00025,
      completionPricePer1kTokens: 0.00125,
    },
  },
  google: {
    'gemini-pro': {
      promptPricePer1kTokens: 0.0005,
      completionPricePer1kTokens: 0.0015,
    },
    'gemini-ultra': {
      promptPricePer1kTokens: 0.0025,
      completionPricePer1kTokens: 0.01,
    },
  },
  mistral: {
    'mistral-large': {
      promptPricePer1kTokens: 0.002,
      completionPricePer1kTokens: 0.006,
    },
    'mistral-medium': {
      promptPricePer1kTokens: 0.0007,
      completionPricePer1kTokens: 0.0021,
    },
    'mistral-small': {
      promptPricePer1kTokens: 0.0002,
      completionPricePer1kTokens: 0.0006,
    },
  },
  cohere: {
    'command': {
      promptPricePer1kTokens: 0.0015,
      completionPricePer1kTokens: 0.002,
    },
    'command-light': {
      promptPricePer1kTokens: 0.0003,
      completionPricePer1kTokens: 0.0006,
    },
  },
  ibm: {
    'granite-13b-chat': {
      promptPricePer1kTokens: 0.0005,
      completionPricePer1kTokens: 0.0005,
    },
    'granite-8b-chat': {
      promptPricePer1kTokens: 0.0003,
      completionPricePer1kTokens: 0.0003,
    },
  },
};

/**
 * Cost Tracker
 */
export class CostTracker {
  private costs: CostEntry[] = [];
  private pricing: Record<string, LLMProviderPricing>;
  private metrics?: PrometheusMetrics;

  constructor(
    customPricing?: Record<string, LLMProviderPricing>,
    metrics?: PrometheusMetrics
  ) {
    this.pricing = { ...DEFAULT_PRICING, ...customPricing };
    this.metrics = metrics;
  }

  /**
   * Calculate LLM provider cost
   */
  calculateLLMCost(
    provider: string,
    model: string,
    promptTokens: number,
    completionTokens: number
  ): number {
    const providerPricing = this.pricing[provider.toLowerCase()];
    if (!providerPricing) {
      console.warn(`Unknown provider pricing: ${provider}`);
      return 0;
    }

    const modelPricing = providerPricing[model.toLowerCase()];
    if (!modelPricing) {
      console.warn(`Unknown model pricing: ${provider}/${model}`);
      return 0;
    }

    const promptCost = (promptTokens / 1000) * modelPricing.promptPricePer1kTokens;
    const completionCost = (completionTokens / 1000) * modelPricing.completionPricePer1kTokens;

    return promptCost + completionCost;
  }

  /**
   * Record LLM provider cost
   */
  recordLLMCost(
    provider: string,
    model: string,
    promptTokens: number,
    completionTokens: number,
    metadata?: Record<string, any>
  ): CostEntry {
    const cost = this.calculateLLMCost(provider, model, promptTokens, completionTokens);
    
    const entry: CostEntry = {
      timestamp: new Date(),
      service: 'llm-provider',
      provider,
      model,
      operation: 'completion',
      costUSD: cost,
      metadata: {
        promptTokens,
        completionTokens,
        ...metadata,
      },
    };

    this.costs.push(entry);

    // Record in Prometheus metrics if available
    if (this.metrics) {
      this.metrics.recordLLMRequest(
        provider,
        model,
        'success',
        0, // latency not available here
        promptTokens,
        completionTokens,
        cost
      );
    }

    return entry;
  }

  /**
   * Record tool execution cost
   */
  recordToolCost(
    toolName: string,
    costUSD: number,
    metadata?: Record<string, any>
  ): CostEntry {
    const entry: CostEntry = {
      timestamp: new Date(),
      service: 'tool-execution',
      operation: toolName,
      costUSD,
      metadata,
    };

    this.costs.push(entry);
    return entry;
  }

  /**
   * Record infrastructure cost
   */
  recordInfrastructureCost(
    service: string,
    costUSD: number,
    metadata?: Record<string, any>
  ): CostEntry {
    const entry: CostEntry = {
      timestamp: new Date(),
      service,
      operation: 'infrastructure',
      costUSD,
      metadata,
    };

    this.costs.push(entry);
    return entry;
  }

  /**
   * Get cost summary for a period
   */
  getCostSummary(startDate: Date, endDate: Date): CostSummary {
    const filtered = this.costs.filter(
      (entry) => entry.timestamp >= startDate && entry.timestamp <= endDate
    );

    const totalCost = filtered.reduce((sum, entry) => sum + entry.costUSD, 0);

    const byService: Record<string, number> = {};
    const byProvider: Record<string, number> = {};
    const byModel: Record<string, number> = {};

    filtered.forEach((entry) => {
      byService[entry.service] = (byService[entry.service] || 0) + entry.costUSD;
      
      if (entry.provider) {
        byProvider[entry.provider] = (byProvider[entry.provider] || 0) + entry.costUSD;
      }
      
      if (entry.model) {
        byModel[entry.model] = (byModel[entry.model] || 0) + entry.costUSD;
      }
    });

    return {
      totalCost,
      period: { start: startDate, end: endDate },
      byService,
      byProvider,
      byModel,
      count: filtered.length,
    };
  }

  /**
   * Get all costs
   */
  getAllCosts(): CostEntry[] {
    return [...this.costs];
  }

  /**
   * Clear costs (useful for testing)
   */
  clear(): void {
    this.costs = [];
  }

  /**
   * Get current pricing
   */
  getPricing(): Record<string, LLMProviderPricing> {
    return { ...this.pricing };
  }

  /**
   * Update pricing
   */
  updatePricing(provider: string, pricing: LLMProviderPricing): void {
    this.pricing[provider.toLowerCase()] = pricing;
  }
}

/**
 * Create cost tracker instance
 */
export function createCostTracker(
  customPricing?: Record<string, LLMProviderPricing>,
  metrics?: PrometheusMetrics
): CostTracker {
  return new CostTracker(customPricing, metrics);
}

