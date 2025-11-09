# Observability Quick Start

Quick reference guide for getting started with observability in the SWE Platform.

## Prerequisites

- Docker and Docker Compose installed
- Access to the staging environment

## Starting Observability Stack

```bash
# Start all observability services
docker-compose -f docker-compose.staging.yml up -d prometheus grafana alertmanager tempo

# Verify services are running
docker ps | grep -E 'prometheus|grafana|alertmanager|tempo'
```

## Accessing Dashboards

### Grafana

1. Navigate to: `http://localhost:3000`
2. Login with: `admin/admin`
3. Change password when prompted
4. Explore dashboards:
   - System Overview
   - HTTP Metrics
   - LLM Providers
   - Tool Execution
   - Traces

### Prometheus

1. Navigate to: `http://localhost:9090`
2. Query metrics using PromQL:
   ```
   rate(http_requests_total[5m])
   histogram_quantile(0.95, http_request_duration_seconds_bucket)
   ```

### Alertmanager

1. Navigate to: `http://localhost:9093`
2. View active alerts
3. Check notification status

## Common Queries

### Request Rate

```promql
rate(http_requests_total[5m])
```

### Error Rate

```promql
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

### P95 Latency

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### LLM Cost

```promql
sum(rate(llm_provider_cost_usd_total[1h])) * 24
```

## Viewing Traces

1. Open Grafana
2. Navigate to "Traces" dashboard
3. Select a service
4. Click on a trace to view details

## Setting Up Alerts

1. Edit `infrastructure/prometheus/alerts.yml`
2. Add alert rules
3. Reload Prometheus: `docker-compose restart prometheus`
4. Configure notification channels in `infrastructure/alertmanager/alertmanager.yml`

## Logging

### View Logs

```bash
# Application logs
docker-compose logs -f api

# Tool service logs
docker-compose logs -f tool-service

# All logs
docker-compose logs -f
```

### Log Levels

Set log level via environment variable:
```bash
LOG_LEVEL=debug docker-compose up
```

## Cost Tracking

### View Costs

```bash
# Get cost summary
curl http://localhost:8000/api/v1/costs/summary?days=7

# Get cost entries
curl http://localhost:8000/api/v1/costs/entries?limit=100
```

## Audit Logs

### Query Audit Logs

```bash
# Get audit logs
curl http://localhost:8000/api/v1/audit/logs?limit=100

# Get audit summary
curl http://localhost:8000/api/v1/audit/summary?days=7
```

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs prometheus grafana alertmanager

# Check ports
netstat -an | grep -E '3000|9090|9093|4317'
```

### Metrics Not Appearing

1. Check Prometheus targets: `http://localhost:9090/targets`
2. Verify `/metrics` endpoints are accessible
3. Check service logs for errors

### Traces Not Appearing

1. Check Tempo is running: `docker ps | grep tempo`
2. Verify OTLP endpoint configuration
3. Check service logs for errors

## Next Steps

- Read [Observability Guide](./OBSERVABILITY.md) for detailed documentation
- Review [Structured Logging](./STRUCTURED_LOGGING.md)
- Check [Alerting Setup](./ALERTING_SETUP.md)
- Explore [Cost Tracking](./COST_TRACKING.md)
- Review [Audit Logging](./AUDIT_LOGGING.md)

