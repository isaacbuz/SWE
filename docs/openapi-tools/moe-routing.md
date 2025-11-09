# MoE Routing Documentation

## Overview

The MoE (Mixture of Experts) Router intelligently selects the best LLM provider for each task based on multiple factors.

## Routing Factors

### 1. Quality Score (0-50 points)

Base quality rating of the model:
- GPT-4 / Claude Opus: ~47-49 points
- GPT-3.5 / Claude Sonnet: ~41-43 points
- Claude Haiku: ~40 points

### 2. Cost Efficiency (0-20 points)

Cost per token optimization:
- Lower cost = higher score
- Formula: `(1 / (1 + cost × 100)) × 20`

### 3. Performance History (0-15 points)

Success rate from historical data:
- Includes time-based decay
- Recent performance weighted higher

### 4. Task Preference (0-5 points)

Model appears in preferred list for task type:
- Flat +5 points bonus

### 5. Vendor Diversity (0-3 points)

Different provider from recent requests:
- Prevents vendor lock-in
- Flat +3 points bonus

## Usage

```typescript
import { MoERouter, TaskType } from '@ai-company/moe-router';
import { OpenAIProvider, AnthropicProvider } from '@ai-company/llm-providers';

const router = new MoERouter();

// Register providers
router.registerProvider(new OpenAIProvider(openaiKey));
router.registerProvider(new AnthropicProvider(anthropicKey));

// Set routing policy
router.setPolicy(TaskType.CODE_GENERATION, {
  taskType: TaskType.CODE_GENERATION,
  preferredProviders: ['openai:gpt-4-turbo-preview'],
  costWeight: 0.3,
  latencyWeight: 0.2,
  qualityWeight: 0.5,
});

// Select provider
const decision = router.selectProvider({
  taskType: TaskType.CODE_GENERATION,
  qualityRequirement: 0.8,
  costBudget: 0.01,
  requiresTools: true,
});

// Use provider
const result = await decision.selectedProvider.completion({
  messages: [{ role: 'user', content: 'Generate code' }],
});

// Record outcome for learning
router.recordOutcome(
  decision.selectedProvider.name,
  TaskType.CODE_GENERATION,
  true,
  500,
  0.002
);
```

## Task Types

- `CODE_GENERATION` - Writing code
- `CODE_ANALYSIS` - Analyzing code
- `PLANNING` - Project planning
- `REVIEW` - Code review
- `REFACTORING` - Code refactoring
- `TESTING` - Test generation
- `DOCUMENTATION` - Documentation generation
- `GENERAL` - General tasks

## Performance Tracking

The router learns from outcomes:

```typescript
router.recordOutcome(
  providerId,
  taskType,
  success,
  latencyMs,
  cost,
  qualityScore
);
```

This data is used to improve future routing decisions.

## Related Documentation

- [MoE Router README](../../packages/moe-router-ts/README.md)
- [Architecture Overview](./architecture.md)

