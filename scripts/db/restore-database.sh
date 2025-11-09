#!/bin/bash
#
# Database Restore Script
#
# Restores PostgreSQL database from backup file
#

set -euo pipefail

# Configuration
BACKUP_FILE="${1:-}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-swe_db}"
DB_USER="${DB_USER:-swe_user}"
DB_PASSWORD="${DB_PASSWORD:-}"

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

check_backup_file() {
    if [[ -z "${BACKUP_FILE}" ]]; then
        log_error "Backup file not specified"
        echo "Usage: $0 <backup_file>"
        exit 1
    fi
    
    if [[ ! -f "${BACKUP_FILE}" ]]; then
        log_error "Backup file not found: ${BACKUP_FILE}"
        exit 1
    fi
    
    log_info "Backup file: ${BACKUP_FILE}"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v pg_restore &> /dev/null && ! command -v psql &> /dev/null; then
        log_error "PostgreSQL client tools not found"
        exit 1
    fi
    
    if [[ "${BACKUP_FILE}" == *.gz ]] && ! command -v gunzip &> /dev/null; then
        log_error "gunzip not found"
        exit 1
    fi
    
    log_info "Dependencies check complete."
}

confirm_restore() {
    log_warn "WARNING: This will restore database ${DB_NAME} from backup"
    log_warn "All existing data will be replaced!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [[ "${confirm}" != "yes" ]]; then
        log_info "Restore cancelled"
        exit 0
    fi
}

drop_database() {
    log_info "Dropping existing database: ${DB_NAME}"
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    # Terminate existing connections
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
        > /dev/null 2>&1 || true
    
    # Drop database
    if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${DB_NAME};"; then
        log_info "Database dropped"
    else
        log_error "Failed to drop database"
        exit 1
    fi
}

create_database() {
    log_info "Creating database: ${DB_NAME}"
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "CREATE DATABASE ${DB_NAME};"; then
        log_info "Database created"
    else
        log_error "Failed to create database"
        exit 1
    fi
}

restore_backup() {
    log_info "Restoring backup..."
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    # Determine backup format
    if [[ "${BACKUP_FILE}" == *.dump ]] || [[ "${BACKUP_FILE}" == *.dump.gz ]]; then
        # Custom format (pg_dump -F c)
        local restore_file="${BACKUP_FILE}"
        
        if [[ "${BACKUP_FILE}" == *.gz ]]; then
            log_info "Decompressing backup..."
            restore_file="${BACKUP_FILE%.gz}"
            gunzip -c "${BACKUP_FILE}" > "${restore_file}"
        fi
        
        if pg_restore \
            -h "${DB_HOST}" \
            -p "${DB_PORT}" \
            -U "${DB_USER}" \
            -d "${DB_NAME}" \
            -v \
            "${restore_file}"; then
            log_info "Backup restored successfully"
            
            # Clean up temporary file if created
            if [[ "${restore_file}" != "${BACKUP_FILE}" ]]; then
                rm -f "${restore_file}"
            fi
        else
            log_error "Restore failed"
            exit 1
        fi
    else
        # SQL format
        local restore_file="${BACKUP_FILE}"
        
        if [[ "${BACKUP_FILE}" == *.gz ]]; then
            log_info "Decompressing backup..."
            gunzip -c "${BACKUP_FILE}" | psql \
                -h "${DB_HOST}" \
                -p "${DB_PORT}" \
                -U "${DB_USER}" \
                -d "${DB_NAME}" \
                -v
        else
            psql \
                -h "${DB_HOST}" \
                -p "${DB_PORT}" \
                -U "${DB_USER}" \
                -d "${DB_NAME}" \
                -f "${BACKUP_FILE}" \
                -v
        fi
        
        if [[ $? -eq 0 ]]; then
            log_info "Backup restored successfully"
        else
            log_error "Restore failed"
            exit 1
        fi
    fi
}

verify_restore() {
    log_info "Verifying restore..."
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    local table_count=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    
    log_info "Tables in database: ${table_count}"
    
    if [[ ${table_count} -gt 0 ]]; then
        log_info "Restore verification successful"
        return 0
    else
        log_warn "No tables found in database"
        return 1
    fi
}

main() {
    log_info "Starting database restore process..."
    log_info "Database: ${DB_NAME}"
    log_info "Host: ${DB_HOST}:${DB_PORT}"
    
    check_backup_file
    check_dependencies
    confirm_restore
    
    drop_database
    create_database
    restore_backup
    
    if verify_restore; then
        log_info "Database restore completed successfully!"
    else
        log_warn "Restore completed but verification found issues"
    fi
}

main "$@"

