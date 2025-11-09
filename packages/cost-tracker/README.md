# Cost Tracker

Cost tracking for LLM providers, tools, and infrastructure.

## Installation

```bash
pnpm add @ai-company/cost-tracker
```

## Usage

### Basic Setup

```typescript
import { createCostTracker } from '@ai-company/cost-tracker';
import { PrometheusMetrics } from '@ai-company/observability';

const metrics = new PrometheusMetrics({ serviceName: 'my-service' });
const costTracker = createCostTracker(undefined, metrics);

// Record LLM provider cost
costTracker.recordLLMCost('openai', 'gpt-4', 1000, 500);

// Record tool execution cost
costTracker.recordToolCost('github_api', 0.01);

// Get cost summary
const summary = costTracker.getCostSummary(
  new Date('2025-11-01'),
  new Date('2025-11-09')
);
```

### Custom Pricing

```typescript
const customPricing = {
  openai: {
    'gpt-4': {
      promptPricePer1kTokens: 0.03,
      completionPricePer1kTokens: 0.06,
    },
  },
};

const costTracker = createCostTracker(customPricing);
```

## API

### `recordLLMCost(provider, model, promptTokens, completionTokens, metadata?)`

Record LLM provider usage cost.

### `recordToolCost(toolName, costUSD, metadata?)`

Record tool execution cost.

### `recordInfrastructureCost(service, costUSD, metadata?)`

Record infrastructure cost.

### `getCostSummary(startDate, endDate)`

Get cost summary for a period.

### `getAllCosts()`

Get all cost entries.

## Supported Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3 Opus, Sonnet, Haiku)
- Google (Gemini Pro, Ultra)
- Mistral (Large, Medium, Small)
- Cohere (Command, Command Light)
- IBM (Granite 13B, 8B)

## Related

- [Prometheus Metrics](../observability/src/metrics/README.md)
- [Cost Tracking API](../../apps/api/routers/cost_tracking.py)

