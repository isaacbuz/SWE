# @ai-company/rate-limiter

Rate limiting and cost quota tracking for LLM-powered tool execution.

## Features

- **Multi-Level Rate Limiting**: Per-user, per-tool, and global limits
- **Cost Quotas**: Daily and monthly spending limits
- **Automatic Resets**: Windows reset automatically
- **Usage Statistics**: Track requests and costs
- **Integration-Ready**: Works with ToolExecutor

## Installation

```bash
npm install @ai-company/rate-limiter
```

## Usage

### Rate Limiting

```typescript
import { RateLimiter, RateLimit } from '@ai-company/rate-limiter';

const config = {
  userLimit: { maxRequests: 1000, windowMs: 3600000, per: 'user' },
  toolLimits: new Map([
    ['github/createIssues', { maxRequests: 100, windowMs: 3600000, per: 'tool' }]
  ]),
  globalLimit: { maxRequests: 10000, windowMs: 3600000, per: 'global' },
  quotas: new Map()
};

const rateLimiter = new RateLimiter(config);

const result = await rateLimiter.checkLimit('user123', 'github/createIssues');
if (!result.allowed) {
  console.log(`Rate limited. Retry after ${result.retryAfter}s`);
}
```

### Cost Quotas

```typescript
import { CostQuotaTracker } from '@ai-company/rate-limiter';

const quotas = new Map([
  ['default', { maxCostPerDay: 10.0, maxCostPerMonth: 200.0 }]
]);

const quotaTracker = new CostQuotaTracker(quotas);

const result = await quotaTracker.checkQuota('user123', 0.05);
if (!result.allowed) {
  console.log(`Quota exceeded. Resets at ${result.resetAt}`);
}

// Track actual cost after execution
await quotaTracker.trackCost('user123', 0.042);
```

## API

### RateLimiter

- `checkLimit(userId, toolName)`: Check rate limit
- `getUsage(userId)`: Get current usage stats

### CostQuotaTracker

- `checkQuota(userId, estimatedCost)`: Check if cost within quota
- `trackCost(userId, actualCost)`: Record actual cost
- `resetQuota(userId, period)`: Manually reset quota
- `getUsage(userId)`: Get usage statistics

## License

MIT
