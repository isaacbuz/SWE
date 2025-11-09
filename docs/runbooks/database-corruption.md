# Runbook: Database Corruption

## Overview

This runbook covers the procedure for recovering from database corruption.

## Symptoms

- Database errors in application logs
- Data inconsistencies reported
- Application failures
- PostgreSQL errors (corruption, checksum failures)

## Prerequisites

- Access to backup storage
- Database restore script
- Database credentials
- Maintenance window (if possible)

## Recovery Procedure

### Step 1: Identify Corruption

```bash
# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql.log

# Check for corruption errors
psql -h localhost -U swe_user -d swe_db -c "SELECT * FROM pg_stat_database WHERE datname = 'swe_db';"
```

### Step 2: Stop Application

```bash
# Stop application services
docker-compose stop api tool-service

# Or for systemd
systemctl stop swe-api
```

### Step 3: Identify Last Good Backup

```bash
# List available backups
ls -lh /var/backups/postgresql/

# Find latest backup
find /var/backups/postgresql -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1
```

### Step 4: Restore Database

```bash
# Restore from backup
./scripts/db/restore-database.sh /var/backups/postgresql/swe_db_20251109_020000.sql.gz
```

### Step 5: Verify Data Integrity

```bash
# Check table count
psql -h localhost -U swe_user -d swe_db -c "SELECT COUNT(*) FROM information_schema.tables;"

# Check data counts
psql -h localhost -U swe_user -d swe_db -c "SELECT COUNT(*) FROM auth.users;"
psql -h localhost -U swe_user -d swe_db -c "SELECT COUNT(*) FROM agents.agent_definitions;"
```

### Step 6: Restart Application

```bash
# Start application services
docker-compose start api tool-service

# Or for systemd
systemctl start swe-api
```

### Step 7: Monitor

```bash
# Monitor application logs
docker-compose logs -f api

# Check health endpoint
curl http://localhost:8000/health
```

## Verification

- [ ] Database restored successfully
- [ ] Data integrity verified
- [ ] Application services running
- [ ] Health checks passing
- [ ] No errors in logs

## Post-Recovery

1. Document incident
2. Investigate root cause
3. Update backup procedures if needed
4. Schedule post-mortem

## Related Scripts

- `scripts/db/restore-database.sh`
- `scripts/dr/test-backup-restore.sh`

