# Disaster Recovery Plan

Comprehensive disaster recovery plan for PieHr platform.

## Executive Summary

**Recovery Time Objective (RTO)**: 4 hours  
**Recovery Point Objective (RPO)**: 1 hour  
**Maximum Acceptable Downtime**: 4 hours  
**Data Loss Tolerance**: 1 hour

## Scope

This plan covers:
- Application infrastructure
- Database recovery
- Data restoration
- Service restoration
- Communication procedures

## Risk Assessment

### Critical Systems

1. **Application Services** (API, Web)
   - Impact: Complete service outage
   - RTO: 2 hours
   - RPO: 15 minutes

2. **Database (Cloud SQL)**
   - Impact: Data loss, service unavailability
   - RTO: 4 hours
   - RPO: 1 hour

3. **Redis Cache**
   - Impact: Performance degradation
   - RTO: 1 hour
   - RPO: 0 (cache can be rebuilt)

4. **Storage (GCS)**
   - Impact: Asset unavailability
   - RTO: 2 hours
   - RPO: 1 hour

## Backup Strategy

### Database Backups

- **Frequency**: Daily at 2 AM UTC
- **Retention**: 7 days
- **Storage**: GCS bucket `piehr-backups`
- **Point-in-Time Recovery**: Enabled (7-day window)

### Application Backups

- **Container Images**: Stored in GCR/GHCR
- **Configuration**: Version controlled in Git
- **Secrets**: Stored in Google Secret Manager

### Storage Backups

- **Frequency**: Daily
- **Retention**: 30 days
- **Storage**: GCS with lifecycle policies

## Recovery Procedures

### Scenario 1: Complete Infrastructure Failure

**Symptoms:**
- All services unavailable
- GKE cluster unreachable
- Database unreachable

**Recovery Steps:**

1. **Assess Damage** (15 minutes)
   - Check GCP console
   - Verify resource status
   - Identify affected components

2. **Restore Infrastructure** (1-2 hours)
   ```bash
   # Recreate infrastructure via Terraform
   cd infrastructure/terraform/environments/production
   terraform apply
   ```

3. **Restore Database** (30 minutes)
   ```bash
   # Restore from latest backup
   python packages/db/backup.py restore \
     --backup-file backups/piehr_backup_YYYYMMDD_HHMMSS.sql
   ```

4. **Deploy Application** (30 minutes)
   ```bash
   ./scripts/deploy-production.sh
   ```

5. **Verify Functionality** (30 minutes)
   - Health checks
   - Smoke tests
   - User acceptance testing

**Total Recovery Time**: ~3-4 hours

### Scenario 2: Database Corruption

**Symptoms:**
- Database errors
- Data inconsistencies
- Application errors

**Recovery Steps:**

1. **Stop Application** (5 minutes)
   ```bash
   kubectl scale deployment/api --replicas=0 -n piehr
   kubectl scale deployment/web --replicas=0 -n piehr
   ```

2. **Identify Corruption** (15 minutes)
   - Check database logs
   - Identify affected tables
   - Determine corruption extent

3. **Restore Database** (30 minutes)
   ```bash
   # Point-in-time recovery if available
   gcloud sql backups restore <backup-id> \
     --backup-instance=piehr-db-prod \
     --restore-instance=piehr-db-prod
   
   # Or restore from backup file
   python packages/db/backup.py restore \
     --backup-file backups/piehr_backup_YYYYMMDD_HHMMSS.sql \
     --drop-existing
   ```

4. **Verify Data Integrity** (15 minutes)
   - Run data validation queries
   - Check referential integrity
   - Verify critical data

5. **Restart Application** (10 minutes)
   ```bash
   kubectl scale deployment/api --replicas=3 -n piehr
   kubectl scale deployment/web --replicas=2 -n piehr
   ```

**Total Recovery Time**: ~1.5 hours

### Scenario 3: Application Failure

**Symptoms:**
- Application crashes
- High error rate
- Service degradation

**Recovery Steps:**

1. **Rollback Deployment** (10 minutes)
   ```bash
   kubectl rollout undo deployment/api -n piehr
   kubectl rollout undo deployment/web -n piehr
   ```

