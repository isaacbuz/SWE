# Alerting System Setup Guide

This guide covers setting up the alerting system using Prometheus Alertmanager.

## Overview

The alerting system provides:
- **Prometheus Alert Rules**: Define alert conditions
- **Alertmanager**: Routes alerts to notification channels
- **Multiple Channels**: Slack, Email, PagerDuty support
- **Alert Grouping**: Groups related alerts together
- **Inhibition Rules**: Suppresses redundant alerts

## Architecture

```
Prometheus → Alert Rules → Alertmanager → Notification Channels
                                      ├── Slack
                                      ├── Email
                                      └── PagerDuty
```

## Components

### 1. Prometheus Alert Rules

**Location**: `infrastructure/prometheus/alerts.yml`

Defines alert conditions:
- HTTP error rate and latency
- LLM provider errors and cost
- Tool execution errors
- System health (CPU, memory, connections)
- Service availability

### 2. Alertmanager Configuration

**Location**: `infrastructure/alertmanager/alertmanager.yml`

Routes alerts to appropriate channels:
- **Critical**: Slack + Email + PagerDuty
- **Warning**: Slack
- **Info**: Email

## Setup

### 1. Configure Notification Channels

Update `.env.staging` with notification settings:

```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM=alerts@example.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=alerts@example.com

# PagerDuty (optional)
PAGERDUTY_SERVICE_KEY=your-pagerduty-key
```

### 2. Deploy Alertmanager

Alertmanager is included in `docker-compose.staging.yml`:

```bash
docker-compose -f docker-compose.staging.yml up -d alertmanager
```

### 3. Verify Configuration

Check Alertmanager UI:
- URL: http://localhost:9093
- Status: http://localhost:9093/api/v1/status

## Alert Rules

### HTTP Metrics

- **HighErrorRate**: Error rate > 10 errors/sec (warning)
- **CriticalErrorRate**: Error rate > 50 errors/sec (critical)
- **HighLatency**: p95 latency > 2s (warning)
- **CriticalLatency**: p95 latency > 5s (critical)

### LLM Provider Metrics

- **LLMProviderErrors**: Error rate > 5 errors/sec (warning)
- **LLMProviderDown**: Error rate > 20 errors/sec (critical)
- **HighLLMCost**: Cost > $10/hour (warning)
- **ExcessiveLLMCost**: Cost > $50/hour (critical)

### Tool Execution Metrics

- **ToolExecutionErrors**: Error rate > 5 errors/sec (warning)
- **ToolExecutionFailure**: Error rate > 20 errors/sec (critical)

### System Health

- **LowCacheHitRate**: Hit rate < 50% (info)
- **HighActiveConnections**: Connections > 1000 (warning)
- **ExcessiveConnections**: Connections > 5000 (critical)
- **HighMemoryUsage**: Memory > 1.5GB (warning)
- **HighCPUUsage**: CPU > 80% (warning)

### Service Availability

- **ServiceDown**: Service unavailable for > 2 minutes (critical)

## Notification Channels

### Slack

1. Create Slack App: https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Create webhook URL
4. Add to `.env.staging`:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

### Email

1. Configure SMTP settings in `.env.staging`
2. For Gmail, use App Password:
   - Enable 2FA
   - Generate App Password
   - Use as `SMTP_PASSWORD`

### PagerDuty

1. Create PagerDuty service
2. Get integration key
3. Add to `alertmanager.yml`:
   ```yaml
   pagerduty_configs:
     - service_key: '${PAGERDUTY_SERVICE_KEY}'
   ```

## Alert Routing

Alerts are routed based on severity:

- **Critical**: All channels (Slack, Email, PagerDuty)
- **Warning**: Slack only
- **Info**: Email only

## Alert Grouping

Alerts are grouped by:
- `alertname`
- `cluster`
- `service`

This prevents alert spam for related issues.

## Inhibition Rules

Inhibition rules suppress redundant alerts:

- Warning alerts suppressed when critical alerts are firing
- Info alerts suppressed when warning or critical alerts are firing

## Testing Alerts

### Test Alert Rule

Create a test alert in Prometheus:

```yaml
- alert: TestAlert
  expr: vector(1)
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Test alert"
    description: "This is a test alert"
```

### Trigger Test Alert

```bash
# Restart Prometheus to reload rules
docker-compose -f docker-compose.staging.yml restart prometheus

# Check Alertmanager UI for alert
open http://localhost:9093
```

## Monitoring Alerts

### Alertmanager UI

- **URL**: http://localhost:9093
- **Features**:
  - View active alerts
  - View alert history
  - Test notification channels
  - View alert routing

### Grafana Integration

Grafana can display alerts:
1. Add Alertmanager as data source
2. Create alert panels
3. View alert history

## Troubleshooting

### Alerts Not Firing

1. Check Prometheus alert rules:
   ```bash
   docker-compose -f docker-compose.staging.yml exec prometheus promtool check rules /etc/prometheus/alerts/swe-platform.yml
   ```

2. Verify metrics exist:
   ```bash
   curl http://localhost:9090/api/v1/query?query=swe_platform_http_request_errors_total
   ```

3. Check Alertmanager logs:
   ```bash
   docker-compose -f docker-compose.staging.yml logs alertmanager
   ```

### Notifications Not Sending

1. Check Alertmanager configuration:
   ```bash
   docker-compose -f docker-compose.staging.yml exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
   ```

2. Verify notification channels:
   - Test Slack webhook URL
   - Test SMTP settings
   - Check PagerDuty integration

3. Check Alertmanager UI:
   - View notification status
   - Check for errors

### Too Many Alerts

1. Adjust alert thresholds in `alerts.yml`
2. Increase `group_interval` in `alertmanager.yml`
3. Add more inhibition rules
4. Adjust `repeat_interval`

## Best Practices

1. **Set Appropriate Thresholds**: Base thresholds on actual system behavior
2. **Use Alert Grouping**: Group related alerts to prevent spam
3. **Test Alerts**: Regularly test alert rules and notifications
4. **Document Alerts**: Document what each alert means and how to respond
5. **Review Regularly**: Review alert effectiveness and adjust as needed

## Related Documentation

- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Grafana Dashboards](../infrastructure/grafana/README.md)
- [Staging Deployment](./STAGING_DEPLOYMENT.md)

