# Staging Environment Deployment Guide

This guide covers deploying the SWE Platform to a staging environment.

## Prerequisites

- Docker and Docker Compose installed
- Access to staging server or local machine
- Environment variables configured (see `.env.staging.example`)

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.staging.example .env.staging
   ```

2. **Update `.env.staging` with your staging configuration:**
   - Database credentials
   - Redis password
   - Secret keys
   - API URLs
   - Grafana password

3. **Deploy to staging:**
   ```bash
   ./scripts/deploy-staging.sh --build
   ```

## Deployment Options

### Initial Deployment

```bash
# Build and start all services
./scripts/deploy-staging.sh --build
```

### Restart Services

```bash
# Stop and restart all services
./scripts/deploy-staging.sh --restart
```

### Manual Deployment

```bash
# Build images
docker-compose -f docker-compose.staging.yml build

# Start services
docker-compose -f docker-compose.staging.yml up -d

# View logs
docker-compose -f docker-compose.staging.yml logs -f

# Stop services
docker-compose -f docker-compose.staging.yml down
```

## Service URLs

After deployment, services are available at:

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Tool Service**: http://localhost:3001
- **Web Frontend**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (default port, adjust if needed)

## Health Checks

All services include health check endpoints:

- **API**: `GET /health`
- **Tool Service**: `GET /health`
- **Prometheus**: `GET /-/healthy`
- **Grafana**: `GET /api/health`

## Monitoring

### Prometheus Metrics

Prometheus automatically scrapes metrics from:
- API service (`/metrics` endpoint)
- Tool service (`/metrics` endpoint)

Access Prometheus UI: http://localhost:9090

### Grafana Dashboards

Grafana is pre-configured with:
- System Overview dashboard
- HTTP Metrics dashboard
- LLM Provider Metrics dashboard
- Tool Execution Metrics dashboard
- Distributed Traces dashboard

Access Grafana: http://localhost:3000
- Username: `admin`
- Password: (from `.env.staging`)

## Environment Variables

Key environment variables for staging:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `staging` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DB_PASSWORD` | PostgreSQL password | (required) |
| `REDIS_PASSWORD` | Redis password | (required) |
| `SECRET_KEY` | JWT secret key | (required) |
| `GRAFANA_PASSWORD` | Grafana admin password | (required) |
| `ALLOWED_ORIGINS` | CORS allowed origins | (required) |

## Troubleshooting

### Services Not Starting

1. Check logs:
   ```bash
   docker-compose -f docker-compose.staging.yml logs [service-name]
   ```

2. Verify environment variables:
   ```bash
   docker-compose -f docker-compose.staging.yml config
   ```

3. Check service health:
   ```bash
   docker-compose -f docker-compose.staging.yml ps
   ```

### Database Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   docker-compose -f docker-compose.staging.yml ps postgres
   ```

2. Check database logs:
   ```bash
   docker-compose -f docker-compose.staging.yml logs postgres
   ```

3. Test connection:
   ```bash
   docker-compose -f docker-compose.staging.yml exec postgres psql -U swe_user -d swe_platform_staging
   ```

### Metrics Not Appearing

1. Verify Prometheus is scraping:
   - Open http://localhost:9090/targets
   - Check all targets are "UP"

2. Check API metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics
   ```

3. Verify Prometheus configuration:
   ```bash
   docker-compose -f docker-compose.staging.yml exec prometheus cat /etc/prometheus/prometheus.yml
   ```

### Grafana Dashboards Not Loading

1. Check Grafana logs:
   ```bash
   docker-compose -f docker-compose.staging.yml logs grafana
   ```

2. Verify dashboard files are mounted:
   ```bash
   docker-compose -f docker-compose.staging.yml exec grafana ls /etc/grafana/provisioning/dashboards
   ```

3. Check datasource configuration:
   - Login to Grafana
   - Go to Configuration → Data Sources
   - Verify Prometheus is configured

## Updating Services

### Update API Service

```bash
# Rebuild and restart API
docker-compose -f docker-compose.staging.yml up -d --build api
```

### Update All Services

```bash
# Rebuild and restart all services
./scripts/deploy-staging.sh --build --restart
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.staging.yml exec postgres pg_dump -U swe_user swe_platform_staging > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose -f docker-compose.staging.yml exec -T postgres psql -U swe_user swe_platform_staging < backup.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v swe-platform-staging_postgres_staging_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Security Considerations

1. **Change Default Passwords**: Update all default passwords in `.env.staging`
2. **Use Strong Secret Keys**: Generate strong random keys for `SECRET_KEY`
3. **Restrict Network Access**: Use firewall rules to restrict access to staging
4. **Enable SSL/TLS**: Use reverse proxy (Nginx/Traefik) with SSL certificates
5. **Regular Updates**: Keep Docker images and dependencies updated
6. **Monitor Logs**: Regularly review logs for security issues

## Production Readiness Checklist

Before deploying to production:

- [ ] All environment variables configured
- [ ] Strong passwords and secret keys set
- [ ] SSL/TLS certificates configured
- [ ] Database backups configured
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up
- [ ] Security audit completed
- [ ] Load testing completed
- [ ] Disaster recovery plan documented

## Related Documentation

- [Deployment Guide](../DEPLOYMENT.md)
- [Production Deployment](../docs/PRODUCTION_DEPLOYMENT.md)
- [Monitoring Setup](../infrastructure/grafana/README.md)
- [API Documentation](../apps/api/README.md)

