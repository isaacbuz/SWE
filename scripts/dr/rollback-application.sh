#!/bin/bash
#
# Application Rollback Script
#
# Rolls back application to a previous version
#

set -euo pipefail

# Configuration
VERSION="${1:-}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
REGISTRY="${REGISTRY:-docker.io}"
IMAGE_NAME="${IMAGE_NAME:-swe-platform}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_version() {
    if [[ -z "${VERSION}" ]]; then
        log_error "Version not specified"
        echo "Usage: $0 <version>"
        echo "Example: $0 v1.0.0"
        exit 1
    fi
    
    log_info "Rolling back to version: ${VERSION}"
}

backup_current_state() {
    log_info "Backing up current state..."
    
    # Backup database before rollback
    if [[ -f "scripts/db/backup-database.sh" ]]; then
        ./scripts/db/backup-database.sh
    fi
    
    # Export current environment
    docker-compose -f "${DOCKER_COMPOSE_FILE}" config > "/tmp/docker-compose-backup-$(date +%Y%m%d_%H%M%S).yml"
    
    log_info "Current state backed up."
}

rollback_docker() {
    log_info "Rolling back Docker containers..."
    
    # Pull previous version
    log_info "Pulling version ${VERSION}..."
    docker pull "${REGISTRY}/${IMAGE_NAME}:${VERSION}" || {
        log_error "Failed to pull version ${VERSION}"
        exit 1
    }
    
    # Update docker-compose to use previous version
    if [[ -f "${DOCKER_COMPOSE_FILE}" ]]; then
        # Create backup
        cp "${DOCKER_COMPOSE_FILE}" "${DOCKER_COMPOSE_FILE}.backup"
        
        # Update image tags (simplified - in production, use proper YAML parsing)
        sed -i.bak "s|${IMAGE_NAME}:.*|${IMAGE_NAME}:${VERSION}|g" "${DOCKER_COMPOSE_FILE}"
        
        # Restart services
        log_info "Restarting services with version ${VERSION}..."
        docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d --force-recreate
        
        log_info "Rollback complete."
    else
        log_error "Docker Compose file not found: ${DOCKER_COMPOSE_FILE}"
        exit 1
    fi
}

rollback_kubernetes() {
    log_info "Rolling back Kubernetes deployment..."
    
    if command -v kubectl &> /dev/null; then
        # Rollback deployment
        kubectl rollout undo deployment/swe-api -n production
        
        # Wait for rollout
        kubectl rollout status deployment/swe-api -n production
        
        log_info "Kubernetes rollback complete."
    else
        log_warn "kubectl not found. Skipping Kubernetes rollback."
    fi
}

verify_rollback() {
    log_info "Verifying rollback..."
    
    # Wait for services to stabilize
    sleep 10
    
    # Check service health
    if docker-compose -f "${DOCKER_COMPOSE_FILE}" ps | grep -q "Up"; then
        log_info "Services are running."
    else
        log_error "Some services failed to start"
        return 1
    fi
    
    # Check API health
    if command -v curl &> /dev/null; then
        local api_url="${API_URL:-http://localhost:8000}"
        if curl -f "${api_url}/health" > /dev/null 2>&1; then
            log_info "API health check passed"
        else
            log_warn "API health check failed - may need manual intervention"
        fi
    fi
    
    log_info "Rollback verification complete."
}

main() {
    log_info "Starting application rollback..."
    
    check_version
    backup_current_state
    
    # Determine deployment method
    if [[ -f "${DOCKER_COMPOSE_FILE}" ]]; then
        rollback_docker
    elif command -v kubectl &> /dev/null; then
        rollback_kubernetes
    else
        log_error "No deployment method found"
        exit 1
    fi
    
    verify_rollback
    
    log_info "Application rollback completed successfully!"
    log_info "Next steps:"
    log_info "1. Verify application functionality"
    log_info "2. Monitor logs for errors"
    log_info "3. Investigate root cause of issue"
    log_info "4. Fix issue and prepare new deployment"
}

main "$@"

