# Deployment Guide

This directory contains deployment scripts and documentation for staging and production environments.

## Quick Start

### Deploy to Staging

```bash
# Using script
./scripts/deploy-staging.sh

# Using kubectl directly
kubectl apply -k infrastructure/kubernetes/overlays/staging
```

### Deploy to Production

```bash
# Using script (requires confirmation)
./scripts/deploy-production.sh

# Using kubectl directly
kubectl apply -k infrastructure/kubernetes/overlays/production
```

## Prerequisites

1. **GCP Project**: Configured with billing enabled
2. **GKE Cluster**: Created and accessible
3. **gcloud CLI**: Installed and authenticated
4. **kubectl**: Installed and configured
5. **kustomize**: Installed (optional, for Kustomize builds)
6. **Docker Images**: Built and pushed to container registry

## Environment Setup

### Staging Environment

- **Namespace**: `piehr-staging`
- **Cluster**: `piehr-gke-staging`
- **Region**: `us-central1`
- **Domain**: `staging.piehr.example.com`

### Production Environment

- **Namespace**: `piehr`
- **Cluster**: `piehr-gke-prod`
- **Region**: `us-central1`
- **Domain**: `piehr.example.com`

## Deployment Process

### 1. Pre-Deployment Checks

- Verify GKE cluster is accessible
- Check database connectivity
- Verify secrets are configured
- Run pre-deployment tests

### 2. Apply Infrastructure

- Apply Kubernetes manifests
- Update image tags
- Wait for rollout

### 3. Post-Deployment

- Run database migrations
- Health checks
- Smoke tests
- Monitor metrics

## Rollback Procedure

### Automatic Rollback

The deployment scripts automatically rollback on failure:

```bash
kubectl rollout undo deployment/api -n piehr-staging
kubectl rollout undo deployment/web -n piehr-staging
```

### Manual Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/api -n piehr-staging

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=2 -n piehr-staging

# View rollout history
kubectl rollout history deployment/api -n piehr-staging
```

## Troubleshooting

### Deployment Fails

1. Check pod status: `kubectl get pods -n piehr-staging`
2. Check pod logs: `kubectl logs -n piehr-staging deployment/api`
3. Check events: `kubectl get events -n piehr-staging --sort-by='.lastTimestamp'`
4. Check ingress: `kubectl get ingress -n piehr-staging`

### Health Checks Fail

1. Verify service is running: `kubectl get svc -n piehr-staging`
2. Check ingress configuration: `kubectl describe ingress -n piehr-staging`
3. Test connectivity: `curl https://staging.piehr.example.com/health`

### Database Migration Fails

1. Check migration job: `kubectl get jobs -n piehr-staging`
2. View migration logs: `kubectl logs -n piehr-staging job/migrate-db-<timestamp>`
3. Manually run migrations if needed

## CI/CD Integration

Deployments are automated via GitHub Actions:

- **Staging**: Auto-deploys on merge to `main` branch
- **Production**: Requires manual approval and git tag

See `.github/workflows/deploy.yml` for details.

## Security

- All secrets managed via External Secrets Operator
- TLS certificates via cert-manager
- Network policies enforced
- RBAC configured

## Monitoring

After deployment, monitor:

- Pod status and health
- Application logs
- Metrics and alerts
- Cost tracking

## Documentation

- [Kubernetes Manifests](../kubernetes/README.md)
- [Terraform Infrastructure](../terraform/README.md)
- [Secret Management](../secrets/README.md)
- [Monitoring Setup](../monitoring/README.md)
