#!/bin/bash
#
# Certificate Renewal Script
#
# This script renews SSL/TLS certificates and reloads Nginx
#

set -euo pipefail

# Configuration
CERTBOT_DIR="${CERTBOT_DIR:-/etc/letsencrypt}"
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

renew_certificates() {
    log_info "Checking for certificate renewal..."
    
    # Renew certificates
    if certbot renew --quiet; then
        log_info "Certificates renewed successfully"
        
        # Reload Nginx
        log_info "Reloading Nginx..."
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "${DOCKER_COMPOSE_FILE}" exec -T nginx nginx -s reload || \
            docker-compose -f "${DOCKER_COMPOSE_FILE}" restart nginx
        elif command -v docker &> /dev/null; then
            docker exec nginx nginx -s reload || docker restart nginx
        else
            sudo systemctl reload nginx || sudo systemctl restart nginx
        fi
        
        log_info "Nginx reloaded"
        return 0
    else
        log_error "Certificate renewal failed"
        return 1
    fi
}

check_certificate_expiry() {
    local domain="${1:-}"
    if [[ -z "${domain}" ]]; then
        log_error "Domain not specified"
        return 1
    fi
    
    local cert_file="${CERTBOT_DIR}/live/${domain}/fullchain.pem"
    if [[ ! -f "${cert_file}" ]]; then
        log_error "Certificate file not found: ${cert_file}"
        return 1
    fi
    
    local expiry_date=$(sudo openssl x509 -enddate -noout -in "${cert_file}" | cut -d= -f2)
    local expiry_epoch=$(date -d "${expiry_date}" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y" "${expiry_date}" +%s 2>/dev/null)
    local current_epoch=$(date +%s)
    local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    log_info "Certificate for ${domain} expires in ${days_until_expiry} days"
    
    if [[ ${days_until_expiry} -lt 30 ]]; then
        log_warn "Certificate expires soon (${days_until_expiry} days). Renewal recommended."
        return 1
    fi
    
    return 0
}

main() {
    local domain="${1:-}"
    
    if [[ -n "${domain}" ]]; then
        check_certificate_expiry "${domain}"
    fi
    
    renew_certificates
}

main "$@"

