# Cost Tracking Guide

This guide covers cost tracking implementation for the SWE Platform.

## Overview

The cost tracking system provides:
- **LLM Provider Cost Tracking**: Automatic cost calculation based on token usage
- **Tool Execution Cost Tracking**: Track costs for external API calls
- **Infrastructure Cost Tracking**: Track infrastructure costs
- **Cost Aggregation**: Summarize costs by service, provider, and model
- **Prometheus Integration**: Export cost metrics to Prometheus

## Implementation

### TypeScript/Node.js

**Location**: `packages/cost-tracker/src/CostTracker.ts`

```typescript
import { createCostTracker } from '@ai-company/cost-tracker';
import { PrometheusMetrics } from '@ai-company/observability';

const metrics = new PrometheusMetrics({ serviceName: 'tool-service' });
const costTracker = createCostTracker(undefined, metrics);

// Record LLM cost
costTracker.recordLLMCost('openai', 'gpt-4', 1000, 500);

// Get summary
const summary = costTracker.getCostSummary(startDate, endDate);
```

### Python/FastAPI

**Location**: `apps/api/services/cost_tracking_service.py`

```python
from services.cost_tracking_service import get_cost_tracker

cost_tracker = get_cost_tracker()

# Record LLM cost
cost_tracker.record_llm_cost('openai', 'gpt-4', 1000, 500)

# Get summary
summary = cost_tracker.get_cost_summary(start_date, end_date)
```

## API Endpoints

### Get Cost Summary

```http
GET /api/v1/costs/summary?days=7
```

Returns aggregated cost data:
- Total cost
- Cost by service
- Cost by provider
- Cost by model
- Entry count

### Get Cost Entries

```http
GET /api/v1/costs/entries?service=llm-provider&limit=100
```

Returns individual cost entries with filtering options.

### Get Pricing

```http
GET /api/v1/costs/pricing
```

Returns current pricing configuration for all providers and models.

## Pricing Configuration

Default pricing is included for all supported providers. Pricing can be customized:

### TypeScript

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

### Python

```python
custom_pricing = {
    'openai': {
        'gpt-4': {'prompt': 0.03, 'completion': 0.06},
    },
}

cost_tracker = CostTrackingService(custom_pricing)
```

## Cost Calculation

### LLM Provider Costs

Cost is calculated based on:
- Prompt tokens: `(promptTokens / 1000) * promptPricePer1kTokens`
- Completion tokens: `(completionTokens / 1000) * completionPricePer1kTokens`
- Total: `promptCost + completionCost`

### Tool Execution Costs

Tool costs are recorded directly (e.g., API call costs).

### Infrastructure Costs

Infrastructure costs are recorded directly (e.g., compute, storage).

## Prometheus Integration

Costs are automatically exported to Prometheus metrics:

- `swe_platform_llm_provider_cost_usd_total`: Total cost counter
- Cost included in LLM request metrics

## Cost Summary Structure

```typescript
interface CostSummary {
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
```

## Usage Examples

### Track LLM Usage

```typescript
// After LLM API call
const result = await llmProvider.completion({ ... });
costTracker.recordLLMCost(
  'openai',
  'gpt-4',
  result.usage.promptTokens,
  result.usage.completionTokens,
  { requestId: '123' }
);
```

### Track Tool Execution

```typescript
// After external API call
const apiCost = 0.01; // $0.01 per API call
costTracker.recordToolCost('github_api', apiCost, {
  operation: 'create_issue',
  requestId: '123',
});
```

### Get Daily Cost Report

```typescript
const today = new Date();
const yesterday = new Date(today);
yesterday.setDate(yesterday.getDate() - 1);

const summary = costTracker.getCostSummary(yesterday, today);
console.log(`Total cost today: $${summary.totalCost.toFixed(2)}`);
console.log(`By provider:`, summary.byProvider);
```

## Best Practices

1. **Record Costs Immediately**: Record costs as soon as they occur
2. **Include Metadata**: Add relevant metadata for debugging and analysis
3. **Regular Monitoring**: Monitor costs regularly to detect anomalies
4. **Set Budgets**: Use cost summaries to set and monitor budgets
5. **Alert on High Costs**: Set up alerts for excessive costs (see Issue #94)

## Related Documentation

- [Prometheus Metrics](./STRUCTURED_LOGGING.md)
- [Alerting System](./ALERTING_SETUP.md)
- [Staging Deployment](./STAGING_DEPLOYMENT.md)

