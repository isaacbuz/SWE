# Production Deployment Guide

This comprehensive guide covers all aspects of deploying the SWE Platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Setup](#environment-setup)
4. [Infrastructure Provisioning](#infrastructure-provisioning)
5. [Application Deployment](#application-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Access

- **Cloud Provider**: AWS/GCP/Azure account with appropriate permissions
- **Domain**: Domain name with DNS access
- **SSL Certificate**: Let's Encrypt or commercial certificate
- **GitHub**: Repository access with deployment keys
- **Secrets Management**: Access to secrets management system

### Required Tools

- Docker and Docker Compose
- kubectl (for Kubernetes deployments)
- terraform (for infrastructure as code)
- git
- curl or httpie
- SSL certificate management tools

### Required Knowledge

- Docker containerization
- Reverse proxy configuration (Nginx)
- Database administration (PostgreSQL)
- SSL/TLS configuration
- Monitoring and logging

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage ≥ 80%
- [ ] Security scans passed
- [ ] Performance tests passed
- [ ] Code review completed
- [ ] Documentation updated

### Infrastructure

- [ ] Cloud resources provisioned
- [ ] Database configured with backups
- [ ] Redis configured
- [ ] SSL certificates obtained
- [ ] DNS records configured
- [ ] Firewall rules configured
- [ ] Load balancer configured

### Security

- [ ] Secrets configured in secure storage
- [ ] Environment variables set
- [ ] Security headers configured
- [ ] Rate limiting configured
- [ ] Authentication configured
- [ ] Audit logging enabled

### Monitoring

- [ ] Monitoring tools configured
- [ ] Alerting rules configured
- [ ] Logging configured
- [ ] Dashboards created
- [ ] On-call rotation configured

---

## Environment Setup

### Environment Variables

**Required Variables**:

```bash
# Application
NODE_ENV=production
API_URL=https://api.example.com
WEB_URL=https://example.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://host:6379
REDIS_PASSWORD=secure_password

# Authentication
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRATION=24h
ENCRYPTION_KEY=your_encryption_key_here

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
COHERE_API_KEY=...
IBM_API_KEY=...

# External APIs
GITHUB_TOKEN=ghp_...
GOOGLE_WORKSPACE_CLIENT_ID=...
GOOGLE_WORKSPACE_CLIENT_SECRET=...

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
SENTRY_DSN=...

# Security
ALLOWED_ORIGINS=https://example.com
RATE_LIMIT_ENABLED=true
CSRF_ENABLED=true
```

### Secrets Management

**Using AWS Secrets Manager**:
```bash
aws secretsmanager create-secret \
  --name swe-platform/production \
  --secret-string file://secrets.json
```

**Using Environment Files**:
```bash
# Create .env.production
cp .env.example .env.production
# Edit with production values
# Store securely, never commit
```

---

## Infrastructure Provisioning

### Docker Compose Deployment

**Production Docker Compose** (`docker-compose.prod.yml`):

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/db/backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  tool-service:
    build:
      context: ./apps/tool-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - nginx_logs:/var/log/nginx
    depends_on:
      - api
      - tool-service
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  nginx_logs:
```

### Kubernetes Deployment

**Deployment Manifests** (`infrastructure/kubernetes/`):

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: swe-platform/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: swe-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

## Application Deployment

### Step 1: Build Images

```bash
# Build all images
docker-compose -f docker-compose.prod.yml build

# Or build individually
docker build -t swe-platform/api:latest ./apps/api
docker build -t swe-platform/tool-service:latest ./apps/tool-service
docker build -t swe-platform/web:latest ./apps/web
```

### Step 2: Run Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Or manually
docker exec -it swe-platform-api-1 python -m alembic upgrade head
```

### Step 3: Deploy Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Or start individually
docker-compose -f docker-compose.prod.yml up -d postgres redis
docker-compose -f docker-compose.prod.yml up -d api tool-service
docker-compose -f docker-compose.prod.yml up -d web nginx
```

### Step 4: Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api

# Health checks
curl https://api.example.com/health
curl https://example.com/health
```

---

## Post-Deployment Verification

### Health Checks

```bash
# API health
curl https://api.example.com/health

# Tool service health
curl https://api.example.com/api/v1/tools/health

# Database connectivity
docker exec -it swe-platform-postgres-1 psql -U swe_user -d swe_db -c "SELECT 1"

# Redis connectivity
docker exec -it swe-platform-redis-1 redis-cli ping
```

### Functional Tests

```bash
# Test authentication
curl -X POST https://api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Test API endpoints
curl https://api.example.com/api/v1/tools \
  -H "Authorization: Bearer $TOKEN"

# Test tool execution
curl -X POST https://api.example.com/api/v1/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"toolName":"test_tool","arguments":{}}'
```

### Performance Tests

```bash
# Run smoke test
./scripts/performance/run-load-tests.sh smoke

# Run load test
API_URL=https://api.example.com ./scripts/performance/run-load-tests.sh load
```

### Security Tests

```bash
# Run security audit
./scripts/security/security-audit.sh

# Run penetration tests
TARGET_URL=https://api.example.com ./scripts/security/penetration-test.sh
```

---

## Rollback Procedures

### Quick Rollback

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Deploy previous version
git checkout <previous-tag>
docker-compose -f docker-compose.prod.yml up -d

# Or use rollback script
./scripts/dr/rollback-application.sh
```

### Database Rollback

```bash
# Restore from backup
./scripts/db/restore-database.sh backup_file.sql.gz

# Or rollback migrations
docker exec -it swe-platform-api-1 python -m alembic downgrade -1
```

### Kubernetes Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/api

# Check rollback status
kubectl rollout status deployment/api
```

---

## Monitoring and Maintenance

### Monitoring Dashboards

- **Grafana**: http://grafana.example.com
- **Prometheus**: http://prometheus.example.com
- **Application Metrics**: http://api.example.com/metrics

### Key Metrics to Monitor

- **API Response Times**: p50, p95, p99
- **Error Rates**: 4xx, 5xx errors
- **Throughput**: Requests per second
- **Database Performance**: Query times, connections
- **Resource Usage**: CPU, memory, disk
- **Cost**: LLM provider costs, infrastructure costs

### Logs

```bash
# View API logs
docker-compose -f docker-compose.prod.yml logs -f api

# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Search logs
docker-compose -f docker-compose.prod.yml logs api | grep ERROR
```

### Maintenance Tasks

**Daily**:
- Review error logs
- Check monitoring dashboards
- Verify backups

**Weekly**:
- Review performance metrics
- Check security alerts
- Update dependencies

**Monthly**:
- Security audit
- Performance optimization
- Cost review
- Disaster recovery test

---

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs service-name

# Check resource usage
docker stats

# Check configuration
docker-compose -f docker-compose.prod.yml config
```

#### Database Connection Issues

```bash
# Test connection
docker exec -it swe-platform-postgres-1 psql -U swe_user -d swe_db

# Check connection pool
docker exec -it swe-platform-api-1 python -c "from sqlalchemy import create_engine; print(create_engine('$DATABASE_URL').pool.size())"
```

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Restart service
docker-compose -f docker-compose.prod.yml restart service-name

# Increase limits in docker-compose.prod.yml
```

#### SSL Certificate Issues

```bash
# Check certificate
openssl s_client -connect api.example.com:443

# Renew certificate
./scripts/ssl/renew-certificates.sh
```

### Emergency Procedures

**Service Down**:
1. Check health endpoints
2. Review logs
3. Check resource usage
4. Restart service
5. If persists, rollback

**Database Issues**:
1. Check database logs
2. Verify connectivity
3. Check disk space
4. Restore from backup if needed

**Security Incident**:
1. Isolate affected services
2. Review audit logs
3. Rotate credentials
4. Patch vulnerabilities
5. Notify security team

---

## Related Documentation

- [Staging Deployment](./STAGING_DEPLOYMENT.md)
- [SSL/TLS Setup](./SSL_TLS_SETUP.md)
- [Database Backups](./DATABASE_BACKUPS.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)
- [Security Audit](./SECURITY_AUDIT.md)
- [Performance Optimization](./PERFORMANCE_OPTIMIZATION.md)

---

## Support

For deployment issues:
1. Check this documentation
2. Review troubleshooting section
3. Check monitoring dashboards
4. Review logs
5. Contact platform team

