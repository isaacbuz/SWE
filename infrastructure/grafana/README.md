# Grafana Dashboards for SWE Platform

This directory contains Grafana dashboard configurations and provisioning files for monitoring the SWE Platform.

## Structure

```
infrastructure/grafana/
├── dashboards/              # Dashboard JSON files
│   ├── system-overview.json
│   ├── http-metrics.json
│   ├── llm-providers.json
│   ├── tool-execution.json
│   └── traces.json
├── provisioning/
│   ├── dashboards/
│   │   └── dashboard.yml   # Dashboard provisioning config
│   └── datasources/
│       ├── prometheus.yml  # Prometheus datasource config
│       └── tempo.yml        # Tempo/Jaeger datasource config
├── alert-rules.yml          # Prometheus alert rules
└── README.md               # This file
```

## Dashboards

### 1. System Overview
**File**: `dashboards/system-overview.json`

Comprehensive overview of system health:
- HTTP request rate and duration
- HTTP error rate
- LLM provider requests and latency
- LLM provider cost
- Tool executions
- Active connections
- Cache hit rate
- System metrics (CPU, memory)

### 2. HTTP Metrics
**File**: `dashboards/http-metrics.json`

Detailed HTTP/API metrics:
- Request rate by route
- Request duration percentiles (p50, p95, p99)
- Error rate by status code
- Requests by HTTP method
- Error rate by route (table)
- Request duration heatmap

### 3. LLM Provider Metrics
**File**: `dashboards/llm-providers.json`

LLM provider performance and cost:
- Request rate by provider
- Success vs error rate
- Latency by provider and model (p95)
- Token usage (prompt vs completion)
- Cost by provider and model
- Provider usage distribution
- Top models by request count

### 4. Tool Execution Metrics
**File**: `dashboards/tool-execution.json`

Tool execution performance:
- Tool execution rate
- Success vs error rate
- Execution duration (p95)
- Execution duration percentiles
- Top tools by execution count
- Error rate by tool
- Tool usage distribution

### 5. Distributed Traces
**File**: `dashboards/traces.json`

OpenTelemetry distributed traces:
- Trace service map
- Trace search and exploration
- Trace duration distribution
- Error rate by service

**Note**: Requires Tempo or Jaeger data source configured.

## Setup

### Using Docker Compose

1. Add Grafana service to `docker-compose.yml`:

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./infrastructure/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infrastructure/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    depends_on:
      - prometheus
```

2. Start services:

```bash
docker-compose up -d grafana prometheus
```

3. Access Grafana:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin` (change in production!)

### Manual Setup

1. Install Grafana: https://grafana.com/docs/grafana/latest/setup-grafana/installation/

2. Copy dashboard files:
   ```bash
   cp -r infrastructure/grafana/dashboards /etc/grafana/provisioning/dashboards
   cp -r infrastructure/grafana/provisioning /etc/grafana/provisioning
   ```

3. Restart Grafana:
   ```bash
   systemctl restart grafana-server
   ```

## Data Sources

### Prometheus

Prometheus datasource is automatically configured via `provisioning/datasources/prometheus.yml`.

**URL**: `http://prometheus:9090` (adjust for your setup)

### Tempo/Jaeger

Tempo datasource is configured via `provisioning/datasources/tempo.yml`.

**URL**: `http://tempo:3200` (adjust for your setup)

**Note**: You need to have Tempo or Jaeger running to view traces.

## Alert Rules

Alert rules are defined in `alert-rules.yml`. To use them:

1. Configure Prometheus to load alert rules:
   ```yaml
   # prometheus.yml
   rule_files:
     - "/etc/prometheus/alerts/*.yml"
   ```

2. Copy alert rules:
   ```bash
   cp infrastructure/grafana/alert-rules.yml /etc/prometheus/alerts/swe-platform.yml
   ```

3. Reload Prometheus:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   ```

### Available Alerts

- **HighErrorRate**: HTTP error rate > 10 errors/sec
- **HighLatency**: p95 HTTP latency > 2s
- **LLMProviderErrors**: LLM provider error rate > 5 errors/sec
- **HighLLMCost**: LLM cost > $10/hour
- **ToolExecutionErrors**: Tool execution error rate > 5 errors/sec
- **LowCacheHitRate**: Cache hit rate < 50%
- **HighActiveConnections**: Active connections > 1000

## Customization

### Adding New Dashboards

1. Create dashboard JSON file in `dashboards/`
2. Dashboard will be automatically loaded by Grafana

### Modifying Dashboards

1. Edit dashboard JSON files directly
2. Or use Grafana UI and export updated JSON
3. Save to `dashboards/` directory

### Adding Alert Rules

1. Add new rules to `alert-rules.yml`
2. Reload Prometheus configuration

## Troubleshooting

### Dashboards Not Appearing

1. Check Grafana logs:
   ```bash
   docker logs grafana
   ```

2. Verify dashboard files are in correct location
3. Check dashboard provisioning config in Grafana UI: Configuration → Provisioning → Dashboards

### Metrics Not Showing

1. Verify Prometheus is scraping `/metrics` endpoint
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify metric names match dashboard queries

### Traces Not Showing

1. Verify Tempo/Jaeger is running
2. Check Tempo datasource configuration in Grafana
3. Verify OpenTelemetry is exporting traces to Tempo

## Related Documentation

- [Prometheus Metrics Collection](../README.md#prometheus)
- [OpenTelemetry Tracing](../README.md#opentelemetry)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)

