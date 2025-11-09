# Disaster Recovery Plan

This document outlines the disaster recovery plan for the SWE Platform, including recovery procedures, objectives, and runbooks.

## Overview

The disaster recovery plan ensures business continuity and data protection in the event of system failures, data loss, or catastrophic events.

## Recovery Objectives

### Recovery Time Objectives (RTO)

| Component | RTO | Description |
|-----------|-----|-------------|
| Database | 15 minutes | Point-in-time restore from backups |
| Application | 5 minutes | Rollback to previous version |
| Infrastructure | 1 hour | Rebuild from Terraform/IaC |
| Full System | 2 hours | Complete system recovery |

### Recovery Point Objectives (RPO)

| Component | RPO | Description |
|-----------|-----|-------------|
| Database | 1 hour | Maximum data loss acceptable |
| Application State | 5 minutes | In-memory state loss acceptable |
| Configuration | 0 minutes | Configuration changes tracked in Git |

## Backup Strategy

### Database Backups

**Frequency**: Daily at 2 AM UTC  
**Retention**: 30 days  
**Storage**: Local + S3/GCS  
**Type**: Full backups + WAL archiving for PITR

**Backup Locations**:
- Local: `/var/backups/postgresql`
- S3: `s3://swe-platform-backups/postgresql-backups/`
- GCS: `gs://swe-platform-backups/postgresql-backups/`

### Application Backups

**Docker Images**: Stored in container registry  
**Configuration**: Version controlled in Git  
**Secrets**: Stored in secret management system

### Infrastructure Backups

**Infrastructure as Code**: All infrastructure defined in Terraform  
**State Files**: Stored in remote backend (S3/GCS)  
**Configuration**: Version controlled in Git

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms**:
- Database errors
- Data inconsistencies
- Application failures

**Recovery Procedure**:
1. Stop application services
2. Identify last known good backup
3. Restore database from backup
4. Verify data integrity
5. Restart application services
6. Monitor for issues

**Script**: `scripts/dr/restore-database.sh`

### Scenario 2: Complete Server Failure

**Symptoms**:
- Server unreachable
- All services down
- No response from infrastructure

**Recovery Procedure**:
1. Assess damage and identify root cause
2. Provision new infrastructure (Terraform)
3. Restore database from latest backup
4. Deploy application from container registry
5. Restore configuration from Git
6. Verify all services are running
7. Run health checks

**Script**: `scripts/dr/full-system-recovery.sh`

### Scenario 3: Data Center Outage

**Symptoms**:
- Complete data center unavailable
- All services unreachable
- Network connectivity lost

**Recovery Procedure**:
1. Activate disaster recovery site
2. Provision infrastructure in DR site
3. Restore database from off-site backup
4. Deploy application to DR site
5. Update DNS to point to DR site
6. Verify services are operational
7. Monitor for issues

**Script**: `scripts/dr/datacenter-failover.sh`

### Scenario 4: Ransomware Attack

**Symptoms**:
- Files encrypted
- Ransom note present
- System compromised

**Recovery Procedure**:
1. Isolate affected systems immediately
2. Do NOT pay ransom
3. Assess extent of compromise
4. Restore from clean backups
5. Rebuild compromised systems
6. Review security logs
7. Implement additional security measures
8. Report incident to authorities

**Script**: `scripts/dr/ransomware-recovery.sh`

### Scenario 5: Application Bug/Deployment Failure

**Symptoms**:
- Application errors
- Service degradation
- User complaints

**Recovery Procedure**:
1. Identify problematic deployment
2. Rollback to previous version
3. Verify rollback successful
4. Investigate root cause
5. Fix issue in development
6. Test fix thoroughly
7. Redeploy with fix

**Script**: `scripts/dr/rollback-application.sh`

## Recovery Procedures

### Database Recovery

#### Full Restore

```bash
# Restore from backup
./scripts/db/restore-database.sh /var/backups/postgresql/swe_db_20251109_020000.sql.gz

# Verify restore
psql -h localhost -U swe_user -d swe_db -c "SELECT COUNT(*) FROM information_schema.tables;"
```

#### Point-in-Time Recovery (PITR)

```bash
# Restore base backup
./scripts/db/restore-database.sh /var/backups/postgresql/base_backup.dump

# Configure recovery
cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /var/backups/postgresql/wal/%f %p'
recovery_target_time = '2025-11-09 14:30:00'
EOF

# Restart PostgreSQL
systemctl restart postgresql
```

### Application Recovery

#### Rollback Deployment

