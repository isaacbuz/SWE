# Infrastructure Setup Guide

This document covers the CI/CD pipelines, Docker configuration, and deployment setup for the AI-First SWE Company platform.

## Table of Contents

1. [CI/CD Pipelines](#cicd-pipelines)
2. [Docker Setup](#docker-setup)
3. [Local Development](#local-development)
4. [Deployment](#deployment)
5. [Security Considerations](#security-considerations)
6. [Troubleshooting](#troubleshooting)

---

## CI/CD Pipelines

### Overview

The project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline** (`.github/workflows/ci.yml`): Runs on all branches and PRs
- **CD Pipeline** (`.github/workflows/cd.yml`): Runs on merges to main and tags

### CI Pipeline (`.github/workflows/ci.yml`)

The CI pipeline includes 7 major jobs:

#### 1. **Lint & Format** (`lint`)
- **Trigger**: All branches and PRs
- **Tasks**:
  - ESLint checks for TypeScript/JavaScript
  - Prettier formatting validation
  - TypeScript type checking
- **Duration**: ~15 minutes
- **Failure**: Blocks PR merge

#### 2. **Security Scanning** (`security`)
- **Trigger**: All branches and PRs
- **Tasks**:
  - npm audit for JavaScript dependencies
  - OWASP Dependency-Check for full codebase
  - Trivy filesystem scanning
  - Vulnerability SARIF report upload
- **Duration**: ~20 minutes
- **Failure**: Non-blocking but uploads reports

#### 3. **Test & Coverage** (`test`)
- **Trigger**: All branches and PRs
- **Services**:
  - PostgreSQL 16 (test database)
  - Redis 7 (caching)
- **Tasks**:
  - Node.js tests with coverage reporting
  - Python API tests with pytest
  - Coverage threshold validation (minimum 80%)
  - Codecov upload
- **Duration**: ~30 minutes
- **Failure**: Blocks PR merge if coverage < 80%

#### 4. **Build Packages** (`build`)
- **Trigger**: Depends on lint, test
- **Tasks**:
  - Installs all dependencies
  - Runs Turbo build for all packages
  - Caches build artifacts
- **Duration**: ~30 minutes
- **Failure**: Blocks PR merge

#### 5. **Build & Scan Docker Images** (`build-docker`)
- **Trigger**: Depends on lint, test
- **Tasks**:
  - Multi-stage Docker build
  - GHA cache for layer caching
  - Trivy vulnerability scanning
  - Image push (only on main branch)
- **Duration**: ~40 minutes
- **Failure**: Non-blocking on PR, blocks on main

#### 6. **Integration Tests** (`integration-tests`)
- **Trigger**: Depends on build
- **Services**:
  - PostgreSQL 16
  - Redis 7
- **Tasks**:
  - API integration tests
  - End-to-end workflow tests
- **Duration**: ~30 minutes
- **Failure**: Blocks PR merge

#### 7. **Auto-Merge Ready PRs** (`auto-merge`)
- **Trigger**: All jobs pass
- **Conditions**:
  - PR must be approved OR
  - PR from dependabot[bot]
- **Merge Method**: Squash merge
- **Failure**: Does not block, just skips auto-merge

### CD Pipeline (`.github/workflows/cd.yml`)

Triggered on:
- Push to main branch
- Git tags matching `v*.*.*`

#### Deployment Environments

**Staging Environment:**
- Trigger: Merge to main (non-tag)
- Endpoint: `https://staging-api.example.com`
- Features:
  - Smoke tests post-deployment
  - Health checks
  - Database migrations

**Production Environment:**
- Trigger: Git tag `v*.*.*`
- Endpoint: `https://api.example.com`
- Features:
  - Pre-deployment safety checks
  - GPG tag verification
  - Backup creation
  - Health checks
  - Rollback on failure
  - Incident notification

#### Jobs in CD Pipeline

1. **Prepare** - Determine version and environment
2. **Build & Push** - Build and push Docker image
3. **Deploy Staging** - Deploy to staging environment
4. **Deploy Production** - Deploy to production
5. **Rollback** - Automatic rollback on failure
6. **Monitoring** - Post-deployment monitoring
7. **Summary** - Generate deployment report

### Environment Variables

All sensitive values are stored in GitHub Secrets, not in the repository:

**Required Secrets for CI/CD:**
```
GITHUB_TOKEN          # Automatic, provided by GitHub Actions
```

**Optional Secrets for CD:**
```
STAGING_DEPLOY_KEY    # SSH key for staging deployment
PROD_DEPLOY_KEY       # SSH key for production deployment
CODECOV_TOKEN         # Codecov integration token
```

### Caching Strategy

- **Node dependencies**: `pnpm install --frozen-lockfile` with pnpm cache
- **Python dependencies**: pip with Python cache
- **Build artifacts**: Turbo cache stored on GitHub (1-day retention)
- **Docker layers**: GitHub Actions cache for Docker (multi-stage builds)

### Coverage Requirements

- **Minimum Coverage**: 80% for all new code
- **Tool**: Codecov + Jest + pytest
- **Reporting**: Uploaded to Codecov for trend analysis

---

## Docker Setup

### Dockerfile Structure

The `Dockerfile` uses a multi-stage build approach:

```
Stage 1: Builder
- Python 3.11-slim base
- Installs build dependencies
- Creates virtual environment
- Installs Python packages

Stage 2: Runtime
- Python 3.11-slim base
- Copies venv from builder
- Non-root user (appuser)
- Health checks
- Minimal image size (~350-400MB)
```

### Key Features

1. **Multi-stage build** - Reduces final image size by 60%+
2. **Non-root user** - Security hardening
3. **Health checks** - Container orchestration ready
4. **Virtual environment** - Cleaner dependency management
5. **Layer caching** - Fast rebuilds during development

### Image Size Optimization

- Base image: python:3.11-slim (125MB)
- Dependencies: ~150-200MB
- Application code: ~10-30MB
- Total: ~300-400MB

### Docker Build Caching

The CI pipeline uses GitHub Actions cache for Docker builds:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

This provides significant speedup for subsequent builds.

---

## Local Development

### Prerequisites

- Docker & Docker Compose 2.0+
- Python 3.11+
- Node.js 18+
- pnpm 8.12+

### Quick Start

1. **Clone and setup:**
```bash
git clone https://github.com/your-org/ai-company.git
cd ai-company
cp .env.example .env
```

2. **Start services:**
```bash
docker-compose up -d
```

3. **Check health:**
```bash
# API
curl http://localhost:8000/health

# Temporal
curl http://localhost:8080

# PostgreSQL
psql -h localhost -U postgres -d ai_company_db

# Redis
redis-cli -p 6379 -a redis_password
```

### Docker Compose Services

#### PostgreSQL (Port 5432)
- **Image**: postgres:16-alpine
- **Database**: ai_company_db
- **User**: postgres / postgres (change in production)
- **Health Check**: Every 10s
- **Data Persistence**: postgres_data volume

#### Redis (Port 6379)
- **Image**: redis:7-alpine
- **Password**: redis_password (change in production)
- **Memory**: 512MB limit with LRU eviction
- **Persistence**: Enabled with AOF
- **Health Check**: Every 10s

#### Temporal (Port 7233, UI 8080)
- **Image**: temporalio/auto-setup:latest
- **Namespace**: default
- **Task Queue**: ai-company-tasks
- **UI**: http://localhost:8080
- **Database**: PostgreSQL (same instance)
- **Health Check**: Every 10s

#### API Service (Port 8000)
- **Build**: Local Dockerfile
- **Environment**: development
- **Debug**: Enabled
- **Log Level**: INFO
- **Health Check**: Every 10s
- **Resource Limits**: 1 CPU, 512MB RAM
- **Dependencies**: postgres, redis, temporal

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect ai_company_postgres_data

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres ai_company_db > backup.sql

# Restore PostgreSQL
docker-compose exec -T postgres psql -U postgres ai_company_db < backup.sql
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# View logs with timestamps
docker-compose logs -f --timestamps

# Filter logs
docker-compose logs -f api | grep ERROR
```

### Environment Configuration

All services read from `.env` file. Copy `.env.example` and customize:

```bash
cp .env.example .env
```

Key variables for development:
- `ENVIRONMENT=development`
- `DEBUG=true`
- `LOG_LEVEL=INFO`
- `DATABASE_URL=postgresql://...`
- `REDIS_URL=redis://...`

### Database Migrations

Database schema is initialized via `infrastructure/db/init.sql` on first start.

For subsequent migrations, use Alembic:
```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
```

### Scaling Services

Scale multiple API instances:
```bash
docker-compose up -d --scale api=3
```

This creates 3 API instances (port 8001, 8002, etc.) with a load balancer.

---

## Deployment

### Prerequisites for Deployment

1. **GitHub Secrets** configured with deployment keys
2. **Target environment** ready (Kubernetes, VPS, etc.)
3. **Domain names** configured (staging.example.com, api.example.com)
4. **Monitoring** setup (Datadog, New Relic, etc.)
5. **Backup strategy** documented

### Staging Deployment

Automatically triggered on every merge to `main`:

1. Builds and pushes Docker image
2. Deploys to staging environment
3. Runs smoke tests
4. Notifies deployment status

**Health Check Endpoint:**
```
GET https://staging-api.example.com/health
```

### Production Deployment

Manually triggered via Git tag:

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

This triggers:
1. Pre-deployment safety checks
2. Database backups
3. Blue-green deployment
4. Health checks post-deployment
5. Smoke tests
6. Automated rollback on failure

### Rollback Procedure

Automatic rollback is triggered if:
- Health checks fail post-deployment
- Smoke tests fail
- Critical errors detected

The system automatically:
1. Identifies previous stable version
2. Restores database from backup
3. Redeployment with previous version
4. Creates incident ticket

Manual rollback:
```bash
# Rollback to previous tag
git tag v1.0.1-rollback $(git describe --tags --abbrev=0 $(git rev-list --tags --skip=1 -n 1))
git push origin v1.0.1-rollback
```

### Monitoring Post-Deployment

The monitoring job checks:
- Application metrics (error rate, latency)
- Resource utilization (CPU, memory)
- Database connection pool
- External API health

Alerts trigger if:
- Error rate > 5%
- P95 latency > 1000ms
- CPU > 80%
- Memory > 85%

---

## Security Considerations

### Secrets Management

1. **Never commit `.env` files** - use `.env.example` template
2. **Store in GitHub Secrets** - all production credentials
3. **Rotate regularly** - implement rotation policy
4. **Audit access** - log all secret accesses
5. **Use service accounts** - not personal credentials

### Container Security

1. **Non-root user** - API runs as `appuser`
2. **Read-only filesystem** - where possible
3. **No privileged mode** - security_opt: no-new-privileges
4. **Network policies** - restrict inter-service communication
5. **Image scanning** - Trivy scans for vulnerabilities

### Pipeline Security

1. **OWASP Dependency Check** - scans all dependencies
2. **Trivy scanning** - filesystem and image scanning
3. **GPG verification** - production tags must be signed
4. **SARIF reporting** - vulnerability reports to GitHub Security
5. **Approval gates** - manual approval for production

### API Security

1. **HTTPS/TLS** - all external communication encrypted
2. **Rate limiting** - 100 requests per minute per IP
3. **CORS** - whitelist allowed origins
4. **JWT tokens** - 30-minute expiration
5. **API keys** - with expiration and rotation

### Database Security

1. **Encrypted connections** - PostgreSQL SSL in production
2. **User permissions** - minimal required access
3. **Audit logging** - all modifications logged
4. **Backups** - encrypted and tested
5. **Secrets** - never in connection strings

---

## Troubleshooting

### Common Issues

#### Services don't start
```bash
# Check Docker daemon
docker ps

# Check compose file syntax
docker-compose config

# Rebuild images
docker-compose build --no-cache

# Check port conflicts
lsof -i :8000
```

#### Database connection fails
```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready

# View PostgreSQL logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U postgres -d ai_company_db
```

#### Redis connection fails
```bash
# Check Redis health
docker-compose exec redis redis-cli ping

# Monitor Redis
docker-compose exec redis redis-cli monitor

# Check memory
docker-compose exec redis redis-cli info memory
```

#### API won't start
```bash
# Check logs
docker-compose logs api

# Rebuild and restart
docker-compose down api
docker-compose build --no-cache api
docker-compose up -d api

# Test health endpoint
curl http://localhost:8000/health
```

#### CI/CD failures

**Lint failures:**
```bash
# Auto-fix formatting
pnpm format

# Fix eslint issues
pnpm lint --fix
```

**Test failures:**
```bash
# Run tests locally
pnpm test

# Run with coverage
pnpm test --coverage
```

**Build failures:**
```bash
# Clean build
pnpm clean
pnpm build

# Check turbo logs
cat .turbo/turbo.log
```

### Performance Optimization

#### Slow database queries
```bash
# Enable query logging
docker-compose exec postgres psql -U postgres -d ai_company_db
# \timing on
# SELECT ...
```

#### High memory usage
```bash
# Check container memory
docker stats

# Limit container memory in docker-compose.yml
```

#### Slow Docker builds
```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Use layer caching
docker build --cache-from <image>

# Check GitHub Actions cache
gh actions-cache list
```

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Temporal Documentation](https://docs.temporal.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review this documentation
3. Check GitHub Actions logs
4. Contact DevOps team

---

**Last Updated**: November 2024
**Maintainers**: Infrastructure Team
**License**: MIT
