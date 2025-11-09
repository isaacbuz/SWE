# Structured Logging

Structured JSON logging with OpenTelemetry integration for TypeScript/Node.js services.

## Installation

```bash
pnpm add @ai-company/observability
```

## Usage

### Basic Setup

```typescript
import { createLogger, LogLevel } from '@ai-company/observability';

const logger = createLogger({
  serviceName: 'my-service',
  serviceVersion: '1.0.0',
  environment: 'production',
  logLevel: LogLevel.INFO,
  enableConsole: true,
  enableFile: true,
  logFile: 'logs/app.log',
  enableOpenTelemetry: true,
});

// Log messages
logger.info('Service started', { port: 3000 });
logger.error('Failed to connect', { error: 'Connection timeout' });
logger.warn('Rate limit approaching', { requests: 95, limit: 100 });
logger.debug('Processing request', { requestId: '123' });
```

### With OpenTelemetry Context

The logger automatically includes trace context when available:

```typescript
import { trace } from '@opentelemetry/api';

trace.getTracer('my-service').startActiveSpan('process-request', (span) => {
  // Logs will automatically include traceId and spanId
  logger.info('Processing request', { requestId: '123' });
  
  span.end();
});
```

### Child Loggers

Create child loggers with additional context:

```typescript
const requestLogger = logger.child({ requestId: '123', userId: '456' });

requestLogger.info('Request received');
requestLogger.info('Request processed');
// Both logs will include requestId and userId
```

### Log Levels

```typescript
enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug',
}
```

### Log Entry Format

```json
{
  "timestamp": "2025-11-09T12:00:00.000Z",
  "level": "info",
  "message": "Request processed",
  "service": "my-service",
  "version": "1.0.0",
  "environment": "production",
  "traceId": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "spanId": "q1r2s3t4u5v6w7x8",
  "requestId": "123",
  "userId": "456"
}
```

## Integration with Express

```typescript
import express from 'express';
import { createLogger } from '@ai-company/observability';

const app = express();
const logger = createLogger({ serviceName: 'api' });

app.use((req, res, next) => {
  const requestLogger = logger.child({
    method: req.method,
    path: req.path,
    requestId: req.headers['x-request-id'],
  });

  req.logger = requestLogger;
  next();
});

app.get('/api/users', (req, res) => {
  req.logger.info('Fetching users');
  // ...
});
```

## Integration with Fastify

```typescript
import Fastify from 'fastify';
import { createLogger } from '@ai-company/observability';

const fastify = Fastify();
const logger = createLogger({ serviceName: 'api' });

fastify.addHook('onRequest', async (request, reply) => {
  request.logger = logger.child({
    method: request.method,
    url: request.url,
    requestId: request.id,
  });
});

fastify.get('/api/users', async (request, reply) => {
  request.logger.info('Fetching users');
  // ...
});
```

## File Logging

Enable file logging for production:

```typescript
const logger = createLogger({
  serviceName: 'my-service',
  enableFile: true,
  logFile: 'logs/app.log',
});
```

## OpenTelemetry Integration

The logger automatically integrates with OpenTelemetry:

- **Trace Context**: Automatically includes `traceId` and `spanId` in logs
- **Error Recording**: Errors are recorded in OpenTelemetry spans
- **Span Status**: Error logs update span status to ERROR

## Related

- [OpenTelemetry Tracing](../tracing/README.md)
- [Prometheus Metrics](../metrics/README.md)

