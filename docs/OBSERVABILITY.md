# Observability Guide

This comprehensive guide covers all aspects of observability in the SWE Platform, including distributed tracing, metrics collection, logging, dashboards, and alerting.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [OpenTelemetry Distributed Tracing](#opentelemetry-distributed-tracing)
4. [Prometheus Metrics](#prometheus-metrics)
5. [Structured Logging](#structured-logging)
6. [Grafana Dashboards](#grafana-dashboards)
7. [Alerting System](#alerting-system)
8. [Cost Tracking](#cost-tracking)
9. [Audit Logging](#audit-logging)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Overview

The SWE Platform implements a comprehensive observability stack that provides:

- **Distributed Tracing**: Track requests across services with OpenTelemetry
- **Metrics Collection**: Monitor system health with Prometheus
- **Structured Logging**: Consistent, searchable logs with context
- **Dashboards**: Visualize metrics and traces in Grafana
- **Alerting**: Get notified of issues with Alertmanager
- **Cost Tracking**: Monitor LLM and infrastructure costs
- **Audit Logging**: Track user actions for compliance

## Architecture

```
┌─────────────────┐
│   Application   │
│   Services      │
└────────┬────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│  OpenTelemetry  │                  │   Prometheus    │
│     Tracing     │                  │    Metrics      │
└────────┬────────┘                  └────────┬────────┘
         │                                     │
         │                                     │
         ▼                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│      Tempo      │                  │   Prometheus    │
│  (Trace Store)  │                  │   (Storage)     │
└────────┬────────┘                  └────────┬────────┘
         │                                     │
         └──────────────┬──────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │     Grafana     │
              │   Dashboards    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Alertmanager   │
              │    Alerts       │
              └─────────────────┘
```

## OpenTelemetry Distributed Tracing

### Overview

OpenTelemetry provides distributed tracing to track requests across services, helping identify bottlenecks and debug issues.

### Implementation

**TypeScript/Node.js**:
- Location: `packages/observability/src/tracing/OpenTelemetryTracer.ts`
- Provides span creation, context propagation, and OTLP export

**Python/FastAPI**:
- Location: `packages/observability/tracing.py`
- Integrates with FastAPI middleware for automatic instrumentation

### Usage

#### TypeScript

```typescript
import { OpenTelemetryTracer } from '@ai-company/observability';

const tracer = new OpenTelemetryTracer({
  serviceName: 'my-service',
  otlpEndpoint: 'http://tempo:4317',
});

// Create a span
const span = tracer.startSpan('my-operation');
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

#### Python

```python
from observability.tracing import DistributedTracing

tracer = DistributedTracing(
    service_name='my-service',
    otlp_endpoint='http://tempo:4317'
)

# Create a span
with tracer.start_span('my-operation') as span:
    try:
        # Your code here
        span.set_status(StatusCode.OK)
    except Exception as e:
        span.set_status(StatusCode.ERROR)
        span.record_exception(e)
```

### Configuration

- **OTLP Endpoint**: `http://tempo:4317` (default)
- **Service Name**: Set per service
- **Sampling Rate**: Configurable (default: 100%)

### Viewing Traces

Traces can be viewed in Grafana by navigating to the "Traces" dashboard and selecting a service.

## Prometheus Metrics

### Overview

Prometheus collects metrics from all services, providing insights into system performance and health.

### Implementation

**TypeScript/Node.js**:
- Location: `packages/observability/src/metrics/PrometheusMetrics.ts`
- Exposes `/metrics` endpoint

**Python/FastAPI**:
- Location: `apps/api/services/metrics_service.py`
- Exposes `/metrics` endpoint

### Available Metrics

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `http_request_size_bytes` - Request size
- `http_response_size_bytes` - Response size

#### LLM Provider Metrics
- `llm_provider_requests_total` - Total LLM requests
- `llm_provider_latency_seconds` - LLM request latency
- `llm_provider_tokens_total` - Tokens processed
- `llm_provider_cost_usd_total` - Cost in USD

#### Tool Execution Metrics
- `tool_executions_total` - Total tool executions
- `tool_execution_duration_seconds` - Execution duration
- `tool_execution_errors_total` - Execution errors

#### System Metrics
- `system_cpu_usage` - CPU usage percentage
- `system_memory_usage` - Memory usage bytes
- `system_disk_usage` - Disk usage bytes

### Configuration

Prometheus scrapes metrics from:
- API Service: `http://api:8000/metrics`
- Tool Service: `http://tool-service:3000/metrics`

Scrape interval: 15 seconds (default)

### Viewing Metrics

Metrics can be viewed in Grafana dashboards or queried directly using PromQL.

## Structured Logging

### Overview

Structured logging provides consistent, searchable logs with context, integrated with OpenTelemetry for trace correlation.

### Implementation

**TypeScript/Node.js**:
- Location: `packages/observability/src/logging/StructuredLogger.ts`
- Uses Winston with JSON formatter

**Python/FastAPI**:
- Location: `apps/api/services/logging_service.py`
- Uses Python logging with JSON formatter

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages
- `WARN` - Warning messages
- `ERROR` - Error messages
- `FATAL` - Fatal errors

### Log Format

```json
{
  "timestamp": "2025-11-09T12:00:00Z",
  "level": "info",
  "service": "api",
  "message": "Request processed",
  "trace_id": "abc123",
  "span_id": "def456",
  "user_id": "user-123",
  "request_id": "req-789"
}
```

### Usage

#### TypeScript

```typescript
import { StructuredLogger } from '@ai-company/observability';

const logger = new StructuredLogger({
  serviceName: 'my-service',
  level: 'info',
});

logger.info('Request processed', {
  userId: 'user-123',
  requestId: 'req-789',
});
```

#### Python

```python
from services.logging_service import get_logger

logger = get_logger('my-service')

logger.info('Request processed', extra={
    'user_id': 'user-123',
    'request_id': 'req-789',
})
```

### Log Aggregation

Logs are collected and can be aggregated using:
- File-based storage (default)
- Log aggregation services (e.g., ELK, Loki)
- Cloud logging services

## Grafana Dashboards

### Overview

Grafana provides visual dashboards for metrics and traces, enabling real-time monitoring and analysis.

### Available Dashboards

1. **System Overview** (`system-overview.json`)
   - Overall system health
   - Request rates and latency
   - Error rates
   - Resource utilization

2. **HTTP Metrics** (`http-metrics.json`)
   - Request rate
   - Latency (p50, p95, p99)
   - Error rate
   - Request/response sizes

3. **LLM Providers** (`llm-providers.json`)
   - Request rate per provider
   - Latency per provider
   - Token usage
   - Cost per provider

4. **Tool Execution** (`tool-execution.json`)
   - Execution rate
   - Duration
   - Success/failure rate
   - Error breakdown

5. **Traces** (`traces.json`)
   - Trace overview
   - Service map
   - Trace details
   - Error traces

### Accessing Dashboards

1. Navigate to Grafana: `http://localhost:3000`
2. Default credentials: `admin/admin` (change in production)
3. Select a dashboard from the dashboard list

### Custom Dashboards

Create custom dashboards by:
1. Clicking "New Dashboard" in Grafana
2. Adding panels with PromQL queries
3. Saving the dashboard

## Alerting System

### Overview

The alerting system uses Prometheus Alertmanager to send notifications when metrics exceed thresholds.

### Alert Rules

Located in: `infrastructure/prometheus/alerts.yml`

#### HTTP Alerts
- High error rate (> 5%)
- High latency (p95 > 1s)
- High request rate (> 1000 req/s)

#### LLM Provider Alerts
- High error rate (> 10%)
- High latency (p95 > 5s)
- High cost (> $100/day)

#### Tool Execution Alerts
- High error rate (> 5%)
- High duration (> 30s)

#### System Health Alerts
- High CPU usage (> 80%)
- High memory usage (> 85%)
- High disk usage (> 90%)
- Service down

### Notification Channels

- **Slack**: `#alerts` channel
- **Email**: `alerts@example.com`
- **PagerDuty**: Integration configured

### Configuration

Alertmanager configuration: `infrastructure/alertmanager/alertmanager.yml`

- **Grouping**: Alerts grouped by service
- **Inhibition**: Related alerts suppressed
- **Routing**: Alerts routed by severity

## Cost Tracking

### Overview

Cost tracking monitors LLM provider usage, tool execution, and infrastructure costs.

### Implementation

- **TypeScript**: `packages/cost-tracker/src/CostTracker.ts`
- **Python**: `apps/api/services/cost_tracking_service.py`

### Features

- Automatic LLM cost calculation
- Tool execution cost tracking
- Infrastructure cost tracking
- Cost aggregation and reporting

### API Endpoints

- `GET /api/v1/costs/summary` - Get cost summary
- `GET /api/v1/costs/entries` - Get cost entries
- `GET /api/v1/costs/pricing` - Get pricing configuration

See [Cost Tracking Guide](./COST_TRACKING.md) for details.

## Audit Logging

### Overview

Audit logging tracks user actions and system events for compliance and security.

### Implementation

- **TypeScript**: `packages/audit-logging/src/AuditLogger.ts`
- **Python**: `apps/api/services/audit_service.py`

### Features

- User action tracking
- Tool execution logging
- Permission change tracking
- Security event logging
- Change tracking (before/after)

### API Endpoints

- `GET /api/v1/audit/logs` - Query audit logs
- `GET /api/v1/audit/logs/{log_id}` - Get audit log by ID
- `GET /api/v1/audit/summary` - Get audit summary

See [Audit Logging Guide](./AUDIT_LOGGING.md) for details.

## Best Practices

### 1. Use Structured Logging

Always use structured logging with context:

```typescript
logger.info('Operation completed', {
  userId: user.id,
  operationId: operation.id,
  duration: durationMs,
});
```

### 2. Create Spans for Operations

Create spans for important operations:

```typescript
const span = tracer.startSpan('process-payment');
// ... operation ...
span.end();
```

### 3. Add Custom Metrics

Add custom metrics for business logic:

```typescript
metrics.recordCustomMetric('orders_processed', 1, {
  order_type: 'premium',
});
```

### 4. Set Appropriate Log Levels

- `DEBUG`: Detailed debugging (development only)
- `INFO`: Normal operations
- `WARN`: Recoverable issues
- `ERROR`: Errors requiring attention
- `FATAL`: Critical errors

### 5. Include Context

Always include relevant context:
- User ID
- Request ID
- Trace ID
- Resource IDs

### 6. Monitor Key Metrics

Monitor:
- Request latency (p50, p95, p99)
- Error rates
- Resource utilization
- Cost trends

### 7. Set Up Alerts

Configure alerts for:
- High error rates
- High latency
- Resource exhaustion
- Cost thresholds

## Troubleshooting

### Traces Not Appearing

1. Check OTLP endpoint configuration
2. Verify Tempo is running: `docker ps | grep tempo`
3. Check service logs for errors
4. Verify trace sampling is enabled

### Metrics Not Scraping

1. Check Prometheus targets: `http://localhost:9090/targets`
2. Verify `/metrics` endpoint is accessible
3. Check Prometheus configuration
4. Review service logs

### Logs Not Appearing

1. Check log level configuration
2. Verify log file permissions
3. Check disk space
4. Review logging service configuration

### Alerts Not Firing

1. Check alert rule syntax
2. Verify Alertmanager is running
3. Check notification channel configuration
4. Review Alertmanager logs

### High Latency

1. Check trace spans for bottlenecks
2. Review metrics for resource constraints
3. Check database query performance
4. Review external API calls

### High Error Rate

1. Check error logs for patterns
2. Review trace spans for errors
3. Check system resource utilization
4. Review recent deployments

## Related Documentation

- [Structured Logging](./STRUCTURED_LOGGING.md)
- [Alerting Setup](./ALERTING_SETUP.md)
- [Cost Tracking](./COST_TRACKING.md)
- [Audit Logging](./AUDIT_LOGGING.md)
- [Staging Deployment](./STAGING_DEPLOYMENT.md)

## Quick Reference

### Service Endpoints

- **Grafana**: `http://localhost:3000`
- **Prometheus**: `http://localhost:9090`
- **Alertmanager**: `http://localhost:9093`
- **Tempo**: `http://localhost:3200`

### Default Credentials

- **Grafana**: `admin/admin` (change in production)
- **Prometheus**: No authentication (add in production)
- **Alertmanager**: No authentication (add in production)

### Environment Variables

```bash
# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317
OTEL_SERVICE_NAME=my-service

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Metrics
METRICS_ENABLED=true
METRICS_PORT=9090
```

## Support

For issues or questions:
1. Check this documentation
2. Review service logs
3. Check Grafana dashboards
4. Review Prometheus alerts
5. Contact the platform team

