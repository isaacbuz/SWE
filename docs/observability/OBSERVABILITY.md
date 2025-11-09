# Observability & Monitoring Guide

Complete guide to monitoring, logging, tracing, and alerting for the SWE Platform.

## Overview

The platform includes comprehensive observability infrastructure:

- **OpenTelemetry Tracing**: Distributed tracing across all services
- **Prometheus Metrics**: Time-series metrics collection
- **Grafana Dashboards**: Visualization and monitoring
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Alerting**: Automated alerts for critical issues

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Application Services (API, Agents, Workflows)         │
│  └─> OpenTelemetry SDK                                  │
└─────────────────────────────────────────────────────────┘
                    │
                    ├─> Prometheus (Metrics)
                    ├─> OTLP Collector (Traces)
                    └─> Structured Logs
                    │
┌─────────────────────────────────────────────────────────┐
│  Observability Stack                                    │
│  ├─ Prometheus (Metrics Storage)                       │
│  ├─ Grafana (Visualization)                            │
│  ├─ Alertmanager (Alert Routing)                       │
│  └─ Jaeger/Tempo (Trace Storage)                       │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Start Observability Stack

```bash
# Start all services including observability
docker-compose up -d prometheus grafana alertmanager

# Access Grafana
open http://localhost:3001
# Default credentials: admin/admin

# Access Prometheus
open http://localhost:9090

# Access Alertmanager
open http://localhost:9093
```

## Metrics

### Available Metrics

#### HTTP Metrics
- `http_server_request_total` - Total HTTP requests
- `http_server_request_errors` - HTTP request errors
- `http_server_request_duration` - Request latency histogram

#### Agent Metrics
- `agent_execution_total` - Total agent executions
- `agent_execution_errors` - Agent execution errors
- `agent_execution_duration` - Execution duration histogram

#### LLM Metrics
- `llm_request_duration` - LLM request latency
- `llm_tokens_total` - Total tokens used
- `llm_cost_total` - Total costs in USD

#### Database Metrics
- `db_query_total` - Total database queries
- `db_query_duration` - Query duration histogram

#### Cache Metrics
- `cache_hits` - Cache hit count
- `cache_misses` - Cache miss count

### Querying Metrics

```promql
# Request rate
rate(http_server_request_total[5m])

# Error rate
rate(http_server_request_errors[5m]) / rate(http_server_request_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_server_request_duration_bucket[5m]))

# LLM cost per hour
rate(llm_cost_total[1h])

# Cache hit rate
rate(cache_hits[5m]) / (rate(cache_hits[5m]) + rate(cache_misses[5m]))
```

## Tracing

### Distributed Tracing

All services automatically generate traces with OpenTelemetry:

```python
from packages.observability.tracing import tracing

# Automatic tracing for FastAPI
tracing.setup()
tracing.instrument_fastapi(app)

# Custom spans
with tracing.create_span("my_operation", {"key": "value"}):
    # Your code here
    pass

# Agent execution tracing
@tracing.trace_agent_execution("CodegenAgent", "generate_code")
async def generate_code(self, prompt: str):
    # Automatically traced
    pass

# LLM call tracing
@tracing.trace_llm_call("gpt-4", "openai")
async def call_openai(self, prompt: str):
    # Automatically traced with token usage
    pass
```

### Viewing Traces

Traces are exported to OTLP endpoint (default: `http://localhost:4318`).

For local development, traces are also logged to console.

## Logging

### Structured Logging

All logs are in JSON format with correlation IDs:

```python
from packages.observability.logging import structured_logger

# Set correlation ID for request tracking
structured_logger.set_correlation_id()

# Log with context
structured_logger.info(
    "Processing request",
    user_id="user-123",
    project_id="project-456",
    action="create_issue"
)

# Agent activity logging
structured_logger.log_agent_activity(
    agent_name="CodegenAgent",
    action="generate_code",
    status="success",
    duration_ms=1234
)

# LLM call logging
structured_logger.log_llm_call(
    provider="openai",
    model="gpt-4",
    prompt_tokens=1000,
    completion_tokens=500,
    cost=0.01,
    duration_ms=800
)
```

### Log Format

```json
{
  "timestamp": "2025-11-08T12:00:00Z",
  "level": "INFO",
  "logger": "swe-platform",
  "message": "Processing request",
  "service": "swe-platform",
  "environment": "production",
  "correlation_id": "abc-123-def-456",
  "user_id": "user-123",
  "project_id": "project-456",
  "trace_id": "0123456789abcdef0123456789abcdef",
  "span_id": "0123456789abcdef",
  "file": "/app/api/main.py",
  "line": 42,
  "function": "process_request"
}
```

