# Production Runbook

Quick reference guide for common production operations and incident response.

## Quick Commands

### Check System Status

```bash
# Overall status
kubectl get all -n piehr

# Pod status
kubectl get pods -n piehr

# Service status
kubectl get svc -n piehr

# Ingress status
kubectl get ingress -n piehr
```

### View Logs

```bash
# API logs
kubectl logs -f deployment/api -n piehr

# Web logs
kubectl logs -f deployment/web -n piehr

# All pods logs
kubectl logs -f -l app=piehr -n piehr
```

### Restart Services

```bash
# Restart API
kubectl rollout restart deployment/api -n piehr

# Restart Web
kubectl rollout restart deployment/web -n piehr
```

## Common Issues

### Issue: Pods CrashLooping

**Symptoms:**

- Pods restarting repeatedly
- `kubectl get pods` shows CrashLoopBackOff

**Diagnosis:**

```bash
kubectl describe pod <pod-name> -n piehr
kubectl logs <pod-name> -n piehr --previous
```

**Common Causes:**

- Configuration errors
- Missing secrets
- Database connection issues
- Resource limits exceeded

**Resolution:**

1. Check logs for error messages
2. Verify secrets are configured
3. Check resource limits
4. Verify database connectivity

### Issue: High Error Rate

**Symptoms:**

- High 5xx error rate in metrics
- User complaints

**Diagnosis:**

```bash
# Check error logs
kubectl logs -f deployment/api -n piehr | grep ERROR

# Check metrics
curl https://api.piehr.example.com/metrics | grep http_requests_total
```

**Resolution:**

1. Identify error pattern
2. Check database connectivity
3. Check external service dependencies
4. Scale up if needed: `kubectl scale deployment/api --replicas=5 -n piehr`

### Issue: Database Connection Issues

**Symptoms:**

- Connection timeout errors
- Database unavailable errors

**Diagnosis:**

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -- \
  psql -h <db-host> -U <user> -d <database>

# Check Cloud SQL proxy
kubectl logs -n piehr deployment/cloud-sql-proxy
```

**Resolution:**

1. Verify Cloud SQL instance is running
2. Check network connectivity
3. Verify credentials
4. Check connection pool settings

### Issue: Certificate Expiration

**Symptoms:**

- SSL/TLS errors
- Certificate warnings in browser

**Diagnosis:**

```bash
kubectl get certificate -n piehr
kubectl describe certificate piehr-tls-cert -n piehr
```

**Resolution:**

1. Check certificate status
2. Verify DNS configuration
3. Manually renew if needed: `kubectl delete certificate piehr-tls-cert -n piehr`
4. Cert-manager will automatically recreate

### Issue: High Memory Usage

**Symptoms:**

- Pods being killed (OOMKilled)
- High memory metrics

**Diagnosis:**

```bash
kubectl top pods -n piehr
kubectl describe pod <pod-name> -n piehr | grep -A 5 "Limits\|Requests"
```

**Resolution:**

1. Increase memory limits
2. Optimize application memory usage
3. Scale horizontally
4. Check for memory leaks

## Incident Response

### Severity Levels

**P0 - Critical**

- Complete service outage
- Data loss
- Security breach

**P1 - High**

- Major feature broken
- Performance degradation
- Partial outage

**P2 - Medium**

- Minor feature issues
- Non-critical errors

**P3 - Low**

- Cosmetic issues
- Documentation updates

### P0 Response Procedure

1. **Assess Impact**

   ```bash
   kubectl get all -n piehr
   curl https://api.piehr.example.com/health
   ```

2. **Mitigate**
   - Rollback if recent deployment: `kubectl rollout undo deployment/api -n piehr`
   - Scale up if overloaded: `kubectl scale deployment/api --replicas=10 -n piehr`
   - Restart services: `kubectl rollout restart deployment/api -n piehr`

3. **Communicate**
   - Update status page
   - Notify team
   - Document incident

4. **Investigate**
   - Check logs
   - Review metrics
   - Identify root cause

5. **Resolve**
   - Apply fix
   - Verify resolution
   - Monitor for recurrence

6. **Post-Mortem**
   - Document incident
   - Identify improvements
   - Update runbooks

### Rollback Procedure

```bash
# Quick rollback
kubectl rollout undo deployment/api -n piehr
kubectl rollout undo deployment/web -n piehr

# Rollback to specific version
kubectl rollout undo deployment/api --to-revision=2 -n piehr

# Verify rollback
kubectl rollout status deployment/api -n piehr
```

## Maintenance Windows

### Scheduled Maintenance

- **Time**: Sunday 2 AM - 4 AM UTC
- **Duration**: 2 hours
- **Notification**: 48 hours in advance

### Maintenance Tasks

1. **Pre-Maintenance**
   - Create backup
   - Notify users
   - Prepare rollback plan

2. **During Maintenance**
   - Apply updates
   - Run migrations
   - Verify functionality

3. **Post-Maintenance**
   - Monitor metrics
   - Verify health checks
   - Update documentation

## Backup and Recovery

### Create Backup

```bash
# Manual backup
python packages/db/backup.py backup

# Verify backup
python packages/db/backup.py list
```

### Restore from Backup

```bash
# List available backups
python packages/db/backup.py list

# Restore backup
python packages/db/backup.py restore --backup-file backups/piehr_backup_YYYYMMDD_HHMMSS.sql
```

### Point-in-Time Recovery

Cloud SQL supports point-in-time recovery:

```bash
# Restore to specific time
gcloud sql backups restore <backup-id> \
  --backup-instance=<instance-name> \
  --restore-instance=<instance-name>
```

## Monitoring

### Key Metrics

- **Error Rate**: Should be < 0.1%
- **Latency**: P95 < 500ms
- **CPU Usage**: < 70%
- **Memory Usage**: < 80%
- **Database Connections**: < 80% of max

### Alerts

- **High Error Rate**: > 1% for 5 minutes
- **High Latency**: P95 > 1s for 5 minutes
- **Resource Exhaustion**: CPU/Memory > 90%
- **Certificate Expiration**: < 7 days remaining
- **Backup Failure**: Any backup job failure

### Dashboards

- **Grafana**: https://grafana.piehr.example.com
- **GCP Console**: Cloud Monitoring

## Escalation

### On-Call Rotation

- **Primary**: DevOps Engineer
- **Secondary**: SRE Engineer
- **Escalation**: Engineering Lead

### Contact Information

- **Slack**: #piehr-production
- **PagerDuty**: piehr-production
- **Email**: ops@piehr.example.com

---

**Last Updated**: November 8, 2025  
**Version**: 1.0.0
