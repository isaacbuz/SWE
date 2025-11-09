#!/bin/bash
#
# Backup Scheduling Script
#
# Sets up automated database backups using cron
#

set -euo pipefail

# Configuration
BACKUP_SCRIPT="${BACKUP_SCRIPT:-$(dirname $0)/backup-database.sh}"
CRON_SCHEDULE="${CRON_SCHEDULE:-0 2 * * *}"  # Daily at 2 AM
CRON_USER="${CRON_USER:-$USER}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_backup_script() {
    if [[ ! -f "${BACKUP_SCRIPT}" ]]; then
        log_error "Backup script not found: ${BACKUP_SCRIPT}"
        exit 1
    fi
    
    if [[ ! -x "${BACKUP_SCRIPT}" ]]; then
        log_warn "Making backup script executable..."
        chmod +x "${BACKUP_SCRIPT}"
    fi
}

install_cron_job() {
    log_info "Installing cron job for user: ${CRON_USER}"
    
    # Create cron job entry
    local cron_entry="${CRON_SCHEDULE} ${BACKUP_SCRIPT} >> /var/log/db-backup.log 2>&1"
    
    # Check if cron job already exists
    if crontab -u "${CRON_USER}" -l 2>/dev/null | grep -q "${BACKUP_SCRIPT}"; then
        log_warn "Cron job already exists. Updating..."
        crontab -u "${CRON_USER}" -l 2>/dev/null | grep -v "${BACKUP_SCRIPT}" | crontab -u "${CRON_USER}" -
    fi
    
    # Add new cron job
    (crontab -u "${CRON_USER}" -l 2>/dev/null; echo "${cron_entry}") | crontab -u "${CRON_USER}" -
    
    log_info "Cron job installed successfully"
    log_info "Schedule: ${CRON_SCHEDULE}"
    log_info "Script: ${BACKUP_SCRIPT}"
}

list_cron_jobs() {
    log_info "Current cron jobs for ${CRON_USER}:"
    crontab -u "${CRON_USER}" -l 2>/dev/null | grep -E "(backup|database)" || log_warn "No backup cron jobs found"
}

remove_cron_job() {
    log_info "Removing cron job..."
    
    if crontab -u "${CRON_USER}" -l 2>/dev/null | grep -q "${BACKUP_SCRIPT}"; then
        crontab -u "${CRON_USER}" -l 2>/dev/null | grep -v "${BACKUP_SCRIPT}" | crontab -u "${CRON_USER}" -
        log_info "Cron job removed"
    else
        log_warn "Cron job not found"
    fi
}

main() {
    local action="${1:-install}"
    
    case "${action}" in
        install)
            check_backup_script
            install_cron_job
            list_cron_jobs
            ;;
        list)
            list_cron_jobs
            ;;
        remove)
            remove_cron_job
            ;;
        *)
            echo "Usage: $0 {install|list|remove}"
            exit 1
            ;;
    esac
}

main "$@"

