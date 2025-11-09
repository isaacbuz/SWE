#!/bin/bash
#
# Production Deployment Script
#
# Automated production deployment with safety checks
#

set -euo pipefail

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
LOG_FILE="${LOG_FILE:-./deployment.log}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_FILE}"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_FILE}"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not found"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
        log_warn ".env.${ENVIRONMENT} not found, using defaults"
    fi
    
    log_info "Prerequisites check passed"
}

backup_database() {
    log_info "Backing up database..."
    
    mkdir -p "${BACKUP_DIR}"
    
    local backup_file="${BACKUP_DIR}/db-backup-$(date +%Y%m%d_%H%M%S).sql.gz"
    
    docker-compose -f "${DOCKER_COMPOSE_FILE}" exec -T postgres \
        pg_dump -U "${DB_USER:-swe_user}" "${DB_NAME:-swe_db}" | \
        gzip > "${backup_file}"
    
    if [[ -f "${backup_file}" ]]; then
        log_info "Database backup created: ${backup_file}"
    else
        log_error "Database backup failed"
        exit 1
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    docker-compose -f "${DOCKER_COMPOSE_FILE}" build --no-cache
    
    log_info "Docker images built successfully"
}

run_migrations() {
    log_info "Running database migrations..."
    
    docker-compose -f "${DOCKER_COMPOSE_FILE}" run --rm api \
        python -m alembic upgrade head
    
    log_info "Database migrations completed"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Start infrastructure services first
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d postgres redis
    
    # Wait for services to be ready
    log_info "Waiting for infrastructure services..."
    sleep 10
    
    # Start application services
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d api tool-service web
    
    # Wait for application services
    log_info "Waiting for application services..."
    sleep 10
    
    # Start reverse proxy
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d nginx
    
    log_info "Services deployed"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check service status
    docker-compose -f "${DOCKER_COMPOSE_FILE}" ps
    
    # Health checks
    local api_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
    
    if [[ "${api_health}" == "200" ]]; then
        log_info "API health check passed"
    else
        log_error "API health check failed: ${api_health}"
        return 1
    fi
    
    log_info "Deployment verification passed"
}

rollback() {
    log_error "Deployment failed. Initiating rollback..."
    
    # Stop services
    docker-compose -f "${DOCKER_COMPOSE_FILE}" down
    
    # Restore database if backup exists
    local latest_backup=$(ls -t "${BACKUP_DIR}"/db-backup-*.sql.gz 2>/dev/null | head -1)
    if [[ -n "${latest_backup}" ]]; then
        log_info "Restoring database from backup: ${latest_backup}"
        gunzip -c "${latest_backup}" | \
            docker-compose -f "${DOCKER_COMPOSE_FILE}" exec -T postgres \
            psql -U "${DB_USER:-swe_user}" "${DB_NAME:-swe_db}"
    fi
    
    log_error "Rollback completed"
    exit 1
}

main() {
    log_info "Starting production deployment..."
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Docker Compose: ${DOCKER_COMPOSE_FILE}"
    
    # Trap errors for rollback
    trap rollback ERR
    
    check_prerequisites
    backup_database
    build_images
    run_migrations
    deploy_services
    verify_deployment
    
    log_info "Production deployment completed successfully!"
    log_info "Monitor logs: docker-compose -f ${DOCKER_COMPOSE_FILE} logs -f"
}

main "$@"

