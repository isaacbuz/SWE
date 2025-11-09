# OpenTelemetry Distributed Tracing

Distributed tracing implementation using OpenTelemetry.

## Installation

```bash
pnpm add @ai-company/observability
```

## Usage

### Basic Setup

```typescript
import { OpenTelemetryTracer } from '@ai-company/observability';

const tracer = new OpenTelemetryTracer({
  serviceName: 'my-service',
  serviceVersion: '1.0.0',
  environment: 'production',
  otlpEndpoint: 'http://localhost:4318',
  sampleRate: 1.0,
});

// Initialize tracer
tracer.initialize();

// Shutdown on exit
process.on('SIGTERM', () => tracer.shutdown());
```

### Manual Span Creation

```typescript
import { OpenTelemetryTracer, SpanKind } from '@ai-company/observability';

const tracer = new OpenTelemetryTracer({ serviceName: 'my-service' });
tracer.initialize();

const span = tracer.startSpan('my-operation', {
  kind: SpanKind.SERVER,
  attributes: {
    'http.method': 'GET',
    'http.route': '/api/users',
  },
});

try {
  // Your code here
  span.setStatus({ code: SpanStatusCode.OK });
} catch (error) {
  span.setStatus({ code: SpanStatusCode.ERROR });
  span.recordException(error);
} finally {
  span.end();
}
```

### Trace Function Execution

```typescript
const result = await tracer.trace('process-data', async (span) => {
  span.setAttribute('data.size', data.length);
  return await processData(data);
}, {
  attributes: {
    'operation.type': 'data-processing',
  },
});
```

### Add Events and Attributes

```typescript
tracer.addEvent('cache-hit', { key: 'user:123' });
tracer.setAttribute('user.id', '123');
```

### Context Propagation

```typescript
// Inject trace context into HTTP headers
const headers = tracer.injectHeaders({ 'Authorization': 'Bearer token' });

// Extract trace context from headers
const extractedContext = tracer.extractContext(request.headers);
```

## Configuration

- **serviceName**: Name of your service
- **serviceVersion**: Version of your service
- **environment**: Deployment environment (development, staging, production)
- **otlpEndpoint**: OTLP endpoint URL (default: http://localhost:4318)
- **otlpHeaders**: Additional headers for OTLP exporter
- **enableAutoInstrumentation**: Enable automatic instrumentation (default: true)
- **sampleRate**: Sampling rate 0.0-1.0 (default: 1.0)

## Auto Instrumentation

When enabled, automatically instruments:
- HTTP requests (incoming and outgoing)
- Database queries
- Redis operations
- gRPC calls
- And more...

## Exporters

Currently supports OTLP HTTP exporter. Can be extended to support:
- Jaeger
- Zipkin
- Prometheus
- Custom exporters

## Related

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [OTLP Protocol](https://opentelemetry.io/docs/specs/otlp/)

