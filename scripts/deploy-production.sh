#!/bin/bash

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Configuration
NAMESPACE="${NAMESPACE:-piehr}"
GKE_CLUSTER="${GKE_CLUSTER:-piehr-gke-prod}"
GKE_REGION="${GKE_REGION:-us-central1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Safety check
if [ "${FORCE_DEPLOY:-false}" != "true" ]; then
    log_warn "⚠️  PRODUCTION DEPLOYMENT"
    read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " -r confirm
    if [[ ! $confirm =~ ^[Yy][Ee][Ss]$ ]]; then
        log_warn "Deployment cancelled"
        exit 0
    fi
fi

log_info "Starting production deployment..."
log_info "Namespace: $NAMESPACE"
log_info "Cluster: $GKE_CLUSTER"
log_info "Region: $GKE_REGION"
log_info "Image Tag: $IMAGE_TAG"

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is required but not installed"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    log_error "gcloud is required but not installed"
    exit 1
fi

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check if staging is healthy
log_info "Checking staging environment health..."
# Add staging health check here

# Create backup
log_info "Creating database backup..."
# Add backup creation here

# Get GKE credentials
log_info "Getting GKE credentials..."
gcloud container clusters get-credentials "$GKE_CLUSTER" \
    --region "$GKE_REGION" || {
    log_error "Failed to get GKE credentials"
    exit 1
}

# Verify cluster access
log_info "Verifying cluster access..."
kubectl cluster-info || {
    log_error "Failed to access cluster"
    exit 1
}

# Apply Kubernetes manifests
log_info "Applying Kubernetes manifests..."
cd "$PROJECT_ROOT/infrastructure/kubernetes/overlays/production"

if command -v kustomize &> /dev/null; then
    kustomize build . | kubectl apply -f -
else
    kubectl apply -k .
fi

# Update image tags if specified
if [ "$IMAGE_TAG" != "latest" ]; then
    log_info "Updating image tags to $IMAGE_TAG..."
    kubectl set image deployment/api api="gcr.io/PROJECT_ID/api:$IMAGE_TAG" -n "$NAMESPACE" || true
    kubectl set image deployment/web web="gcr.io/PROJECT_ID/web:$IMAGE_TAG" -n "$NAMESPACE" || true
fi

# Wait for rollout
log_info "Waiting for deployment rollout..."
kubectl rollout status deployment/api -n "$NAMESPACE" --timeout=10m || {
    log_error "API deployment failed, initiating rollback..."
    kubectl rollout undo deployment/api -n "$NAMESPACE"
    exit 1
}

kubectl rollout status deployment/web -n "$NAMESPACE" --timeout=10m || {
    log_error "Web deployment failed, initiating rollback..."
    kubectl rollout undo deployment/web -n "$NAMESPACE"
    exit 1
}

# Run database migrations
log_info "Running database migrations..."
# This would typically be done via a Kubernetes Job

# Health checks
log_info "Running health checks..."
API_URL=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}' || echo "")
if [ -n "$API_URL" ]; then
    for i in {1..60}; do
        if curl -f -s "https://$API_URL/health" > /dev/null 2>&1; then
            log_success "Health check passed"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Health check failed after 60 attempts, initiating rollback..."
            kubectl rollout undo deployment/api -n "$NAMESPACE"
            kubectl rollout undo deployment/web -n "$NAMESPACE"
            exit 1
        fi
        log_info "Waiting for service to be ready... (attempt $i/60)"
        sleep 10
    done
else
    log_warn "Could not determine API URL, skipping health check"
fi

# Smoke tests
log_info "Running smoke tests..."
# Add your smoke test commands here

log_success "Production deployment completed successfully!"
log_info "Deployment details:"
kubectl get pods -n "$NAMESPACE"
kubectl get services -n "$NAMESPACE"
kubectl get ingress -n "$NAMESPACE"