2. **Scale Up** (5 minutes)
   ```bash
   kubectl scale deployment/api --replicas=5 -n piehr
   ```

3. **Verify Recovery** (15 minutes)
   - Health checks
   - Error rate monitoring
   - Performance metrics

**Total Recovery Time**: ~30 minutes

### Scenario 4: Regional Outage

**Symptoms:**
- Entire GCP region unavailable
- All services down

**Recovery Steps:**

1. **Failover to Secondary Region** (2-3 hours)
   - Provision infrastructure in secondary region
   - Restore database from backup
   - Update DNS to point to secondary region
   - Deploy application

2. **Monitor Primary Region** (ongoing)
   - Wait for region recovery
   - Plan failback procedure

**Total Recovery Time**: ~3-4 hours

## Failover Procedures

### Database Failover

Cloud SQL provides automatic failover:
- **Failover Time**: < 60 seconds
- **Data Loss**: None (synchronous replication)
- **Manual Failover**: Available via GCP console

### Application Failover

- **Multi-Zone Deployment**: Enabled by default
- **Auto-Scaling**: Handles traffic spikes
- **Load Balancing**: Distributes traffic across zones

## Testing Procedures

### Quarterly DR Tests

1. **Test Backup Restoration** (Monthly)
   - Restore database to test environment
   - Verify data integrity
   - Document results

2. **Test Infrastructure Recovery** (Quarterly)
   - Simulate infrastructure failure
   - Execute recovery procedures
   - Measure recovery time
   - Document improvements

3. **Test Application Failover** (Quarterly)
   - Simulate application failure
   - Test rollback procedures
   - Verify service restoration

### Test Schedule

- **Monthly**: Backup restoration test
- **Quarterly**: Full DR test
- **Annually**: Complete disaster simulation

## Communication Plan

### Internal Communication

- **Slack Channel**: #piehr-incidents
- **Email**: ops@piehr.example.com
- **PagerDuty**: Automatic alerts

### External Communication

- **Status Page**: https://status.piehr.example.com
- **Email Notifications**: Automated via monitoring
- **Social Media**: Updates as needed

### Escalation Matrix

1. **Level 1**: DevOps Engineer (0-30 minutes)
2. **Level 2**: SRE Lead (30-60 minutes)
3. **Level 3**: Engineering Lead (60+ minutes)
4. **Level 4**: CTO (Critical issues only)

## Post-Recovery Procedures

### Immediate Actions

1. **Document Incident**
   - Timeline of events
   - Root cause analysis
   - Recovery steps taken
   - Downtime duration

2. **Verify System Health**
   - All services operational
   - Data integrity verified
   - Performance metrics normal

3. **Notify Stakeholders**
   - Incident resolved
   - Brief summary
   - Post-mortem scheduled

### Post-Mortem

**Within 24 Hours:**
- Incident report
- Root cause analysis
- Impact assessment

**Within 1 Week:**
- Detailed post-mortem document
- Action items identified
- Process improvements

**Within 1 Month:**
- Action items completed
- Process improvements implemented
- DR plan updated

## Maintenance

### Regular Reviews

- **Monthly**: Review backup status
- **Quarterly**: Review DR procedures
- **Annually**: Update DR plan

### Backup Verification

- **Daily**: Automated backup verification
- **Weekly**: Manual backup restoration test
- **Monthly**: Full backup audit

## Appendices

### A. Contact Information

- **On-Call**: See PagerDuty
- **Escalation**: ops@piehr.example.com
- **GCP Support**: Via GCP console

### B. Backup Locations

- **Database**: `gs://piehr-backups/database/`
- **Storage**: `gs://piehr-backups/storage/`
- **Configurations**: Git repository

### C. Recovery Scripts

- `scripts/deploy-production.sh`: Application deployment
- `packages/db/backup.py`: Database backup/restore
- `infrastructure/terraform/`: Infrastructure provisioning

---

**Last Updated**: November 8, 2025  
**Version**: 1.0.0  
**Next Review**: February 8, 2026

