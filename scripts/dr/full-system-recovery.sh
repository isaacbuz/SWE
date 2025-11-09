#!/bin/bash
#
# Full System Recovery Script
#
# Recovers entire system from scratch in case of catastrophic failure
#

set -euo pipefail

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups}"
TERRAFORM_DIR="${TERRAFORM_DIR:-infrastructure/terraform}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"

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

confirm_recovery() {
    log_warn "WARNING: This will rebuild the entire system!"
    log_warn "All existing data will be replaced!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [[ "${confirm}" != "yes" ]]; then
        log_info "Recovery cancelled"
        exit 0
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("docker" "docker-compose" "psql" "terraform")
    for tool in "${required_tools[@]}"; do
        if ! command -v "${tool}" &> /dev/null; then
            log_error "${tool} not found. Please install it first."
            exit 1
        fi
    done
    
    # Check backup availability
    if [[ ! -d "${BACKUP_DIR}" ]]; then
        log_warn "Backup directory not found: ${BACKUP_DIR}"
        log_info "Attempting to download from S3..."
        # TODO: Download from S3 if available
    fi
    
    log_info "Prerequisites check complete."
}

provision_infrastructure() {
    log_info "Provisioning infrastructure..."
    
    if [[ -d "${TERRAFORM_DIR}" ]]; then
        cd "${TERRAFORM_DIR}"
        
        log_info "Initializing Terraform..."
        terraform init
        
        log_info "Planning infrastructure..."
        terraform plan -var-file="terraform.${ENVIRONMENT}.tfvars"
        
        log_info "Applying infrastructure..."
        terraform apply -var-file="terraform.${ENVIRONMENT}.tfvars" -auto-approve
        
        cd - > /dev/null
        log_info "Infrastructure provisioned."
    else
        log_warn "Terraform directory not found. Skipping infrastructure provisioning."
    fi
}

restore_database() {
    log_info "Restoring database..."
    
    # Find latest backup
    local latest_backup=$(find "${BACKUP_DIR}/postgresql" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -z "${latest_backup}" ]]; then
        log_error "No database backup found"
        exit 1
    fi
    
    log_info "Using backup: ${latest_backup}"
    
    # Restore database
    if [[ -f "scripts/db/restore-database.sh" ]]; then
        ./scripts/db/restore-database.sh "${latest_backup}"
    else
        log_error "Database restore script not found"
        exit 1
    fi
    
    log_info "Database restored."
}

deploy_application() {
    log_info "Deploying application..."
    
    # Pull latest images
    log_info "Pulling Docker images..."
    docker-compose -f "${DOCKER_COMPOSE_FILE}" pull
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Verify services
    log_info "Verifying services..."
    if docker-compose -f "${DOCKER_COMPOSE_FILE}" ps | grep -q "Up"; then
        log_info "Services are running."
    else
        log_error "Some services failed to start"
        docker-compose -f "${DOCKER_COMPOSE_FILE}" ps
        exit 1
    fi
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Check API health
    if command -v curl &> /dev/null; then
        local api_url="${API_URL:-http://localhost:8000}"
        if curl -f "${api_url}/health" > /dev/null 2>&1; then
            log_info "API health check passed"
        else
            log_error "API health check failed"
            return 1
        fi
    fi
    
    # Check database connectivity
    if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-swe_user}" -d "${DB_NAME:-swe_db}" -c "SELECT 1;" > /dev/null 2>&1; then
        log_info "Database connectivity check passed"
    else
        log_error "Database connectivity check failed"
        return 1
    fi
    
    log_info "All health checks passed."
}

main() {
    log_info "Starting full system recovery..."
    log_info "Environment: ${ENVIRONMENT}"
    
    confirm_recovery
    check_prerequisites
    provision_infrastructure
    restore_database
    deploy_application
    run_health_checks
    
    log_info "Full system recovery completed successfully!"
    log_info "Next steps:"
    log_info "1. Verify all services are running"
    log_info "2. Run smoke tests"
    log_info "3. Monitor logs for errors"
    log_info "4. Update status page"
}

main "$@"

