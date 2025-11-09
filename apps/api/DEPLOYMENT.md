# Deployment Guide

## Overview

This guide covers deploying the SWE Agent API to production environments.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Domain with SSL certificate
- Reverse proxy (nginx/Caddy)

## Environment Setup

### 1. Production Environment Variables

Create `.env` file with production settings:

```bash
# Application
APP_NAME="SWE Agent API"
APP_VERSION="1.0.0"
ENVIRONMENT=production
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=false
WORKERS=4  # CPU cores * 2 + 1

# Database (use connection pooling)
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/swe_agent
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://redis-host:6379/0

# JWT (use strong secrets!)
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# CORS (production domains only)
CORS_ORIGINS=["https://app.yourdomain.com","https://dashboard.yourdomain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2. Generate Secrets

```bash
# JWT Secret
openssl rand -hex 32

# General Secret Key
openssl rand -hex 32
```

## Deployment Options

### Option 1: Docker Deployment

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app
USER apiuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml**:

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/swe_agent
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:14-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=swe_agent
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**Build and Run**:

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale workers
docker-compose up -d --scale api=4
```

### Option 2: Systemd Service

**Service file** (`/etc/systemd/system/swe-api.service`):

```ini
[Unit]
Description=SWE Agent API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/swe-agent/api
Environment="PATH=/opt/swe-agent/api/venv/bin"
ExecStart=/opt/swe-agent/api/venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-config logging.json

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/swe-agent/api/logs

[Install]
WantedBy=multi-user.target
```

**Commands**:

```bash
# Enable and start
sudo systemctl enable swe-api
sudo systemctl start swe-api

# Status
sudo systemctl status swe-api

# Logs
sudo journalctl -u swe-api -f

# Restart
sudo systemctl restart swe-api
```

### Option 3: Kubernetes Deployment

**deployment.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swe-api
  labels:
    app: swe-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: swe-api
  template:
    metadata:
      labels:
        app: swe-api
    spec:
      containers:
        - name: api
          image: swe-agent/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: swe-api-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: swe-api-secrets
                  key: redis-url
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: swe-api-secrets
                  key: jwt-secret
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
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
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: swe-api-service
spec:
  selector:
    app: swe-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

## Reverse Proxy Configuration

### Nginx

```nginx
upstream swe_api {
    least_conn;
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy Configuration
    location / {
        proxy_pass http://swe_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /api/v1/ws/ {
        proxy_pass http://swe_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://swe_api;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/swe-agent/api/static/;
        expires 30d;
    }
}
```

### Caddy (simpler alternative)

```caddy
api.yourdomain.com {
    reverse_proxy localhost:8000 localhost:8001 localhost:8002 localhost:8003 {
        lb_policy least_conn
        health_uri /health
        health_interval 10s
    }

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
    }
}
```

## Database Setup

### PostgreSQL Initialization

```sql
-- Create database
CREATE DATABASE swe_agent;

-- Create user
CREATE USER swe_api WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE swe_agent TO swe_api;

-- Connect to database
\c swe_agent

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Run Migrations

```bash
# If using Alembic
alembic upgrade head
```

## Monitoring

### Health Checks

```bash
# Basic health check
curl https://api.yourdomain.com/health

# Detailed monitoring
curl https://api.yourdomain.com/api/v1/analytics/performance
```

### Logging

**Structured JSON logs**:

```bash
# View logs
tail -f /var/log/swe-api/access.log

# Search logs
cat /var/log/swe-api/access.log | jq '. | select(.level=="ERROR")'
```

### Metrics (Prometheus)

Add Prometheus metrics endpoint:

```python
from prometheus_fastapi_instrumentator import Instrumentator

# In main.py
Instrumentator().instrument(app).expose(app)
```

## Performance Tuning

### Worker Configuration

```bash
# Calculate optimal workers
workers = (2 * CPU_cores) + 1

# For 4 CPU cores
workers = 9
```

### Database Connection Pool

```python
DATABASE_POOL_SIZE = 50  # Total connections
DATABASE_MAX_OVERFLOW = 20  # Extra connections when pool full
```

### Redis Configuration

```bash
# Redis maxmemory
maxmemory 2gb
maxmemory-policy allkeys-lru
```

## Security Checklist

- [ ] Use HTTPS/TLS everywhere
- [ ] Strong JWT secrets (32+ bytes)
- [ ] Environment variables for secrets
- [ ] Database credentials rotation
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers set
- [ ] Firewall rules configured
- [ ] Regular dependency updates
- [ ] Log sensitive data excluded
- [ ] API key rotation policy
- [ ] Database backups automated

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -h localhost -U swe_api swe_agent | gzip > /backups/swe_agent_$DATE.sql.gz

# Retain last 7 days
find /backups -name "swe_agent_*.sql.gz" -mtime +7 -delete
```

### Configuration Backups

```bash
# Backup environment and configs
tar -czf /backups/config_$DATE.tar.gz .env config/
```

## Rollback Procedure

```bash
# Docker
docker-compose pull  # Get previous image
docker-compose up -d

# Systemd
sudo systemctl stop swe-api
cd /opt/swe-agent/api
git checkout <previous-tag>
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start swe-api

# Database rollback
alembic downgrade -1
```

## Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 https://api.yourdomain.com/health

# Using k6
k6 run load-test.js
```

## Troubleshooting

### High CPU Usage

```bash
# Check worker count
ps aux | grep uvicorn

# Monitor with htop
htop -p $(pgrep -d',' uvicorn)
```

### Memory Leaks

```bash
# Monitor memory
watch -n 1 'ps aux | grep uvicorn'

# Restart workers periodically
gunicorn --max-requests 1000 --max-requests-jitter 50
```

### Database Connection Pool Exhausted

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'swe_agent';

-- Increase pool size
DATABASE_POOL_SIZE=100
```

## Maintenance

### Zero-Downtime Deployment

```bash
# Rolling update (Kubernetes)
kubectl rollout restart deployment/swe-api

# Blue-Green (Docker)
docker-compose -f docker-compose.blue.yml up -d
# Test
docker-compose -f docker-compose.green.yml down
```

### Database Migration

```bash
# Backup first!
pg_dump swe_agent > backup.sql

# Run migration
alembic upgrade head

# Verify
alembic current
```

## Support

For issues, check:

1. Application logs
2. Database logs
3. Redis logs
4. Nginx/Caddy logs
5. System metrics
