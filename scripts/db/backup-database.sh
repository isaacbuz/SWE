#!/bin/bash
#
# Database Backup Script
#
# Creates PostgreSQL database backups with compression and optional S3 upload
#

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-postgresql-backups/}"
COMPRESSION="${COMPRESSION:-gzip}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database connection (from environment or defaults)
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

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. Please install PostgreSQL client tools."
        exit 1
    fi
    
    if [[ "${COMPRESSION}" == "gzip" ]] && ! command -v gzip &> /dev/null; then
        log_error "gzip not found"
        exit 1
    fi
    
    if [[ -n "${S3_BUCKET}" ]] && ! command -v aws &> /dev/null; then
        log_warn "AWS CLI not found. S3 upload will be skipped."
    fi
    
    log_info "Dependencies check complete."
}

create_backup_directory() {
    log_info "Creating backup directory..."
    mkdir -p "${BACKUP_DIR}"
    log_info "Backup directory: ${BACKUP_DIR}"
}

create_backup() {
    local backup_file="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.${COMPRESSION}"
    
    log_info "Creating backup of database: ${DB_NAME}"
    
    # Set PGPASSWORD environment variable
    export PGPASSWORD="${DB_PASSWORD}"
    
    # Create backup
    if pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -F c \
        -f "${backup_file}.dump" \
        --verbose; then
        
        log_info "Backup created: ${backup_file}.dump"
        
        # Compress if requested
        if [[ "${COMPRESSION}" == "gzip" ]]; then
            log_info "Compressing backup..."
            gzip -c "${backup_file}.dump" > "${compressed_file}"
            rm -f "${backup_file}.dump"
            log_info "Compressed backup: ${compressed_file}"
            echo "${compressed_file}"
        else
            echo "${backup_file}.dump"
        fi
    else
        log_error "Backup failed"
        exit 1
    fi
}

upload_to_s3() {
    local backup_file="$1"
    
    if [[ -z "${S3_BUCKET}" ]]; then
        log_info "S3 bucket not configured. Skipping upload."
        return 0
    fi
    
    if ! command -v aws &> /dev/null; then
        log_warn "AWS CLI not available. Skipping S3 upload."
        return 0
    fi
    
    log_info "Uploading backup to S3: s3://${S3_BUCKET}/${S3_PREFIX}$(basename ${backup_file})"
    
    if aws s3 cp "${backup_file}" "s3://${S3_BUCKET}/${S3_PREFIX}$(basename ${backup_file})"; then
        log_info "Backup uploaded to S3 successfully"
        
        # Optionally remove local backup after successful upload
        if [[ "${REMOVE_LOCAL_AFTER_S3_UPLOAD:-false}" == "true" ]]; then
            log_info "Removing local backup after successful S3 upload"
            rm -f "${backup_file}"
        fi
    else
        log_error "S3 upload failed"
        return 1
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
    
    local deleted_count=0
    while IFS= read -r -d '' backup_file; do
        if [[ -f "${backup_file}" ]]; then
            rm -f "${backup_file}"
            ((deleted_count++))
            log_info "Deleted old backup: $(basename ${backup_file})"
        fi
    done < <(find "${BACKUP_DIR}" -type f -name "${DB_NAME}_*.sql*" -mtime +${RETENTION_DAYS} -print0)
    
    log_info "Cleaned up ${deleted_count} old backup(s)"
}

verify_backup() {
    local backup_file="$1"
    
    log_info "Verifying backup: ${backup_file}"
    
    # Check file exists and has size
    if [[ ! -f "${backup_file}" ]]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi
    
    local file_size=$(stat -f%z "${backup_file}" 2>/dev/null || stat -c%s "${backup_file}" 2>/dev/null)
    if [[ ${file_size} -eq 0 ]]; then
        log_error "Backup file is empty: ${backup_file}"
        return 1
    fi
    
    log_info "Backup verified: ${file_size} bytes"
    return 0
}

main() {
    log_info "Starting database backup process..."
    log_info "Database: ${DB_NAME}"
    log_info "Host: ${DB_HOST}:${DB_PORT}"
    log_info "Backup directory: ${BACKUP_DIR}"
    log_info "Retention: ${RETENTION_DAYS} days"
    
    check_dependencies
    create_backup_directory
    
    local backup_file
    if backup_file=$(create_backup); then
        if verify_backup "${backup_file}"; then
            if [[ -n "${S3_BUCKET}" ]]; then
                upload_to_s3 "${backup_file}"
            fi
            cleanup_old_backups
            log_info "Backup process completed successfully!"
            log_info "Backup file: ${backup_file}"
        else
            log_error "Backup verification failed"
            exit 1
        fi
    else
        log_error "Backup creation failed"
        exit 1
    fi
}

main "$@"

