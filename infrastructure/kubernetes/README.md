# Kubernetes Manifests for PieHr Platform

This directory contains Kubernetes manifests for deploying the PieHr AI-First Software Engineering Platform to production.

## Structure

```
infrastructure/kubernetes/
├── base/                          # Base manifests
│   ├── namespace.yaml            # Namespace definitions
│   ├── resource-quota.yaml       # Resource quotas
│   ├── service-accounts.yaml     # Service accounts
│   ├── network-policy.yaml       # Network policies
│   ├── api/                      # API service manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   ├── pdb.yaml
│   │   └── configmap.yaml
│   ├── web/                      # Web frontend manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── configmap.yaml
│   ├── postgresql/               # PostgreSQL database
│   │   ├── statefulset.yaml
│   │   └── service.yaml
│   ├── redis/                    # Redis cache
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── configmap.yaml
│   ├── temporal/                 # Temporal worker
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── ingress/                  # Ingress configuration
│   │   └── ingress.yaml
│   └── kustomization.yaml        # Base kustomization
├── overlays/                      # Environment-specific overlays
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   ├── ingress-patch.yaml
│   │   └── replicas-patch.yaml
│   └── production/
│       ├── kustomization.yaml
│       ├── ingress-patch.yaml
│       └── resource-quotas-patch.yaml
└── README.md                      # This file
```

## Components

### API Service
- **Deployment**: FastAPI backend service
- **Replicas**: 3 (production), 2 (staging)
- **Resources**: 512Mi-2Gi memory, 500m-2000m CPU
- **HPA**: Auto-scales based on CPU (70%) and memory (80%)
- **Health Checks**: `/health` (liveness), `/ready` (readiness)

### Web Service
- **Deployment**: Next.js frontend application
- **Replicas**: 3 (production), 2 (staging)
- **Resources**: 256Mi-1Gi memory, 250m-1000m CPU
- **HPA**: Auto-scales based on CPU (70%) and memory (80%)

### PostgreSQL Database
- **StatefulSet**: PostgreSQL 15 with persistent storage
- **Replicas**: 1 (primary)
- **Storage**: 100Gi SSD persistent volume
- **Resources**: 1Gi-4Gi memory, 500m-2000m CPU

### Redis Cache
- **Deployment**: Redis 7 with persistent storage
- **Replicas**: 1
- **Storage**: 50Gi SSD persistent volume
- **Resources**: 512Mi-2Gi memory, 250m-1000m CPU
- **Persistence**: AOF (Append Only File) enabled

### Temporal Worker
- **Deployment**: Temporal workflow worker
- **Replicas**: 2
- **Resources**: 512Mi-2Gi memory, 500m-2000m CPU

## Deployment

### Prerequisites
- Kubernetes cluster (GKE recommended)
- kubectl configured
- kustomize installed
- Container images built and pushed to registry
- Domain name configured
- SSL certificates (Let's Encrypt via cert-manager)

### Deploy to Staging

```bash
kubectl apply -k overlays/staging
```

### Deploy to Production

```bash
kubectl apply -k overlays/production
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods -n piehr

# Check services
kubectl get svc -n piehr

# Check ingress
kubectl get ingress -n piehr

# Check HPA
kubectl get hpa -n piehr
```

## Configuration

### Environment Variables
- Set `PROJECT_ID` in image references
- Update domain names in ingress configurations
- Configure secrets (database URLs, API keys, etc.)

### Secrets
Secrets should be created separately using sealed-secrets or external-secrets:
- `api-secrets`: Database URL, Redis URL, JWT secret
- `postgresql-secrets`: Database username and password
- `redis-secrets`: Redis password

### ConfigMaps
- `api-config`: API service configuration
- `web-config`: Web frontend configuration
- `redis-config`: Redis configuration
- `temporal-config`: Temporal worker configuration

## Scaling

### Horizontal Pod Autoscaling
- API and Web services have HPA configured
- Scales based on CPU (70%) and memory (80%) utilization
- Min replicas: 3, Max replicas: 10

### Manual Scaling
```bash
# Scale API
kubectl scale deployment api -n piehr --replicas=5

# Scale Web
kubectl scale deployment web -n piehr --replicas=5
```

## Security

### Network Policies
- Restricts ingress/egress traffic between pods
- API can only connect to PostgreSQL and Redis
- Web can only connect to API
- Database and cache are isolated

### Pod Security
- All pods run as non-root users
- Read-only root filesystem
- Dropped capabilities
- Security contexts configured

### TLS/SSL
- TLS termination at ingress
- Let's Encrypt certificates via cert-manager
- Automatic certificate renewal

## Monitoring

### Health Checks
- Liveness probes: `/health` endpoint
- Readiness probes: `/ready` endpoint
- Configured for all services

### Metrics
- Prometheus scraping enabled
- Metrics exposed on port 9090
- ServiceMonitor can be added for Prometheus Operator

## Troubleshooting

### Check Pod Logs
```bash
# API logs
kubectl logs -n piehr deployment/api

# Web logs
kubectl logs -n piehr deployment/web
```

### Describe Resources
```bash
# Describe deployment
kubectl describe deployment api -n piehr

# Describe pod
kubectl describe pod <pod-name> -n piehr
```

### Debug Pod
```bash
# Exec into pod
kubectl exec -it <pod-name> -n piehr -- /bin/sh
```

## Updates

### Rolling Updates
- All deployments use RollingUpdate strategy
- Max surge: 1, Max unavailable: 0
- Ensures zero-downtime deployments

### Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/api -n piehr

# Check rollout history
kubectl rollout history deployment/api -n piehr
```

## Resource Management

### Resource Quotas
- Production: 200 CPU requests, 400Gi memory requests
- Staging: 100 CPU requests, 200Gi memory requests
- Limits set at 2x requests

### Pod Disruption Budgets
- API: Minimum 2 pods available
- Ensures high availability during node maintenance

## Next Steps

1. Set up sealed-secrets or external-secrets for secret management
2. Configure cert-manager for automatic TLS certificates
3. Set up Prometheus monitoring
4. Configure backup for PostgreSQL
5. Set up log aggregation (e.g., Loki, Elasticsearch)

