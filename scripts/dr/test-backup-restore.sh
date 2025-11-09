#!/bin/bash
#
# Backup Restore Test Script
#
# Tests backup restore procedure in a test environment
#

set -euo pipefail

# Configuration
TEST_DB_NAME="${TEST_DB_NAME:-swe_db_test}"
TEST_DB_USER="${TEST_DB_USER:-swe_user_test}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
TEST_ENV_DIR="${TEST_ENV_DIR:-/tmp/dr-test}"

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

find_latest_backup() {
    local latest_backup=$(find "${BACKUP_DIR}" -name "*.sql.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -z "${latest_backup}" ]]; then
        log_error "No backup found in ${BACKUP_DIR}"
        exit 1
    fi
    
    echo "${latest_backup}"
}

setup_test_environment() {
    log_info "Setting up test environment..."
    
    mkdir -p "${TEST_ENV_DIR}"
    
    # Create test database
    log_info "Creating test database: ${TEST_DB_NAME}"
    export PGPASSWORD="${DB_PASSWORD:-}"
    psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" > /dev/null 2>&1 || true
    psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres \
        -c "CREATE DATABASE ${TEST_DB_NAME};" || {
        log_error "Failed to create test database"
        exit 1
    }
    
    log_info "Test environment ready."
}

restore_backup() {
    local backup_file="$1"
    
    log_info "Restoring backup: ${backup_file}"
    
    # Set environment for restore
    export DB_NAME="${TEST_DB_NAME}"
    export DB_USER="${TEST_DB_USER}"
    
    # Restore backup
    if [[ -f "scripts/db/restore-database.sh" ]]; then
        ./scripts/db/restore-database.sh "${backup_file}" || {
            log_error "Backup restore failed"
            return 1
        }
    else
        log_error "Restore script not found"
        return 1
    fi
    
    log_info "Backup restored successfully."
}

verify_restore() {
    log_info "Verifying restore..."
    
    export PGPASSWORD="${DB_PASSWORD:-}"
    
    # Check table count
    local table_count=$(psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${TEST_DB_NAME}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    
    log_info "Tables found: ${table_count}"
    
    if [[ ${table_count} -eq 0 ]]; then
        log_error "No tables found in restored database"
        return 1
    fi
    
    # Check data integrity (sample queries)
    log_info "Running data integrity checks..."
    
    # Check for common tables
    local checks=(
        "SELECT COUNT(*) FROM auth.users;"
        "SELECT COUNT(*) FROM agents.agent_definitions;"
    )
    
    for check in "${checks[@]}"; do
        if psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${TEST_DB_NAME}" \
            -t -c "${check}" > /dev/null 2>&1; then
            log_info "Data integrity check passed: ${check}"
        else
            log_warn "Data integrity check failed: ${check}"
        fi
    done
    
    log_info "Restore verification complete."
}

cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    
    # Drop test database
    export PGPASSWORD="${DB_PASSWORD:-}"
    psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" > /dev/null 2>&1 || true
    
    # Remove test directory
    rm -rf "${TEST_ENV_DIR}"
    
    log_info "Test environment cleaned up."
}

main() {
    log_info "Starting backup restore test..."
    
    # Find latest backup
    local backup_file
    backup_file=$(find_latest_backup)
    log_info "Testing with backup: ${backup_file}"
    
    # Setup test environment
    setup_test_environment
    
    # Restore backup
    if restore_backup "${backup_file}"; then
        # Verify restore
        if verify_restore; then
            log_info "Backup restore test PASSED"
            cleanup_test_environment
            exit 0
        else
            log_error "Backup restore test FAILED - verification failed"
            cleanup_test_environment
            exit 1
        fi
    else
        log_error "Backup restore test FAILED - restore failed"
        cleanup_test_environment
        exit 1
    fi
}

main "$@"

