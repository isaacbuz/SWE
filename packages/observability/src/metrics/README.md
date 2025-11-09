# Prometheus Metrics Collection

Prometheus metrics collection and export for monitoring.

## Installation

```bash
pnpm add @ai-company/observability
```

## Usage

### Basic Setup

```typescript
import { PrometheusMetrics } from '@ai-company/observability';

const metrics = new PrometheusMetrics({
  serviceName: 'my-service',
  serviceVersion: '1.0.0',
  environment: 'production',
  enableDefaultMetrics: true,
});

// Get metrics endpoint (for Express/Fastify)
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', 'text/plain');
  res.send(await metrics.getMetrics());
});
```

### Record HTTP Metrics

```typescript
const startTime = Date.now();

try {
  // Handle request
  const duration = (Date.now() - startTime) / 1000;
  metrics.recordHttpRequest('GET', '/api/users', 200, duration);
} catch (error) {
  const duration = (Date.now() - startTime) / 1000;
  metrics.recordHttpRequest('GET', '/api/users', 500, duration);
}
```

### Record LLM Provider Metrics

```typescript
const startTime = Date.now();

try {
  const result = await llmProvider.completion({ ... });
  const duration = (Date.now() - startTime) / 1000;

  metrics.recordLLMRequest(
    'openai',
    'gpt-4',
    'success',
    duration,
    result.usage.promptTokens,
    result.usage.completionTokens,
    calculateCost(result.usage)
  );
} catch (error) {
  const duration = (Date.now() - startTime) / 1000;
  metrics.recordLLMRequest('openai', 'gpt-4', 'error', duration);
}
```

### Record Tool Execution Metrics

```typescript
const startTime = Date.now();

try {
  await executeTool('github_create_issue', args);
  const duration = (Date.now() - startTime) / 1000;
  metrics.recordToolExecution('github_create_issue', 'success', duration);
} catch (error) {
  const duration = (Date.now() - startTime) / 1000;
  metrics.recordToolExecution('github_create_issue', 'error', duration);
}
```

### Cache Metrics

```typescript
if (cache.has(key)) {
  metrics.recordCacheHit('redis');
} else {
  metrics.recordCacheMiss('redis');
}
```

### Connection Metrics

```typescript
// Update active connections
metrics.updateActiveConnections('websocket', activeWebSocketConnections);
metrics.updateActiveConnections('http', activeHttpConnections);
metrics.updateActiveConnections('db', activeDbConnections);
```

## Available Metrics

### HTTP Metrics
- `swe_platform_http_request_duration_seconds` - Request duration histogram
- `swe_platform_http_requests_total` - Total request counter
- `swe_platform_http_request_errors_total` - Error counter

### LLM Provider Metrics
- `swe_platform_llm_provider_requests_total` - Provider request counter
- `swe_platform_llm_provider_latency_seconds` - Provider latency histogram
- `swe_platform_llm_provider_tokens_total` - Token counter
- `swe_platform_llm_provider_cost_usd_total` - Cost counter

### Tool Execution Metrics
- `swe_platform_tool_executions_total` - Tool execution counter
- `swe_platform_tool_execution_duration_seconds` - Execution duration histogram

### System Metrics
- `swe_platform_active_connections` - Active connections gauge
- `swe_platform_cache_hits_total` - Cache hit counter
- `swe_platform_cache_misses_total` - Cache miss counter

### Default Metrics
When `enableDefaultMetrics` is true, also collects:
- CPU usage
- Memory usage
- Event loop lag
- Process uptime
- And more...

## Integration with Express

```typescript
import express from 'express';
import { PrometheusMetrics } from '@ai-company/observability';

const app = express();
const metrics = new PrometheusMetrics({ serviceName: 'api' });

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', 'text/plain');
  res.send(await metrics.getMetrics());
});

// Middleware to record HTTP metrics
app.use((req, res, next) => {
  const startTime = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - startTime) / 1000;
    metrics.recordHttpRequest(req.method, req.route?.path || req.path, res.statusCode, duration);
  });
  next();
});
```

## Integration with Fastify

```typescript
import Fastify from 'fastify';
import { PrometheusMetrics } from '@ai-company/observability';

const fastify = Fastify();
const metrics = new PrometheusMetrics({ serviceName: 'api' });

// Metrics endpoint
fastify.get('/metrics', async (request, reply) => {
  reply.type('text/plain');
  return await metrics.getMetrics();
});

// Hook to record metrics
fastify.addHook('onResponse', async (request, reply) => {
  const duration = (Date.now() - request.startTime) / 1000;
  metrics.recordHttpRequest(
    request.method,
    request.routerPath || request.url,
    reply.statusCode,
    duration
  );
});
```

## Related

- [Prometheus Documentation](https://prometheus.io/docs/)
- [prom-client Documentation](https://github.com/siimon/prom-client)

