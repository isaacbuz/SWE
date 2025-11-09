# Structured Logging Guide

This guide covers structured logging implementation for the SWE Platform.

## Overview

Structured logging provides:
- **JSON Format**: Machine-readable log entries
- **OpenTelemetry Integration**: Automatic trace context inclusion
- **Consistent Format**: Standardized log structure across services
- **Better Analysis**: Easy to parse and analyze logs

## Implementation

### Python (FastAPI)

**Location**: `apps/api/services/logging_service.py`

```python
from services.logging_service import get_logger

logger = get_logger(
    service_name='swe-platform-api',
    service_version='1.0.0',
    environment='production',
    log_level='INFO'
)

# Log messages
logger.info('Service started', port=8000)
logger.error('Failed to connect', error='Connection timeout')
logger.warn('Rate limit approaching', requests=95, limit=100)
logger.debug('Processing request', request_id='123')
```

### TypeScript (Node.js)

**Location**: `packages/observability/src/logging/StructuredLogger.ts`

```typescript
import { createLogger } from '@ai-company/observability';

const logger = createLogger({
  serviceName: 'tool-service',
  serviceVersion: '1.0.0',
  environment: 'production',
  logLevel: LogLevel.INFO,
});

logger.info('Service started', { port: 3001 });
logger.error('Failed to connect', { error: 'Connection timeout' });
```

## Log Format

### Standard Fields

All log entries include:

- `timestamp`: ISO 8601 timestamp
- `level`: Log level (error, warn, info, debug)
- `message`: Log message
- `service`: Service name
- `version`: Service version
- `environment`: Environment (development, staging, production)

### OpenTelemetry Fields

When OpenTelemetry is enabled:

- `traceId`: OpenTelemetry trace ID
- `spanId`: OpenTelemetry span ID

### Custom Fields

Additional fields can be added:

```typescript
logger.info('Request processed', {
  requestId: '123',
  userId: '456',
  duration: 150,
  statusCode: 200,
});
```

## Log Levels

### Python

- `ERROR`: Error conditions
- `WARNING`: Warning conditions
- `INFO`: Informational messages
- `DEBUG`: Debug messages

### TypeScript

- `ERROR`: Error conditions
- `WARN`: Warning conditions
- `INFO`: Informational messages
- `DEBUG`: Debug messages

## Configuration

### Environment Variables

```bash
# Log level
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=production

# Service version
API_VERSION=1.0.0
```

### Python Configuration

```python
logger = get_logger(
    service_name='swe-platform-api',
    service_version='1.0.0',
    environment='production',
    log_level='INFO',
    enable_console=True,
    enable_file=True,
    log_file='logs/app.log'
)
```

### TypeScript Configuration

```typescript
const logger = createLogger({
  serviceName: 'tool-service',
  serviceVersion: '1.0.0',
  environment: 'production',
  logLevel: LogLevel.INFO,
  enableConsole: true,
  enableFile: true,
  logFile: 'logs/app.log',
  enableOpenTelemetry: true,
});
```

## Integration

### FastAPI Middleware

The logging service is integrated into FastAPI middleware:

```python
from services.logging_service import get_logger

logger = get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info('Request received', {
        'method': request.method,
        'path': request.url.path,
    })
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info('Request completed', {
        'method': request.method,
        'path': request.url.path,
        'status_code': response.status_code,
        'duration': duration,
    })
    
    return response
```

### Express Middleware

```typescript
app.use((req, res, next) => {
  const requestLogger = logger.child({
    method: req.method,
    path: req.path,
    requestId: req.headers['x-request-id'],
  });

  req.logger = requestLogger;
  next();
});
```

## Log Analysis

### Using jq

```bash
# Filter error logs
cat logs/app.log | jq 'select(.level == "error")'

# Filter by trace ID
cat logs/app.log | jq 'select(.traceId == "abc123")'

# Count errors by service
cat logs/app.log | jq -r 'select(.level == "error") | .service' | sort | uniq -c
```

### Using grep

```bash
# Find all error logs
grep '"level":"error"' logs/app.log

# Find logs for specific trace
grep '"traceId":"abc123"' logs/app.log
```

### Using Log Aggregation

For production, use log aggregation tools:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki** (Grafana Labs)
- **Datadog**
- **New Relic**

## Best Practices

1. **Use Structured Fields**: Always use structured fields instead of string interpolation
   ```typescript
   // Good
   logger.info('User logged in', { userId: '123', ip: '1.2.3.4' });
   
   // Bad
   logger.info(`User ${userId} logged in from ${ip}`);
   ```

2. **Include Context**: Add relevant context to logs
   ```typescript
   logger.error('Failed to process request', {
     requestId: '123',
     userId: '456',
     error: error.message,
     stack: error.stack,
   });
   ```

3. **Use Appropriate Levels**: Use the right log level
   - `ERROR`: Errors that need immediate attention
   - `WARN`: Warnings that should be monitored
   - `INFO`: Important events (startup, shutdown, key operations)
   - `DEBUG`: Detailed information for debugging

4. **Don't Log Sensitive Data**: Never log passwords, tokens, or PII
   ```typescript
   // Good
   logger.info('User authenticated', { userId: '123' });
   
   // Bad
   logger.info('User authenticated', { password: 'secret123' });
   ```

5. **Use Child Loggers**: Create child loggers for request context
   ```typescript
   const requestLogger = logger.child({ requestId: '123' });
   requestLogger.info('Processing request');
   ```

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration
2. Verify file permissions for file logging
3. Check console output for console logging

### Trace Context Missing

1. Verify OpenTelemetry is initialized
2. Check that spans are active when logging
3. Ensure `enableOpenTelemetry` is set to `true`

### Log Format Issues

1. Verify JSON serialization
2. Check for circular references
3. Ensure all values are JSON-serializable

## Related Documentation

- [OpenTelemetry Tracing](../tracing/README.md)
- [Prometheus Metrics](../metrics/README.md)
- [Staging Deployment](./STAGING_DEPLOYMENT.md)

