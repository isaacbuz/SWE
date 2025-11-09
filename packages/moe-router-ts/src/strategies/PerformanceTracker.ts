import { LLMProvider } from '@ai-company/llm-providers';
import { TaskType } from '../types';

/**
 * Performance tracking for providers
 */
interface PerformanceMetric {
  providerId: string;
  taskType: TaskType;
  success: boolean;
  latencyMs: number;
  cost: number;
  qualityScore?: number;
  timestamp: Date;
}

/**
 * Performance tracker with time-based decay
 */
export class PerformanceTracker {
  private metrics: PerformanceMetric[] = [];
  private readonly decayFactor = 0.95; // Exponential decay per hour

  /**
   * Record a performance metric
   */
  recordMetric(metric: Omit<PerformanceMetric, 'timestamp'>): void {
    this.metrics.push({
      ...metric,
      timestamp: new Date(),
    });

    // Keep only last 1000 metrics
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }
  }

  /**
   * Get recommendation weight for a provider/task type
   * Returns 0-1, higher is better
   */
  getRecommendationWeight(providerId: string, taskType: TaskType): number {
    const relevantMetrics = this.metrics.filter(
      (m) => m.providerId === providerId && m.taskType === taskType
    );

    if (relevantMetrics.length === 0) {
      return 0.5; // Neutral if no history
    }

    const now = Date.now();
    let weightedSuccess = 0;
    let totalWeight = 0;

    for (const metric of relevantMetrics) {
      const ageHours = (now - metric.timestamp.getTime()) / (1000 * 60 * 60);
      const weight = Math.pow(this.decayFactor, ageHours);

      if (metric.success) {
        weightedSuccess += weight;
      }
      totalWeight += weight;
    }

    return totalWeight > 0 ? weightedSuccess / totalWeight : 0.5;
  }

  /**
   * Get average latency for a provider/task type
   */
  getAverageLatency(providerId: string, taskType: TaskType): number | null {
    const relevantMetrics = this.metrics.filter(
      (m) => m.providerId === providerId && m.taskType === taskType && m.success
    );

    if (relevantMetrics.length === 0) {
      return null;
    }

    const now = Date.now();
    let weightedLatency = 0;
    let totalWeight = 0;

    for (const metric of relevantMetrics) {
      const ageHours = (now - metric.timestamp.getTime()) / (1000 * 60 * 60);
      const weight = Math.pow(this.decayFactor, ageHours);

      weightedLatency += metric.latencyMs * weight;
      totalWeight += weight;
    }

    return totalWeight > 0 ? weightedLatency / totalWeight : null;
  }

  /**
   * Get win rate (success rate) for a provider/task type
   */
  getWinRate(providerId: string, taskType: TaskType): number {
    return this.getRecommendationWeight(providerId, taskType);
  }
}

