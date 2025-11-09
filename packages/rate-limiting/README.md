# @ai-company/rate-limiting

Rate limiting and quotas for tool execution.

## Overview

Per-user and per-tool rate limiting with cost quotas for controlling tool execution.

## Features

- ✅ Per-user rate limiting
- ✅ Per-tool rate limiting
- ✅ Cost quotas (daily/monthly)
- ✅ Sliding window algorithm
- ✅ Quota tracking and alerts

## Installation

```bash
pnpm add @ai-company/rate-limiting
```

## Usage

### Rate Limiting

```typescript
import { RateLimiter } from '@ai-company/rate-limiting';

const limiter = new RateLimiter();

// Check rate limit
const status = limiter.checkLimit({
  maxRequests: 100,
  windowMs: 60 * 1000, // 1 minute
  identifier: 'user-123',
});

if (status.exceeded) {
  throw new Error(`Rate limit exceeded. Retry after ${status.resetAt}`);
}
```

### Quota Management

```typescript
import { QuotaManager } from '@ai-company/rate-limiting';

const quotaManager = new QuotaManager();

// Check quota before execution
const cost = 0.01;
const status = quotaManager.checkQuota(
  {
    maxCost: 10.0,
    periodMs: 24 * 60 * 60 * 1000, // 24 hours
    identifier: 'user-123',
  },
  cost
);

if (status.exceeded) {
  throw new Error(`Quota exceeded. Remaining: $${status.remaining}`);
}
```

## Related Packages

- `@ai-company/tool-executor` - Tool execution engine
- `@ai-company/audit-logging` - Audit logging

## License

MIT

