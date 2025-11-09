import { TaskType } from '@ai-company/moe-router';

/**
 * Provider execution metric
 */
export interface ProviderExecutionMetric {
  providerId: string;
  taskType: TaskType;
  tokensIn: number;
  tokensOut: number;
  cost: number;
  latencyMs: number;
  success: boolean;
  toolCallsCount: number;
  errorType?: string;
  timestamp: Date;
}

/**
 * Provider statistics
 */
export interface ProviderStats {
  totalRequests: number;
  successRate: number;
  avgLatencyMs: number;
  p50LatencyMs: number;
  p95LatencyMs: number;
  p99LatencyMs: number;
  totalCost: number;
  avgCostPerRequest: number;
  totalTokensIn: number;
  totalTokensOut: number;
}

/**
 * Provider metrics collector
 */
export class ProviderMetricsCollector {
  private metrics: ProviderExecutionMetric[] = [];
  private readonly maxMetrics = 10000;

  /**
   * Record an execution metric
   */
  recordExecution(metric: Omit<ProviderExecutionMetric, 'timestamp'>): void {
    this.metrics.push({
      ...metric,
      timestamp: new Date(),
    });

    // Keep only last N metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }
  }

  /**
   * Get provider statistics
   */
  getProviderStats(
    providerId: string,
    timeRange?: { start: Date; end: Date }
  ): ProviderStats {
    let relevantMetrics = this.metrics.filter((m) => m.providerId === providerId);

    if (timeRange) {
      relevantMetrics = relevantMetrics.filter(
        (m) => m.timestamp >= timeRange.start && m.timestamp <= timeRange.end
      );
    }

    if (relevantMetrics.length === 0) {
      return {
        totalRequests: 0,
        successRate: 0,
        avgLatencyMs: 0,
        p50LatencyMs: 0,
        p95LatencyMs: 0,
        p99LatencyMs: 0,
        totalCost: 0,
        avgCostPerRequest: 0,
        totalTokensIn: 0,
        totalTokensOut: 0,
      };
    }

    const successful = relevantMetrics.filter((m) => m.success);
    const latencies = successful.map((m) => m.latencyMs).sort((a, b) => a - b);
    const costs = relevantMetrics.map((m) => m.cost);

    return {
      totalRequests: relevantMetrics.length,
      successRate: successful.length / relevantMetrics.length,
      avgLatencyMs: latencies.reduce((a, b) => a + b, 0) / latencies.length,
      p50LatencyMs: this.percentile(latencies, 0.5),
      p95LatencyMs: this.percentile(latencies, 0.95),
      p99LatencyMs: this.percentile(latencies, 0.99),
      totalCost: costs.reduce((a, b) => a + b, 0),
      avgCostPerRequest: costs.reduce((a, b) => a + b, 0) / costs.length,
      totalTokensIn: relevantMetrics.reduce((sum, m) => sum + m.tokensIn, 0),
      totalTokensOut: relevantMetrics.reduce((sum, m) => sum + m.tokensOut, 0),
    };
  }

  /**
   * Get win rates by task type
   */
  getWinRates(taskType: TaskType): Map<string, number> {
    const taskMetrics = this.metrics.filter((m) => m.taskType === taskType);
    const providerStats = new Map<string, { success: number; total: number }>();

    for (const metric of taskMetrics) {
      const stats = providerStats.get(metric.providerId) || { success: 0, total: 0 };
      stats.total++;
      if (metric.success) {
        stats.success++;
      }
      providerStats.set(metric.providerId, stats);
    }

    const winRates = new Map<string, number>();
    for (const [providerId, stats] of providerStats) {
      winRates.set(providerId, stats.success / stats.total);
    }

    return winRates;
  }

  /**
   * Get cost analysis
   */
  getCostAnalysis(timeRange?: { start: Date; end: Date }) {
    let relevantMetrics = this.metrics;

    if (timeRange) {
      relevantMetrics = relevantMetrics.filter(
        (m) => m.timestamp >= timeRange.start && m.timestamp <= timeRange.end
      );
    }

    const byProvider = new Map<string, number>();
    const byTaskType = new Map<TaskType, number>();

    for (const metric of relevantMetrics) {
      byProvider.set(
        metric.providerId,
        (byProvider.get(metric.providerId) || 0) + metric.cost
      );
      byTaskType.set(
        metric.taskType,
        (byTaskType.get(metric.taskType) || 0) + metric.cost
      );
    }

    return {
      totalCost: Array.from(byProvider.values()).reduce((a, b) => a + b, 0),
      byProvider: Object.fromEntries(byProvider),
      byTaskType: Object.fromEntries(byTaskType),
    };
  }

  /**
   * Export metrics in Prometheus format
   */
  exportPrometheus(): string {
    const lines: string[] = [];

    // Provider stats
    const providers = new Set(this.metrics.map((m) => m.providerId));
    for (const providerId of providers) {
      const stats = this.getProviderStats(providerId);
      lines.push(`# Provider: ${providerId}`);
      lines.push(`provider_requests_total{provider="${providerId}"} ${stats.totalRequests}`);
      lines.push(`provider_success_rate{provider="${providerId}"} ${stats.successRate}`);
      lines.push(`provider_avg_latency_ms{provider="${providerId}"} ${stats.avgLatencyMs}`);
      lines.push(`provider_total_cost{provider="${providerId}"} ${stats.totalCost}`);
    }

    return lines.join('\n');
  }

  /**
   * Calculate percentile
   */
  private percentile(sorted: number[], p: number): number {
    if (sorted.length === 0) return 0;
    const index = Math.ceil(sorted.length * p) - 1;
    return sorted[Math.max(0, Math.min(index, sorted.length - 1))];
  }
}

