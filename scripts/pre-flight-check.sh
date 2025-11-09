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
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*"
}

# Check counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNINGS=0

check_pass() {
    log_success "$1"
    ((CHECKS_PASSED++)) || true
}

check_fail() {
    log_error "$1"
    ((CHECKS_FAILED++)) || true
}

check_warn() {
    log_warn "$1"
    ((CHECKS_WARNINGS++)) || true
}

log_info "=== Production Deployment Pre-Flight Check ==="
echo ""

# 1. Check required tools
log_info "Checking required tools..."

if command -v kubectl &> /dev/null; then
    check_pass "kubectl installed"
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3)
    log_info "  Version: $KUBECTL_VERSION"
else
    check_fail "kubectl not installed"
fi

if command -v gcloud &> /dev/null; then
    check_pass "gcloud installed"
    GCLOUD_VERSION=$(gcloud --version | head -n1)
    log_info "  $GCLOUD_VERSION"
else
    check_fail "gcloud not installed"
fi

if command -v terraform &> /dev/null; then
    check_pass "terraform installed"
    TERRAFORM_VERSION=$(terraform version | head -n1)
    log_info "  $TERRAFORM_VERSION"
else
    check_warn "terraform not installed (optional)"
fi

if command -v kustomize &> /dev/null; then
    check_pass "kustomize installed"
else
    check_warn "kustomize not installed (optional, can use kubectl apply -k)"
fi

echo ""

# 2. Check GCP authentication
log_info "Checking GCP authentication..."

if gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
    check_pass "GCP authenticated"
    log_info "  Account: $ACTIVE_ACCOUNT"
else
    check_fail "GCP not authenticated - run: gcloud auth login"
fi

if gcloud config get-value project &> /dev/null; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    check_pass "GCP project configured"
    log_info "  Project: $PROJECT_ID"
else
    check_fail "GCP project not configured - run: gcloud config set project PROJECT_ID"
fi

echo ""

# 3. Check Kubernetes access
log_info "Checking Kubernetes cluster access..."

if kubectl cluster-info &> /dev/null; then
    check_pass "Kubernetes cluster accessible"
    CLUSTER_NAME=$(kubectl config current-context 2>/dev/null || echo "unknown")
    log_info "  Context: $CLUSTER_NAME"
else
    check_warn "Kubernetes cluster not accessible - will need to configure during deployment"
fi

echo ""

# 4. Check required files
log_info "Checking required files..."

if [ -f "$PROJECT_ROOT/scripts/deploy-production.sh" ]; then
    check_pass "Deployment script exists"
else
    check_fail "Deployment script not found: scripts/deploy-production.sh"
fi

if [ -d "$PROJECT_ROOT/infrastructure/kubernetes/overlays/production" ]; then
    check_pass "Production Kubernetes manifests exist"
else
    check_fail "Production Kubernetes manifests not found"
fi

if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/cert-manager/cluster-issuer.yaml" ]; then
    check_pass "SSL/TLS certificate configuration exists"
else
    check_warn "SSL/TLS certificate configuration not found"
fi

if [ -f "$PROJECT_ROOT/infrastructure/deployment/DEPLOYMENT_GUIDE.md" ]; then
    check_pass "Deployment documentation exists"
else
    check_warn "Deployment documentation not found"
fi

echo ""

# 5. Check environment variables
log_info "Checking environment variables..."

if [ -n "${GCP_PROJECT_ID:-}" ]; then
    check_pass "GCP_PROJECT_ID set"
else
    check_warn "GCP_PROJECT_ID not set (will use gcloud config)"
fi

if [ -n "${GKE_CLUSTER:-}" ]; then
    check_pass "GKE_CLUSTER set"
    log_info "  Cluster: $GKE_CLUSTER"
else
    check_warn "GKE_CLUSTER not set (will need to be specified)"
fi

if [ -n "${GKE_REGION:-}" ]; then
    check_pass "GKE_REGION set"
    log_info "  Region: $GKE_REGION"
else
    check_warn "GKE_REGION not set (will default to us-central1)"
fi

echo ""

# 6. Check secrets availability
log_info "Checking secrets availability..."

if gcloud secrets list &> /dev/null; then
    check_pass "Google Secret Manager accessible"
    
    # Check for common secrets
    REQUIRED_SECRETS=("database-url" "jwt-secret" "redis-url")
    for secret in "${REQUIRED_SECRETS[@]}"; do
        if gcloud secrets describe "$secret" &> /dev/null; then
            check_pass "Secret '$secret' exists"
        else
            check_warn "Secret '$secret' not found - may need to create"
        fi
    done
else
    check_warn "Google Secret Manager not accessible - verify permissions"
fi

echo ""

# 7. Check Docker images
log_info "Checking Docker images..."

# This would check if images are built and pushed
# For now, just check if Docker is available
if command -v docker &> /dev/null; then
    check_pass "Docker installed"
    if docker info &> /dev/null; then
        check_pass "Docker daemon running"
    else
        check_warn "Docker daemon not running"
    fi
else
    check_warn "Docker not installed (may not be needed if using CI/CD)"
fi

echo ""

# 8. Summary
log_info "=== Pre-Flight Check Summary ==="
echo ""
echo "Passed:  $CHECKS_PASSED"
echo "Failed:  $CHECKS_FAILED"
echo "Warnings: $CHECKS_WARNINGS"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    log_success "All critical checks passed! Ready for deployment."
    echo ""
    log_info "Next steps:"
    echo "  1. Review deployment guide: infrastructure/deployment/DEPLOYMENT_GUIDE.md"
    echo "  2. Execute deployment: ./scripts/deploy-production.sh"
    echo "  3. Monitor deployment: kubectl get pods -n piehr"
    exit 0
else
    log_error "Some critical checks failed. Please fix issues before deploying."
    echo ""
    log_info "Review the errors above and fix them before proceeding."
    exit 1
fi

