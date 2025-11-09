#!/bin/bash
#
# SSL/TLS Certificate Setup Script
#
# This script sets up SSL/TLS certificates using Let's Encrypt
# for the SWE Platform production deployment.
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${DOMAIN:-example.com}"
EMAIL="${EMAIL:-admin@${DOMAIN}}"
CERTBOT_DIR="${CERTBOT_DIR:-/etc/letsencrypt}"
CERTBOT_WEBROOT="${CERTBOT_WEBROOT:-/var/www/certbot}"
STAGING="${STAGING:-false}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v certbot &> /dev/null; then
        log_error "certbot is not installed. Installing..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update
            sudo apt-get install -y certbot
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install certbot
        else
            log_error "Unsupported OS. Please install certbot manually."
            exit 1
        fi
    fi
    
    log_info "Dependencies check complete."
}

create_directories() {
    log_info "Creating necessary directories..."
    
    sudo mkdir -p "${CERTBOT_DIR}"
    sudo mkdir -p "${CERTBOT_WEBROOT}"
    sudo mkdir -p "${CERTBOT_DIR}/live/${DOMAIN}"
    sudo mkdir -p "${CERTBOT_DIR}/archive/${DOMAIN}"
    sudo mkdir -p "${CERTBOT_DIR}/renewal"
    
    log_info "Directories created."
}

obtain_certificate() {
    log_info "Obtaining SSL certificate for ${DOMAIN}..."
    
    local certbot_args=(
        certonly
        --webroot
        --webroot-path="${CERTBOT_WEBROOT}"
        --email "${EMAIL}"
        --agree-tos
        --no-eff-email
        --keep-until-expiring
        -d "${DOMAIN}"
    )
    
    # Add staging flag if specified
    if [[ "${STAGING}" == "true" ]]; then
        certbot_args+=(--staging)
        log_warn "Using Let's Encrypt staging environment"
    fi
    
    # Add www subdomain if specified
    if [[ -n "${WWW_DOMAIN:-}" ]]; then
        certbot_args+=(-d "${WWW_DOMAIN}")
    fi
    
    if sudo certbot "${certbot_args[@]}"; then
        log_info "Certificate obtained successfully!"
        return 0
    else
        log_error "Failed to obtain certificate"
        return 1
    fi
}

setup_auto_renewal() {
    log_info "Setting up automatic certificate renewal..."
    
    # Create renewal script
    sudo tee /etc/cron.daily/renew-certificates > /dev/null <<EOF
#!/bin/bash
certbot renew --quiet --post-hook "docker-compose -f /path/to/docker-compose.prod.yml restart nginx"
EOF
    
    sudo chmod +x /etc/cron.daily/renew-certificates
    
    # Test renewal
    log_info "Testing certificate renewal..."
    sudo certbot renew --dry-run
    
    log_info "Auto-renewal setup complete."
}

verify_certificate() {
    log_info "Verifying certificate..."
    
    if [[ -f "${CERTBOT_DIR}/live/${DOMAIN}/fullchain.pem" ]] && \
       [[ -f "${CERTBOT_DIR}/live/${DOMAIN}/privkey.pem" ]]; then
        log_info "Certificate files found:"
        ls -lh "${CERTBOT_DIR}/live/${DOMAIN}/"
        
        # Check certificate expiration
        local expiry=$(sudo openssl x509 -enddate -noout -in "${CERTBOT_DIR}/live/${DOMAIN}/fullchain.pem" | cut -d= -f2)
        log_info "Certificate expires on: ${expiry}"
        
        return 0
    else
        log_error "Certificate files not found"
        return 1
    fi
}

main() {
    log_info "Starting SSL/TLS certificate setup..."
    log_info "Domain: ${DOMAIN}"
    log_info "Email: ${EMAIL}"
    log_info "Staging: ${STAGING}"
    
    check_dependencies
    create_directories
    
    if obtain_certificate; then
        verify_certificate
        setup_auto_renewal
        log_info "SSL/TLS certificate setup complete!"
        log_info "Next steps:"
        log_info "1. Update Nginx configuration to use certificates"
        log_info "2. Restart Nginx service"
        log_info "3. Test HTTPS connection"
    else
        log_error "Certificate setup failed"
        exit 1
    fi
}

# Run main function
main "$@"