## Dashboards

### Platform Overview Dashboard

Access at: `http://localhost:3001/d/platform-overview`

**Panels:**
- Request Rate
- Error Rate
- P95 Latency
- LLM Cost Rate
- Agent Execution Rate
- Cache Hit Rate

### Creating Custom Dashboards

1. Access Grafana: `http://localhost:3001`
2. Create new dashboard
3. Add panels with Prometheus queries
4. Save dashboard JSON to `infrastructure/grafana/dashboards/`

## Alerting

### Alert Rules

Alert rules are defined in `infrastructure/prometheus/alerts.yml`:

- **HighErrorRate**: Error rate > 10%
- **HighLatency**: P95 latency > 1000ms
- **HighLLMCost**: Cost rate > $10/hour
- **AgentExecutionFailures**: Failure rate > 5%
- **ServiceDown**: Service unavailable > 2 minutes
- **DailyCostBudgetExceeded**: Daily cost > $100

### Alert Routing

Alerts are routed via Alertmanager:

- **Critical alerts** → Slack #alerts-critical + Webhook
- **Cost alerts** → Slack #alerts-cost + Email
- **Quality alerts** → Slack #alerts-quality

### Configuring Alert Channels

Edit `infrastructure/alertmanager/config.yml`:

```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - channel: '#your-alerts-channel'
        webhook_url: '${SLACK_WEBHOOK_URL}'
    email_configs:
      - to: 'alerts@yourcompany.com'
```

## Cost Tracking

### LLM Cost Monitoring

Costs are automatically tracked for all LLM calls:

```python
from packages.observability.metrics import metrics_collector

# Record LLM cost
metrics_collector.record_llm_request(
    provider="openai",
    model="gpt-4",
    duration_seconds=1.2,
    prompt_tokens=1000,
    completion_tokens=500,
    cost=0.01,
    status="success"
)
```

### Cost Queries

```promql
# Total cost today
sum(increase(llm_cost_total[24h]))

# Cost by provider
sum by (llm_provider) (rate(llm_cost_total[1h]))

# Cost by model
sum by (llm_model) (rate(llm_cost_total[1h]))
```

## Best Practices

### 1. Use Correlation IDs

Always set correlation IDs for request tracking:

```python
from packages.observability.logging import set_correlation_id

correlation_id = set_correlation_id()
# All logs in this request will include correlation_id
```

### 2. Add Custom Metrics

Create custom metrics for business logic:

```python
from packages.observability.metrics import metrics_collector

# Create custom counter
counter = metrics_collector.create_counter(
    name="custom.business.metric",
    description="Custom business metric"
)
counter.add(1, {"label": "value"})
```

### 3. Trace Critical Paths

Add tracing to critical operations:

```python
from packages.observability.tracing import trace_operation

@trace_operation("critical_operation", {"component": "api"})
async def critical_function():
    # Automatically traced
    pass
```

### 4. Monitor Key SLIs

Track Service Level Indicators:

- **Availability**: `up{job="api"}`
- **Latency**: `histogram_quantile(0.95, rate(http_server_request_duration_bucket[5m]))`
- **Error Rate**: `rate(http_server_request_errors[5m]) / rate(http_server_request_total[5m])`
- **Throughput**: `rate(http_server_request_total[5m])`

## Troubleshooting

### Metrics Not Appearing

1. Check Prometheus targets: `http://localhost:9090/targets`
2. Verify service exposes `/metrics` endpoint
3. Check Prometheus logs: `docker-compose logs prometheus`

### Traces Not Showing

1. Verify OTLP endpoint is accessible
2. Check trace exporter configuration
3. Review application logs for trace errors

### Alerts Not Firing

1. Check Alertmanager: `http://localhost:9093`
2. Verify alert rules are loaded: `http://localhost:9090/alerts`
3. Test alert routing: `http://localhost:9093/#/alerts`

## Production Considerations

### Retention

- **Metrics**: 30 days (configurable in Prometheus)
- **Traces**: 7 days (configurable in trace backend)
- **Logs**: 90 days (configurable in log aggregation)

### Scaling

- **Prometheus**: Use federation for multiple instances
- **Grafana**: Use read replicas for high availability
- **Alertmanager**: Use clustering for redundancy

### Security

- Use authentication for Grafana
- Secure Prometheus endpoints
- Encrypt alert webhook URLs
- Rotate API keys regularly

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

