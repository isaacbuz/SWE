# Infrastructure Setup Guide

This directory contains all infrastructure configuration and deployment code for the AI Company Platform.

## Directory Structure

```
infrastructure/
├── terraform/              # Terraform IaC for cloud deployment
│   ├── main.tf            # Main Terraform configuration
│   ├── variables.tf       # Variable definitions
│   ├── terraform.dev.tfvars   # Development environment variables
│   └── terraform.prod.tfvars  # Production environment variables
├── kubernetes/            # Kubernetes manifests
│   ├── namespace.yaml     # Namespace and resource quotas
│   ├── deployment.yaml    # Application deployment
│   ├── secrets.yaml       # Secret management
│   └── ingress.yaml       # Ingress configuration
├── database/              # Database configurations
├── docker/                # Docker build configurations
└── README.md              # This file
```

## Quick Start

### Local Development Setup

```bash
# Run the automated setup script
bash scripts/setup-local.sh

# Verify services are running
docker-compose ps

# Check health of services
docker-compose logs

# Access services
# - API: http://localhost:8000
# - Temporal UI: http://localhost:8080
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### Cloud Deployment (GCP)

```bash
# Initialize Terraform
cd infrastructure/terraform
terraform init

# Plan deployment
terraform plan -var-file="terraform.prod.tfvars"

# Apply configuration
terraform apply -var-file="terraform.prod.tfvars"

# Get outputs
terraform output
```

## Components

### 1. PostgreSQL Database (Cloud SQL)

**Local Development**:

```bash
# Connection
psql -h localhost -U postgres -d ai_company_db

# Backup
docker-compose exec postgres pg_dump -U postgres ai_company_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres ai_company_db < backup.sql
```

**Production (GCP Cloud SQL)**:

- Automatic backups with point-in-time recovery
- SSL/TLS encryption in transit
- Private network access via VPC
- Cloud SQL Auth proxy for secure connections
- Query Insights for performance monitoring

### 2. Redis Cache

**Local Development**:

```bash
# Connect to Redis
redis-cli -h localhost -p 6379 -a redis_password

# Monitor commands
MONITOR

# Check memory usage
INFO memory
```

**Production (GCP Memorystore)**:

- High availability with replication
- Automatic failover
- Persistence options (RDB, AOF)
- Private network access
- Encrypted connection support

### 3. Cloud Storage (GCS)

**Bucket Management**:

```bash
# Create bucket
gsutil mb -c STANDARD gs://ai-company-bucket-prod

# Upload files
gsutil -m cp -r local_folder gs://ai-company-bucket-prod

# Configure lifecycle rules
gsutil lifecycle set lifecycle.json gs://ai-company-bucket-prod

# Enable encryption
gsutil encryption set <key-name> gs://ai-company-bucket-prod
```

### 4. Kubernetes Cluster (GKE)

**Cluster Management**:

```bash
# Get cluster credentials
gcloud container clusters get-credentials ai-company-gke-prod --region us-central1

# View cluster status
kubectl cluster-info

# Scale cluster
gcloud container clusters resize ai-company-gke-prod --num-nodes 5 --region us-central1

# View nodes
kubectl get nodes -o wide
```

**Deployment**:

```bash
# Apply all manifests
kubectl apply -f infrastructure/kubernetes/

# Monitor deployment
kubectl rollout status deployment/ai-company-app -n production

# View pods
kubectl get pods -n production

# View logs
kubectl logs -f deployment/ai-company-app -n production
```

## Environment Variables

### Development (.env.example)

All required environment variables are documented in `.env.example`:

```bash
# Copy to your environment
cp .env.example .env

# Edit with your values
nano .env
```

Key variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - JWT signing secret
- `API_KEYS` - External service API keys
- `CLOUD_CREDENTIALS` - AWS/GCP credentials

### Terraform Variables

```bash
# Use tfvars files for different environments
terraform plan -var-file="terraform.dev.tfvars"
terraform plan -var-file="terraform.prod.tfvars"

# Or set variables via command line
terraform plan \
  -var="gcp_project_id=my-project" \
  -var="environment=production"
```

## Security

### Secret Management

See `/docs/SECURITY.md` for comprehensive security guidelines.

**Quick Reference**:

1. Never commit `.env` files to git
2. Use `.env.example` as template
3. For CI/CD: Use GitHub Secrets
4. For Production: Use managed secret stores (Google Secret Manager, AWS Secrets Manager)
5. Rotate secrets regularly using `scripts/rotate-secrets.sh`

### Access Control

**Kubernetes RBAC**:

```yaml
# Example role for application
kind: Role
metadata:
  name: app-role
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]
```

**Workload Identity** (for GKE):

```bash
# Bind Kubernetes SA to GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  ai-company-gke-prod@project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member serviceAccount:project.svc.id.goog[production/app-sa]
```

## Deployment Strategies

### Development (docker-compose)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Full reset
docker-compose down -v
```

