# Monitoring and Alerting Infrastructure

This directory contains the complete monitoring and alerting setup for the PieHr platform.

## Components

### Prometheus
- **Location**: `infrastructure/prometheus/`
- **Purpose**: Metrics collection and storage
- **Configuration**: `prometheus.yml`
- **Alerts**: `alerts.yml`

### Grafana
- **Location**: `infrastructure/grafana/`
- **Purpose**: Visualization and dashboards
- **Dashboards**: `grafana/dashboards/`
- **Provisioning**: `grafana/provisioning/`

### Alertmanager
- **Location**: `infrastructure/alertmanager/`
- **Purpose**: Alert routing and notification
- **Configuration**: `config.yml`

### Alert Manager (Python)
- **Location**: `infrastructure/alerts/`
- **Purpose**: Application-level alerting
- **File**: `alert_manager.py`
- **Rules**: `alerting_rules.yml`

## Setup

### Prerequisites

1. Kubernetes cluster
2. Prometheus Operator (optional, for easier management)
3. Grafana installed
4. Alertmanager installed

### Deploy Prometheus

```bash
kubectl apply -f infrastructure/prometheus/
```

### Deploy Grafana

```bash
kubectl apply -f infrastructure/grafana/
```

### Deploy Alertmanager

```bash
kubectl apply -f infrastructure/alertmanager/
```

## Dashboards

### Platform Overview
- System health metrics
- Request rates and latencies
- Error rates
- Resource utilization

### Agent Performance
- Agent execution metrics
- Success/failure rates
- Average execution time
- Cost per agent

### Cost Analytics
- LLM API costs
- Infrastructure costs
- Cost trends
- Budget alerts

### Quality Metrics
- Test coverage
- Code quality scores
- PR review metrics
- Deployment success rates

### System Health
- CPU/Memory usage
- Database connections
- Redis performance
- Network metrics

## Alert Rules

### Critical Alerts
- High error rate (>10 errors/sec for 5 minutes)
- High memory usage (>95% for 5 minutes)
- Database connection pool exhausted
- Service unavailable

### Warning Alerts
- High latency (P95 >2s for 10 minutes)
- High CPU usage (>90% for 10 minutes)
- Cost threshold exceeded
- Quality metrics degraded

## Notification Channels

### Email
- Configured via SMTP settings
- Used for critical and cost alerts

### Slack
- Webhook integration
- Separate channels for different alert types

### PagerDuty
- Critical alerts only
- Integration key required

### Webhooks
- Custom webhook endpoints
- For integration with other systems

## Metrics

### Application Metrics
- HTTP request duration
- Request count by status code
- Agent execution metrics
- LLM API costs
- Database query performance

### Infrastructure Metrics
- CPU/Memory usage
- Disk I/O
- Network traffic
- Pod status

### Business Metrics
- User activity
- Feature usage
- Cost per user
- Quality scores

## SLO/SLI Tracking

### Service Level Objectives
- Availability: 99.9%
- Latency: P95 <500ms
- Error rate: <0.1%

### Service Level Indicators
- Uptime percentage
- Request latency percentiles
- Error rate percentage

## Troubleshooting

### Prometheus Not Scraping
- Check service discovery configuration
- Verify pod labels match scrape config
- Check network policies

### Alerts Not Firing
- Verify alert rules syntax
- Check Prometheus evaluation interval
- Verify Alertmanager configuration

### Grafana Dashboards Not Loading
- Check datasource configuration
- Verify Prometheus connectivity
- Check dashboard JSON syntax

## Documentation

- [Prometheus Configuration](prometheus/README.md)
- [Grafana Dashboards](grafana/README.md)
- [Alert Rules](alerts/README.md)

