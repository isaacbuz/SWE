# Database Backup Guide

This guide covers database backup configuration, scheduling, and restoration for the SWE Platform.

## Overview

The database backup system provides:
- **Automated Backups**: Scheduled daily backups
- **Multiple Storage Options**: Local, S3, GCS
- **Compression**: Gzip compression to save space
- **Retention Policies**: Configurable retention periods
- **Point-in-Time Recovery**: WAL archiving for PITR
- **Monitoring**: Backup verification and alerts

## Quick Start

### 1. Configure Environment Variables

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=swe_db
export DB_USER=swe_user
export DB_PASSWORD=your_password
export BACKUP_DIR=/var/backups/postgresql
export RETENTION_DAYS=30
```

### 2. Run Manual Backup

```bash
# Make scripts executable
chmod +x scripts/db/backup-database.sh
chmod +x scripts/db/restore-database.sh

# Create backup
./scripts/db/backup-database.sh
```

### 3. Set Up Automated Backups

```bash
# Install cron job
./scripts/db/schedule-backups.sh install

# List scheduled backups
./scripts/db/schedule-backups.sh list
```

## Backup Scripts

### backup-database.sh

Creates a PostgreSQL database backup.

**Usage**:
```bash
./scripts/db/backup-database.sh
```

**Environment Variables**:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: swe_db)
- `DB_USER`: Database user (default: swe_user)
- `DB_PASSWORD`: Database password
- `BACKUP_DIR`: Backup directory (default: /var/backups/postgresql)
- `RETENTION_DAYS`: Retention period in days (default: 30)
- `COMPRESSION`: Compression method (default: gzip)
- `S3_BUCKET`: S3 bucket for upload (optional)
- `S3_PREFIX`: S3 prefix (default: postgresql-backups/)

**Features**:
- Custom format backup (pg_dump -F c)
- Gzip compression
- S3 upload (optional)
- Automatic cleanup of old backups
- Backup verification

### restore-database.sh

Restores a PostgreSQL database from backup.

**Usage**:
```bash
./scripts/db/restore-database.sh <backup_file>
```

**Example**:
```bash
./scripts/db/restore-database.sh /var/backups/postgresql/swe_db_20251109_020000.sql.gz
```

**Warning**: This will drop and recreate the database!

### schedule-backups.sh

Manages automated backup scheduling.

**Usage**:
```bash
# Install cron job
./scripts/db/schedule-backups.sh install

# List cron jobs
./scripts/db/schedule-backups.sh list

# Remove cron job
./scripts/db/schedule-backups.sh remove
```

## Backup Types

### Full Backup

Complete database dump using `pg_dump`:
- Includes all data and schema
- Can be restored to any point
- Larger file size
- Recommended: Weekly

### Incremental Backup (WAL Archiving)

Write-Ahead Log (WAL) archiving for point-in-time recovery:
- Archives transaction logs
- Enables PITR
- Smaller storage footprint
- Requires continuous archiving

## Storage Options

### Local Storage

Backups stored on local filesystem:
```bash
export BACKUP_DIR=/var/backups/postgresql
```

**Pros**:
- Fast access
- No external dependencies
- Simple setup

**Cons**:
- Limited by disk space
- No off-site backup
- Single point of failure

### S3 Storage

Backups uploaded to AWS S3:
```bash
export S3_BUCKET=swe-platform-backups
export S3_PREFIX=postgresql-backups/
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

**Pros**:
- Off-site backup
- Scalable storage
- Durable and reliable

**Cons**:
- Requires AWS account
- Network dependency
- Potential costs

### Google Cloud Storage

Backups uploaded to GCS:
```bash
export GCS_BUCKET=swe-platform-backups
export GCS_PREFIX=postgresql-backups/
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Retention Policy

Configure retention in `infrastructure/db/backup-config.yml`:

```yaml
retention:
  days: 30      # Keep daily backups for 30 days
  weeks: 4      # Keep weekly backups for 4 weeks
  months: 12    # Keep monthly backups for 12 months
```

The backup script automatically cleans up old backups based on retention policy.

## Point-in-Time Recovery (PITR)

### Enable WAL Archiving

1. Update PostgreSQL configuration:
```conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /var/backups/postgresql/wal/%f && cp %p /var/backups/postgresql/wal/%f'
```

2. Create WAL archive directory:
```bash
mkdir -p /var/backups/postgresql/wal
chown postgres:postgres /var/backups/postgresql/wal
```

3. Restart PostgreSQL

### Restore to Point in Time

```bash
# Restore base backup
./scripts/db/restore-database.sh /var/backups/postgresql/base_backup.dump

# Create recovery.conf
cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /var/backups/postgresql/wal/%f %p'
recovery_target_time = '2025-11-09 14:30:00'
EOF

# Restart PostgreSQL
```

## Monitoring

### Backup Verification

The backup script automatically verifies backups:
- Checks file existence
- Verifies file size
- Validates backup format

### Alerts

Configure alerts for backup failures:
```bash
# Add to backup script
if [[ $? -ne 0 ]]; then
    echo "Backup failed" | mail -s "Database Backup Failed" admin@example.com
fi
```

### Monitoring Script

Create monitoring script to check backup status:
```bash
#!/bin/bash
# Check if backup exists from last 24 hours
if find /var/backups/postgresql -name "*.sql.gz" -mtime -1 | grep -q .; then
    echo "Backup exists"
else
    echo "WARNING: No recent backup found"
fi
```

## Best Practices

1. **Regular Backups**: Schedule daily backups
2. **Off-Site Storage**: Use S3 or GCS for redundancy
3. **Test Restores**: Regularly test restore procedures
4. **Monitor Backups**: Set up alerts for failures
5. **Retention Policy**: Keep backups according to requirements
6. **Encryption**: Encrypt backups at rest
7. **Documentation**: Document restore procedures
8. **Automation**: Use cron/systemd for scheduling

## Troubleshooting

### Backup Fails

1. **Check Database Connection**:
   ```bash
   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;"
   ```

2. **Check Disk Space**:
   ```bash
   df -h $BACKUP_DIR
   ```

3. **Check Permissions**:
   ```bash
   ls -la $BACKUP_DIR
   ```

4. **Check Logs**:
   ```bash
   tail -f /var/log/db-backup.log
   ```

### Restore Fails

1. **Verify Backup File**:
   ```bash
   file /var/backups/postgresql/backup.dump.gz
   ```

2. **Check Database Access**:
   ```bash
   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1;"
   ```

3. **Check Disk Space**:
   ```bash
   df -h
   ```

### S3 Upload Fails

1. **Check AWS Credentials**:
   ```bash
   aws s3 ls s3://$S3_BUCKET
   ```

2. **Check Network Connectivity**:
   ```bash
   ping s3.amazonaws.com
   ```

3. **Check IAM Permissions**:
   Ensure IAM user has `s3:PutObject` permission

## Production Checklist

- [ ] Backup scripts tested
- [ ] Automated backups scheduled
- [ ] Retention policy configured
- [ ] Off-site storage configured (S3/GCS)
- [ ] Backup monitoring set up
- [ ] Restore procedure tested
- [ ] WAL archiving enabled (for PITR)
- [ ] Backup encryption configured
- [ ] Documentation updated
- [ ] Team trained on restore procedures

## Related Documentation

- [Staging Deployment](./STAGING_DEPLOYMENT.md)
- [Production Deployment](./PRODUCTION_DEPLOYMENT.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)

## Support

For issues:
1. Check troubleshooting section
2. Review backup logs
3. Verify database connectivity
4. Check disk space and permissions
5. Contact platform team