```bash
# Docker Compose
docker-compose pull
docker-compose up -d

# Kubernetes
kubectl rollout undo deployment/swe-api -n production

# Manual rollback
git checkout <previous-tag>
docker build -t swe-platform:previous .
docker-compose up -d
```

### Infrastructure Recovery

#### Rebuild from Terraform

```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file="terraform.prod.tfvars"
terraform apply -var-file="terraform.prod.tfvars"
```

## Testing and Validation

### Backup Testing

**Frequency**: Weekly  
**Procedure**:
1. Restore backup to test environment
2. Verify data integrity
3. Test application functionality
4. Document results

**Script**: `scripts/dr/test-backup-restore.sh`

### Disaster Recovery Drills

**Frequency**: Quarterly  
**Scenarios**:
- Database corruption
- Server failure
- Data center outage
- Application rollback

**Procedure**:
1. Simulate disaster scenario
2. Execute recovery procedures
3. Measure recovery time
4. Document lessons learned
5. Update procedures as needed

## Monitoring and Alerts

### Backup Monitoring

- Daily backup success/failure alerts
- Backup size monitoring
- Storage capacity alerts
- Backup age alerts (> 24 hours)

### System Health Monitoring

- Service availability
- Database connectivity
- Disk space usage
- CPU and memory usage
- Network connectivity

### Alert Channels

- Email: `alerts@example.com`
- Slack: `#alerts` channel
- PagerDuty: Critical alerts
- SMS: On-call rotation

## Communication Plan

### Incident Response Team

- **Incident Commander**: Coordinates recovery efforts
- **Database Administrator**: Handles database recovery
- **DevOps Engineer**: Handles infrastructure recovery
- **Application Developer**: Handles application issues
- **Security Officer**: Handles security incidents

### Communication Channels

- **Internal**: Slack `#incidents` channel
- **External**: Status page updates
- **Stakeholders**: Email updates every 2 hours

### Status Page

- **URL**: `https://status.swe-platform.com`
- **Updates**: Every 30 minutes during incident
- **Post-Mortem**: Published within 48 hours

## Post-Incident Review

### Post-Mortem Process

1. **Timeline**: Document incident timeline
2. **Root Cause**: Identify root cause
3. **Impact**: Assess business impact
4. **Actions**: Document actions taken
5. **Lessons Learned**: Identify improvements
6. **Action Items**: Create follow-up tasks
7. **Report**: Publish post-mortem report

### Continuous Improvement

- Review DR plan quarterly
- Update procedures based on incidents
- Test recovery procedures regularly
- Train team on recovery procedures
- Update documentation

## Runbooks

### Runbook: Database Corruption

**Location**: `docs/runbooks/database-corruption.md`

**Steps**:
1. Identify corruption
2. Stop application
3. Restore from backup
4. Verify integrity
5. Restart application
6. Monitor

### Runbook: Server Failure

**Location**: `docs/runbooks/server-failure.md`

**Steps**:
1. Assess failure
2. Provision new server
3. Restore database
4. Deploy application
5. Verify services
6. Monitor

### Runbook: Application Rollback

**Location**: `docs/runbooks/application-rollback.md`

**Steps**:
1. Identify issue
2. Stop deployment
3. Rollback to previous version
4. Verify functionality
5. Investigate root cause
6. Fix and redeploy

## Recovery Scripts

### Full System Recovery

**Location**: `scripts/dr/full-system-recovery.sh`

**Purpose**: Complete system recovery from scratch

**Usage**:
```bash
./scripts/dr/full-system-recovery.sh
```

### Database Recovery

**Location**: `scripts/dr/restore-database.sh`

**Purpose**: Restore database from backup

**Usage**:
```bash
./scripts/dr/restore-database.sh <backup_file>
```

### Application Rollback

**Location**: `scripts/dr/rollback-application.sh`

**Purpose**: Rollback application to previous version

**Usage**:
```bash
./scripts/dr/rollback-application.sh <previous_version>
```

## Backup Verification

### Automated Testing

**Script**: `scripts/dr/test-backup-restore.sh`

**Frequency**: Weekly

**Procedure**:
1. Restore latest backup to test environment
2. Verify database integrity
3. Test application functionality
4. Report results

## Related Documentation

- [Database Backups](./DATABASE_BACKUPS.md)
- [Staging Deployment](./STAGING_DEPLOYMENT.md)
- [Production Deployment](./PRODUCTION_DEPLOYMENT.md)
- [Security Guide](./SECURITY.md)

## Support

For disaster recovery assistance:
1. Check this documentation
2. Review runbooks
3. Execute recovery scripts
4. Contact incident response team
5. Escalate if needed