### Staging/Production (Kubernetes)

```bash
# Deploy with rolling update
kubectl apply -f infrastructure/kubernetes/deployment.yaml

# Monitor rollout
kubectl rollout status deployment/ai-company-app -n production

# Rollback if needed
kubectl rollout undo deployment/ai-company-app -n production
```

### Canary Deployments

```bash
# Deploy new version to canary namespace
kubectl apply -f deployment-canary.yaml -n canary

# Monitor metrics
kubectl top pods -n canary

# Promote to production
kubectl apply -f deployment.yaml -n production
```

## Monitoring and Observability

### Prometheus

```bash
# Access Prometheus UI
open http://localhost:9090

# Query metrics
# Example: http_requests_total
```

### Grafana

```bash
# Access Grafana
open http://localhost:3001

# Default credentials
# Username: admin
# Password: (set in .env via GRAFANA_PASSWORD)
```

### Jaeger Tracing

```bash
# Access Jaeger UI
open http://localhost:16686

# View distributed traces
# Service: ai-company-app
```

### Logs

```bash
# Docker Compose
docker-compose logs -f <service-name>

# Kubernetes
kubectl logs -f deployment/ai-company-app -n production

# Google Cloud Logging
gcloud logging read "resource.type=cloud_run_revision"
```

## Scaling

### Horizontal Pod Autoscaling (HPA)

```bash
# Create HPA
kubectl apply -f infrastructure/kubernetes/deployment.yaml

# View HPA status
kubectl get hpa -n production

# Manual scaling
kubectl scale deployment ai-company-app --replicas=5 -n production
```

### Cluster Autoscaling

```bash
# Enable cluster autoscaling
gcloud container clusters update ai-company-gke-prod \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10 \
  --region=us-central1
```

## Backup and Disaster Recovery

### Database Backups

```bash
# PostgreSQL (local)
docker-compose exec postgres pg_dump -U postgres -Fc ai_company_db > backup.dump

# Restore
docker-compose exec -T postgres pg_restore -U postgres -d ai_company_db < backup.dump

# Cloud SQL (automated)
# Backups are configured in terraform/main.tf
# - Automatic daily backups
# - Point-in-time recovery enabled
# - 30-day retention
```

### GCS Backups

```bash
# Configure lifecycle policy
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://ai-company-bucket-prod
```

### Disaster Recovery Plan

1. **Data Recovery**:
   - Cloud SQL: Point-in-time restore to specific timestamp
   - GCS: Version-enabled buckets allow file restoration
   - Redis: Persistence enabled for recovery

2. **Infrastructure Recovery**:
   - Terraform: Recreate infrastructure from code
   - Kubernetes: Redeploy from manifests
   - Configuration: Stored in version control

3. **Recovery Time Objectives (RTO)**:
   - Database: 15 minutes
   - Infrastructure: 30 minutes
   - Full system: 1 hour

## Troubleshooting

### Services not starting

```bash
# Check Docker daemon
docker ps

# View service logs
docker-compose logs <service-name>

# Health check
docker-compose ps

# Restart services
docker-compose restart
```

### Database connection issues

```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d ai_company_db -c "SELECT 1"

# Check password in .env
grep DATABASE_PASSWORD .env

# View PostgreSQL logs
docker-compose logs postgres
```

### Kubernetes issues

```bash
# Check cluster status
kubectl cluster-info

# View pod status
kubectl describe pod <pod-name> -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'

# Debug pod
kubectl exec -it <pod-name> -n production -- /bin/bash
```

## Cost Optimization

### GCP Cost Tips

1. **Compute**:
   - Use auto-scaling for variable load
   - Enable cluster autoscaling
   - Use preemptible instances for non-critical workloads

2. **Storage**:
   - Implement lifecycle policies for old data
   - Use Coldline/Archive storage classes
   - Enable compression for backups

3. **Networking**:
   - Use private services where possible
   - Configure CloudCDN for static assets
   - Monitor egress costs

4. **Monitoring**:
   - Set up budget alerts
   - Review monthly cost reports
   - Optimize log retention

## Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [Google Cloud Best Practices](https://cloud.google.com/docs/best-practices)
- [Kubernetes Documentation](https://kubernetes.io/docs)
- [Docker Documentation](https://docs.docker.com)
- [Security Guidelines](../docs/SECURITY.md)

## Support

For infrastructure-related questions:

1. Check the troubleshooting section above
2. Review logs and error messages
3. Consult the documentation for the specific service
4. Contact the infrastructure team

---

Last Updated: 2025-11-08
Version: 1.0
