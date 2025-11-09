# Runbook: Application Rollback

## Overview

This runbook covers the procedure for rolling back a failed application deployment.

## Symptoms

- Application errors after deployment
- Service degradation
- User complaints
- Increased error rates
- Health checks failing

## Prerequisites

- Previous version available
- Database backup (before rollback)
- Deployment access
- Rollback script

## Recovery Procedure

### Step 1: Identify Issue

```bash
# Check application logs
docker-compose logs -f api

# Check error rates
curl http://localhost:8000/metrics | grep error

# Check health endpoint
curl http://localhost:8000/health
```

### Step 2: Backup Current State

```bash
# Backup database
./scripts/db/backup-database.sh

# Export current configuration
docker-compose config > docker-compose-backup.yml
```

### Step 3: Identify Previous Version

```bash
# List available versions
git tag --sort=-v:refname | head -10

# Or check container registry
docker images | grep swe-platform
```

### Step 4: Rollback Application

```bash
# Using rollback script
./scripts/dr/rollback-application.sh v1.0.0

# Or manually
docker-compose pull
docker-compose up -d --force-recreate
```

### Step 5: Verify Rollback

```bash
# Check service status
docker-compose ps

# Check health endpoint
curl http://localhost:8000/health

# Monitor logs
docker-compose logs -f api
```

### Step 6: Monitor

```bash
# Monitor for 15 minutes
watch -n 5 'curl -s http://localhost:8000/health'

# Check error rates
curl http://localhost:8000/metrics | grep error_rate
```

## Verification

- [ ] Previous version deployed
- [ ] Services running
- [ ] Health checks passing
- [ ] Error rates decreased
- [ ] No new errors in logs

## Post-Recovery

1. Investigate root cause
2. Fix issue in development
3. Test fix thoroughly
4. Prepare new deployment
5. Schedule redeployment

## Related Scripts

- `scripts/dr/rollback-application.sh`
- `scripts/db/backup-database.sh`

