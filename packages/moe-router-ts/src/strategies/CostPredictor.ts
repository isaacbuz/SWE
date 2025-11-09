import { LLMProvider, CompletionOptions } from '@ai-company/llm-providers';
import { RoutingRequest } from '../types';

/**
 * Cost prediction for provider selection
 */
export class CostPredictor {
  /**
   * Predict cost for a request
   */
  predictCost(
    provider: LLMProvider,
    request: RoutingRequest,
    estimatedInputTokens: number = 1000,
    estimatedOutputTokens: number = 500
  ): {
    expectedCost: number;
    withinBudget: boolean;
    costEfficiencyScore: number; // 0-1, higher is better
  } {
    const inputCost = (estimatedInputTokens / 1_000_000) * provider.pricePerMTokIn;
    const outputCost = (estimatedOutputTokens / 1_000_000) * provider.pricePerMTokOut;
    const expectedCost = inputCost + outputCost;

    const withinBudget = request.costBudget
      ? expectedCost <= request.costBudget
      : true;

    // Cost efficiency: inverse of cost (normalized)
    // Lower cost = higher efficiency score
    const maxCost = Math.max(provider.pricePerMTokIn, provider.pricePerMTokOut) * 0.01; // 10k tokens
    const costEfficiencyScore = Math.max(0, 1 - (expectedCost / maxCost));

    return {
      expectedCost,
      withinBudget,
      costEfficiencyScore,
    };
  }
}

