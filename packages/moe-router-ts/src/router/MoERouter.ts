import { LLMProvider } from '@ai-company/llm-providers';
import { RoutingRequest, RoutingDecision, RoutingPolicy, ProviderScore, TaskType } from '../types';
import { CostPredictor } from '../strategies/CostPredictor';
import { PerformanceTracker } from '../strategies/PerformanceTracker';

/**
 * MoE Router - Intelligent provider selection
 * 
 * Selects the best LLM provider for each task based on:
 * - Task type and requirements
 * - Cost constraints
 * - Performance history
 * - Quality requirements
 * - Latency requirements
 */
export class MoERouter {
  private providers: Map<string, LLMProvider> = new Map();
  private policies: Map<TaskType, RoutingPolicy> = new Map();
  private costPredictor: CostPredictor;
  private performanceTracker: PerformanceTracker;

  constructor() {
    this.costPredictor = new CostPredictor();
    this.performanceTracker = new PerformanceTracker();
  }

  /**
   * Register a provider
   */
  registerProvider(provider: LLMProvider): void {
    this.providers.set(provider.name, provider);
  }

  /**
   * Set routing policy for a task type
   */
  setPolicy(taskType: TaskType, policy: RoutingPolicy): void {
    this.policies.set(taskType, policy);
  }

  /**
   * Select provider for a request
   */
  selectProvider(request: RoutingRequest): RoutingDecision {
    // Filter available providers
    const availableProviders = this.filterProviders(request);

    if (availableProviders.length === 0) {
      throw new Error('No providers available matching requirements');
    }

    // Score providers
    const scoredProviders = this.scoreProviders(request, availableProviders);

    if (scoredProviders.length === 0) {
      throw new Error('No providers passed scoring');
    }

    // Select top provider
    const topScore = scoredProviders[0];
    const fallbacks = scoredProviders.slice(1, 4).map((s) => s.provider);

    // Build rationale
    const rationale = this.buildRationale(topScore, request);

    return {
      selectedProvider: topScore.provider,
      confidence: Math.min(1.0, topScore.score / 100),
      rationale,
      estimatedCost: this.costPredictor.predictCost(
        topScore.provider,
        request
      ).expectedCost,
      estimatedQuality: this.getQualityScore(topScore.provider),
      fallbackProviders: fallbacks,
      scores: scoredProviders,
    };
  }

  /**
   * Filter providers by requirements
   */
  private filterProviders(request: RoutingRequest): LLMProvider[] {
    const available: LLMProvider[] = [];

    for (const provider of this.providers.values()) {
      // Check quality requirement (simplified - would need quality scores)
      // Check context window
      if (request.contextSize && provider.maxContext < request.contextSize) {
        continue;
      }

      // Check capabilities
      if (request.requiresTools && !provider.capabilities.tools) {
        continue;
      }

      if (request.requiresVision && !provider.capabilities.vision) {
        continue;
      }

      if (request.requiresJsonMode && !provider.capabilities.jsonMode) {
        continue;
      }

      if (request.requiresStreaming && !provider.capabilities.streaming) {
        continue;
      }

      available.push(provider);
    }

    return available;
  }

  /**
   * Score providers
   */
  private scoreProviders(
    request: RoutingRequest,
    providers: LLMProvider[]
  ): ProviderScore[] {
    const policy = this.policies.get(request.taskType);
    const scored: ProviderScore[] = [];

    for (const provider of providers) {
      let score = 0.0;
      const factors: ProviderScore['factors'] = {
        quality: 0,
        cost: 0,
        performance: 0,
      };

      // Factor 1: Quality score (0-50 points)
      const qualityScore = this.getQualityScore(provider);
      const qualityPoints = qualityScore * 50;
      score += qualityPoints;
      factors.quality = qualityPoints;

      // Factor 2: Cost efficiency (0-20 points)
      const costPred = this.costPredictor.predictCost(provider, request);
      if (!costPred.withinBudget) {
        continue; // Skip if over budget
      }

      const costPoints = costPred.costEfficiencyScore * 20;
      score += costPoints;
      factors.cost = costPoints;

      // Factor 3: Performance history (0-15 points)
      const perfWeight = this.performanceTracker.getRecommendationWeight(
        provider.name,
        request.taskType
      );
      const perfPoints = perfWeight * 15;
      score += perfPoints;
      factors.performance = perfPoints;

      // Factor 4: Task preference bonus (0-5 points)
      if (policy && policy.preferredProviders.includes(provider.name)) {
        score += 5;
        factors.preferred = 5;
      }

      // Factor 5: Vendor diversity bonus (0-3 points)
      if (request.vendorDiversity) {
        // Would need to track recent providers
        score += 1; // Simplified
        factors.diversity = 1;
      }

      // Factor 6: Vendor preference bonus (0-2 points)
      if (request.vendorPreference) {
        const vendor = provider.name.split(':')[0];
        if (vendor === request.vendorPreference) {
          score += 2;
        }
      }

      scored.push({
        provider,
        score,
        factors,
      });
    }

    // Sort by score descending
    scored.sort((a, b) => b.score - a.score);

    return scored;
  }

  /**
   * Get quality score for provider (simplified)
   */
  private getQualityScore(provider: LLMProvider): number {
    // Simplified - would use actual quality metrics
    // For now, use provider name as heuristic
    if (provider.name.includes('gpt-4') || provider.name.includes('claude-3-opus')) {
      return 0.95;
    }
    if (provider.name.includes('gpt-3.5') || provider.name.includes('claude-3-sonnet')) {
      return 0.85;
    }
    if (provider.name.includes('claude-3-haiku')) {
      return 0.75;
    }
    return 0.7; // Default
  }

  /**
   * Build rationale for decision
   */
  private buildRationale(score: ProviderScore, request: RoutingRequest): string {
    const reasons: string[] = [];

    reasons.push(`quality score ${score.factors.quality.toFixed(1)}`);
    reasons.push(`cost efficiency ${score.factors.cost.toFixed(1)}`);
    reasons.push(`performance history ${score.factors.performance.toFixed(1)}`);

    if (score.factors.preferred) {
      reasons.push('preferred for task type');
    }

    return `Selected ${score.provider.name} for ${request.taskType} based on: ${reasons.join(', ')}. Overall score: ${score.score.toFixed(1)}/100.`;
  }

  /**
   * Record request outcome for learning
   */
  recordOutcome(
    providerId: string,
    taskType: TaskType,
    success: boolean,
    latencyMs: number,
    cost: number,
    qualityScore?: number
  ): void {
    this.performanceTracker.recordMetric({
      providerId,
      taskType,
      success,
      latencyMs,
      cost,
      qualityScore,
    });
  }

  /**
   * Get performance tracker (for metrics)
   */
  getPerformanceTracker(): PerformanceTracker {
    return this.performanceTracker;
  }
}

