# Production Deployment Guide

Complete guide for deploying the PieHr platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Steps](#deployment-steps)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)
7. [Monitoring](#monitoring)

## Prerequisites

### Infrastructure

- [ ] GCP Project created and billing enabled
- [ ] GKE cluster provisioned (see `infrastructure/terraform/`)
- [ ] Cloud SQL instance created
- [ ] Cloud Memorystore (Redis) instance created
- [ ] Cloud Storage bucket for backups
- [ ] DNS zone configured
- [ ] Domain names configured

### Tools

- [ ] `gcloud` CLI installed and authenticated
- [ ] `kubectl` installed and configured
- [ ] `kustomize` installed (optional)
- [ ] `terraform` installed (for infrastructure)
- [ ] Docker installed (for local testing)

### Access

- [ ] GCP Service Account with required permissions
- [ ] Kubernetes cluster access configured
- [ ] GitHub Actions secrets configured
- [ ] Access to Google Secret Manager

## Pre-Deployment Checklist

### Security

- [ ] All secrets stored in Google Secret Manager
- [ ] External Secrets Operator installed
- [ ] Network policies configured
- [ ] RBAC configured
- [ ] SSL/TLS certificates configured
- [ ] Security scanning completed

### Database

- [ ] Database migrations tested
- [ ] Backup strategy configured
- [ ] Point-in-time recovery enabled
- [ ] Connection pooling configured

### Monitoring

- [ ] Prometheus configured
- [ ] Grafana dashboards created
- [ ] Alerting rules configured
- [ ] Log aggregation configured

### Application

- [ ] Container images built and pushed
- [ ] Health checks implemented
- [ ] Graceful shutdown configured
- [ ] Resource limits set

## Deployment Steps

### 1. Provision Infrastructure

```bash
cd infrastructure/terraform/environments/production
terraform init
terraform plan
terraform apply
```

**Expected Output:**
- GKE cluster created
- Cloud SQL instance created
- Cloud Memorystore instance created
- Cloud Storage bucket created
- VPC and networking configured

### 2. Configure Kubernetes Access

```bash
gcloud container clusters get-credentials piehr-gke-prod \
  --region us-central1 \
  --project YOUR_PROJECT_ID
```

### 3. Install Prerequisites

#### Install cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

#### Install External Secrets Operator

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

#### Install NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### 4. Configure Secrets

#### Create Secret Store

```bash
kubectl apply -f infrastructure/kubernetes/secrets/external-secrets-operator.yaml
```

#### Verify Secrets Synced

```bash
kubectl get secrets -n piehr
```

### 5. Configure SSL/TLS Certificates

```bash
kubectl apply -f infrastructure/kubernetes/cert-manager/cluster-issuer.yaml
```

**Verify Certificate Status:**

```bash
kubectl get certificate -n piehr
kubectl describe certificate piehr-tls-cert -n piehr
```

### 6. Deploy Application

#### Using Kustomize (Recommended)

```bash
cd infrastructure/kubernetes/overlays/production
kustomize build . | kubectl apply -f -
```

#### Using kubectl directly

```bash
kubectl apply -k infrastructure/kubernetes/overlays/production
```

#### Using deployment script

```bash
./scripts/deploy-production.sh
```

### 7. Run Database Migrations

```bash
kubectl create job --from=cronjob/migrate-db migrate-db-$(date +%s) -n piehr
kubectl logs -f job/migrate-db-<timestamp> -n piehr
```

### 8. Verify Deployment

```bash
# Check pod status
kubectl get pods -n piehr

# Check services
kubectl get svc -n piehr

# Check ingress
kubectl get ingress -n piehr

# Check certificate
kubectl get certificate -n piehr
```

## Post-Deployment Verification

### Health Checks

```bash
# API health check
curl https://api.piehr.example.com/health

# Web health check
curl https://piehr.example.com/health
```

### Smoke Tests

```bash
# Test API endpoints
curl https://api.piehr.example.com/api/v1/projects
curl https://api.piehr.example.com/api/v1/agents

# Test authentication
curl -X POST https://api.piehr.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

### Performance Tests

```bash
# Run load tests (if configured)
k6 run tests/load/api-load-test.js
```

### Monitoring Verification

- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards showing data
- [ ] Alerts configured and tested
- [ ] Logs aggregating correctly

## Rollback Procedures

### Automatic Rollback

The deployment scripts automatically rollback on failure:

```bash
# Rollback API deployment
kubectl rollout undo deployment/api -n piehr

# Rollback Web deployment
kubectl rollout undo deployment/web -n piehr
```

### Manual Rollback

#### Rollback to Previous Version

```bash
# View rollout history
kubectl rollout history deployment/api -n piehr

# Rollback to previous revision
kubectl rollout undo deployment/api -n piehr

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=2 -n piehr
```

#### Rollback Database Migration

```bash
# List migration jobs
kubectl get jobs -n piehr | grep migrate

# View migration logs
kubectl logs job/migrate-db-<timestamp> -n piehr

# If migration failed, restore from backup
python packages/db/backup.py restore --backup-file backups/piehr_backup_YYYYMMDD_HHMMSS.sql
```

### Emergency Rollback

If critical issues occur:

1. **Immediate Rollback:**
   ```bash
   kubectl rollout undo deployment/api -n piehr
   kubectl rollout undo deployment/web -n piehr
   ```

2. **Scale Down:**
   ```bash
   kubectl scale deployment/api --replicas=0 -n piehr
   kubectl scale deployment/web --replicas=0 -n piehr
   ```

3. **Restore Database:**
   ```bash
   python packages/db/backup.py restore --backup-file backups/latest_backup.sql --drop-existing
   ```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n piehr

# Check pod logs
kubectl logs -n piehr deployment/api
kubectl logs -n piehr deployment/web

# Check pod events
kubectl describe pod <pod-name> -n piehr
```

### Database Connection Issues

```bash
# Check database connectivity
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -- \
  psql -h <db-host> -U <user> -d <database>

# Check Cloud SQL proxy (if using)
kubectl logs -n piehr deployment/cloud-sql-proxy
```

### Certificate Issues

```bash
# Check certificate status
kubectl get certificate -n piehr
kubectl describe certificate piehr-tls-cert -n piehr

# Check certificate order
kubectl get order -n piehr

# Check certificate challenge
kubectl get challenge -n piehr
```

### Ingress Issues

```bash
# Check ingress status
kubectl get ingress -n piehr
kubectl describe ingress piehr-ingress -n piehr

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n piehr
kubectl top nodes

# Check HPA status
kubectl get hpa -n piehr

# Check metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/piehr/pods
```

## Monitoring

### Metrics

- **Application Metrics**: Available at `/metrics` endpoint
- **Kubernetes Metrics**: Available via metrics-server
- **Custom Metrics**: Available via Prometheus

### Dashboards

- **Grafana**: https://grafana.piehr.example.com
- **GCP Console**: Cloud Monitoring dashboards

### Alerts

Configured alerts:
- High error rate
- High latency
- Resource exhaustion
- Certificate expiration
- Backup failures

### Logs

- **Application Logs**: Available via Cloud Logging
- **Kubernetes Logs**: Available via `kubectl logs`
- **Audit Logs**: Available via Cloud Audit Logs

## Backup and Recovery

### Automated Backups

- **Database**: Daily backups at 2 AM UTC
- **Storage**: Backups stored in GCS bucket
- **Retention**: 7 days of backups retained

### Manual Backup

```bash
# Create manual backup
python packages/db/backup.py backup

# List backups
python packages/db/backup.py list

# Restore from backup
python packages/db/backup.py restore --backup-file backups/piehr_backup_YYYYMMDD_HHMMSS.sql
```

### Point-in-Time Recovery

Cloud SQL supports point-in-time recovery:
- Recovery window: 7 days
- Recovery granularity: 1 minute

## Security

### Network Policies

Network policies are enforced:
- Ingress traffic only from ingress controller
- Egress traffic restricted to necessary services
- Inter-pod communication restricted

### RBAC

Role-based access control:
- Service accounts with minimal permissions
- No cluster-admin access for workloads
- Audit logging enabled

### Secrets Management

- All secrets stored in Google Secret Manager
- External Secrets Operator syncs to Kubernetes
- Secrets rotated regularly
- No secrets in code or config files

## Maintenance

### Regular Tasks

- **Weekly**: Review and update dependencies
- **Monthly**: Security audit and updates
- **Quarterly**: Disaster recovery testing

### Updates

- **Application Updates**: Deploy via CI/CD pipeline
- **Infrastructure Updates**: Apply via Terraform
- **Kubernetes Updates**: Managed by GKE

## Support

For issues or questions:
- **Documentation**: See `docs/` directory
- **Runbooks**: See `infrastructure/runbooks/`
- **Issues**: Create GitHub issue

---

**Last Updated**: November 8, 2025  
**Version**: 1.0.0

