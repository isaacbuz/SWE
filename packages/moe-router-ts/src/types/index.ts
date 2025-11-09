/**
 * MoE Router types and interfaces
 */

import { LLMProvider, CompletionOptions } from '@ai-company/llm-providers';

/**
 * Task type classification
 */
export enum TaskType {
  CODE_GENERATION = 'code_generation',
  CODE_ANALYSIS = 'code_analysis',
  PLANNING = 'planning',
  REVIEW = 'review',
  REFACTORING = 'refactoring',
  TESTING = 'testing',
  DOCUMENTATION = 'documentation',
  GENERAL = 'general',
}

/**
 * Routing request
 */
export interface RoutingRequest {
  /**
   * Task type
   */
  taskType: TaskType;

  /**
   * Quality requirement (0-1)
   */
  qualityRequirement: number;

  /**
   * Cost budget in USD
   */
  costBudget?: number;

  /**
   * Context size in tokens
   */
  contextSize?: number;

  /**
   * Latency requirement in milliseconds
   */
  latencyRequirementMs?: number;

  /**
   * Requires tool calling
   */
  requiresTools?: boolean;

  /**
   * Requires vision capabilities
   */
  requiresVision?: boolean;

  /**
   * Requires JSON mode
   */
  requiresJsonMode?: boolean;

  /**
   * Requires streaming
   */
  requiresStreaming?: boolean;

  /**
   * Vendor preference
   */
  vendorPreference?: string;

  /**
   * Vendor diversity (avoid same vendor consecutively)
   */
  vendorDiversity?: boolean;
}

/**
 * Routing policy
 */
export interface RoutingPolicy {
  taskType: TaskType;
  preferredProviders: string[];
  costWeight: number; // 0-1
  latencyWeight: number; // 0-1
  qualityWeight: number; // 0-1
  maxCostPerRequest?: number;
}

/**
 * Provider score
 */
export interface ProviderScore {
  provider: LLMProvider;
  score: number;
  factors: {
    quality: number;
    cost: number;
    performance: number;
    learned?: number;
    preferred?: number;
    diversity?: number;
  };
}

/**
 * Routing decision
 */
export interface RoutingDecision {
  selectedProvider: LLMProvider;
  confidence: number;
  rationale: string;
  estimatedCost: number;
  estimatedQuality: number;
  fallbackProviders: LLMProvider[];
  scores: ProviderScore[];
}

