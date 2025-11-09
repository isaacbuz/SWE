# @ai-company/moe-router

TypeScript MoE Router with intelligent provider selection.

## Overview

Intelligent router that selects the best LLM provider for each task based on cost, quality, performance history, and task requirements.

## Features

- ✅ Multi-factor routing (cost, quality, latency, capabilities)
- ✅ Performance-based learning
- ✅ Task type classification
- ✅ Cost optimization
- ✅ Provider fallback
- ✅ Performance tracking with time decay

## Installation

```bash
pnpm add @ai-company/moe-router
```

## Usage

```typescript
import { MoERouter, TaskType } from '@ai-company/moe-router';
import { OpenAIProvider, AnthropicProvider } from '@ai-company/llm-providers';

// Create router
const router = new MoERouter();

// Register providers
router.registerProvider(new OpenAIProvider(process.env.OPENAI_API_KEY!));
router.registerProvider(new AnthropicProvider(process.env.ANTHROPIC_API_KEY!));

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

console.log(`Selected: ${decision.selectedProvider.name}`);
console.log(`Confidence: ${decision.confidence}`);
console.log(`Rationale: ${decision.rationale}`);

// Use provider
const result = await decision.selectedProvider.completion({
  messages: [{ role: 'user', content: 'Hello!' }],
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

## API Reference

### MoERouter

```typescript
class MoERouter {
  registerProvider(provider: LLMProvider): void;
  setPolicy(taskType: TaskType, policy: RoutingPolicy): void;
  selectProvider(request: RoutingRequest): RoutingDecision;
  recordOutcome(...): void;
  getPerformanceTracker(): PerformanceTracker;
}
```

## Related Packages

- `@ai-company/llm-providers` - LLM provider implementations
- `@ai-company/tool-pipeline` - Tool calling pipeline

## License

MIT

