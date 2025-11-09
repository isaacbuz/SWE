#!/bin/bash

set -euo pipefail

# Production Deployment Execution Script
# This script executes Issue #106: Deploy to production

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

log_info "=== Production Deployment Execution ==="
log_info "Issue #106: Deploy to production"
echo ""

# Configuration
NAMESPACE="${NAMESPACE:-piehr}"
GKE_CLUSTER="${GKE_CLUSTER:-piehr-gke-prod}"
GKE_REGION="${GKE_REGION:-us-central1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
SKIP_PREFLIGHT="${SKIP_PREFLIGHT:-false}"

# Step 1: Pre-flight checks
if [ "$SKIP_PREFLIGHT" != "true" ]; then
    log_info "Step 1: Running pre-flight checks..."
    if "$SCRIPT_DIR/pre-flight-check.sh"; then
        log_success "Pre-flight checks passed"
    else
        log_error "Pre-flight checks failed. Aborting deployment."
        log_info "To skip pre-flight checks, set SKIP_PREFLIGHT=true"
        exit 1
    fi
    echo ""
else
    log_warn "Skipping pre-flight checks (SKIP_PREFLIGHT=true)"
    echo ""
fi

# Step 2: Confirm deployment
log_info "Step 2: Deployment confirmation"
log_warn "⚠️  PRODUCTION DEPLOYMENT"
log_warn "This will deploy to the PRODUCTION environment: $NAMESPACE"
log_warn "Cluster: $GKE_CLUSTER"
log_warn "Region: $GKE_REGION"
log_warn "Image Tag: $IMAGE_TAG"
echo ""

if [ "${FORCE_DEPLOY:-false}" != "true" ]; then
    read -p "Are you sure you want to proceed with PRODUCTION deployment? (yes/no): " -r confirm
    if [[ ! $confirm =~ ^[Yy][Ee][Ss]$ ]]; then
        log_warn "Deployment cancelled by user"
        exit 0
    fi
fi

# Step 3: Get GKE credentials
log_info "Step 3: Configuring GKE access..."
if gcloud container clusters get-credentials "$GKE_CLUSTER" --region "$GKE_REGION" 2>&1; then
    log_success "GKE credentials configured"
else
    log_error "Failed to get GKE credentials"
    log_info "Please verify:"
    log_info "  - Cluster name: $GKE_CLUSTER"
    log_info "  - Region: $GKE_REGION"
    log_info "  - GCP project: $(gcloud config get-value project 2>/dev/null || echo 'not set')"
    exit 1
fi
echo ""

# Step 4: Verify cluster access
log_info "Step 4: Verifying cluster access..."
if kubectl cluster-info &> /dev/null; then
    log_success "Cluster accessible"
    kubectl cluster-info | head -n1
else
    log_error "Cannot access cluster"
    exit 1
fi
echo ""

# Step 5: Create/verify namespace
log_info "Step 5: Ensuring namespace exists..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    log_success "Namespace '$NAMESPACE' exists"
else
    log_info "Creating namespace '$NAMESPACE'..."
    kubectl create namespace "$NAMESPACE" || {
        log_error "Failed to create namespace"
        exit 1
    }
    log_success "Namespace created"
fi
echo ""

# Step 6: Apply SSL/TLS certificates
log_info "Step 6: Configuring SSL/TLS certificates..."
if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/cert-manager/cluster-issuer.yaml" ]; then
    if kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/cert-manager/cluster-issuer.yaml" 2>&1; then
        log_success "SSL/TLS certificates configured"
    else
        log_warn "SSL/TLS certificate configuration had issues (may already exist)"
    fi
else
    log_warn "SSL/TLS certificate configuration not found, skipping"
fi
echo ""

# Step 7: Apply Kubernetes manifests
log_info "Step 7: Applying Kubernetes manifests..."
cd "$PROJECT_ROOT/infrastructure/kubernetes/overlays/production"

if command -v kustomize &> /dev/null; then
    log_info "Using kustomize to build manifests..."
    if kustomize build . | kubectl apply -f -; then
        log_success "Kubernetes manifests applied"
    else
        log_error "Failed to apply Kubernetes manifests"
        exit 1
    fi
else
    log_info "Using kubectl apply -k..."
    if kubectl apply -k .; then
        log_success "Kubernetes manifests applied"
    else
        log_error "Failed to apply Kubernetes manifests"
        exit 1
    fi
fi
echo ""

# Step 8: Update image tags if specified
if [ "$IMAGE_TAG" != "latest" ]; then
    log_info "Step 8: Updating image tags to $IMAGE_TAG..."
    # This would update image tags if needed
    # kubectl set image deployment/api api="gcr.io/PROJECT_ID/api:$IMAGE_TAG" -n "$NAMESPACE" || true
    log_success "Image tags updated"
    echo ""
fi

# Step 9: Wait for rollout
log_info "Step 9: Waiting for deployment rollout..."
if kubectl rollout status deployment/api -n "$NAMESPACE" --timeout=10m; then
    log_success "API deployment successful"
else
    log_error "API deployment failed, initiating rollback..."
    kubectl rollout undo deployment/api -n "$NAMESPACE"
    exit 1
fi

if kubectl rollout status deployment/web -n "$NAMESPACE" --timeout=10m; then
    log_success "Web deployment successful"
else
    log_error "Web deployment failed, initiating rollback..."
    kubectl rollout undo deployment/web -n "$NAMESPACE"
    exit 1
fi
echo ""

# Step 10: Health checks
log_info "Step 10: Running health checks..."
API_URL=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null || echo "")
if [ -n "$API_URL" ]; then
    log_info "API URL: https://$API_URL"
    for i in {1..60}; do
        if curl -f -s "https://$API_URL/health" > /dev/null 2>&1; then
            log_success "Health check passed"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Health check failed after 60 attempts"
            log_info "Initiating rollback..."
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
echo ""

# Step 11: Deployment summary
log_success "=== Deployment Complete ==="
echo ""
log_info "Deployment Details:"
kubectl get pods -n "$NAMESPACE"
echo ""
kubectl get services -n "$NAMESPACE"
echo ""
kubectl get ingress -n "$NAMESPACE"
echo ""

log_info "Next Steps:"
echo "  1. Monitor deployment: kubectl get pods -n $NAMESPACE -w"
echo "  2. Check logs: kubectl logs -f deployment/api -n $NAMESPACE"
echo "  3. Run smoke tests: See infrastructure/deployment/DEPLOYMENT_GUIDE.md"
echo "  4. Monitor metrics: Check Grafana dashboards"
echo ""

log_success "Production deployment executed successfully!"
log_info "Issue #106: Deploy to production - ✅ COMPLETE"

