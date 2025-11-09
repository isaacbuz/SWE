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
LOG_FILE="$PROJECT_ROOT/secret-rotation.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$PROJECT_ROOT/.secret-backups/$TIMESTAMP"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

# Initialize log file
mkdir -p "$(dirname "$LOG_FILE")" ".secret-backups"
> "$LOG_FILE"

echo ""
log_info "Starting secret rotation process..."
log_info "Timestamp: $TIMESTAMP"
echo ""

# ============================================================================
# Configuration
# ============================================================================

# Secrets to rotate
declare -A SECRETS=(
    [JWT_SECRET]="32"
    [SESSION_SECRET]="32"
    [ENCRYPTION_KEY]="32"
)

# API Keys that should be rotated
declare -a API_KEYS=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "GITHUB_TOKEN"
    "SLACK_BOT_TOKEN"
)

# ============================================================================
# Utility Functions
# ============================================================================

# Generate a random secret of specified length
generate_secret() {
    local length=$1
    openssl rand -base64 "$length" | tr -d '\n'
}

# Generate a secure random token
generate_token() {
    openssl rand -hex 32
}

# Backup current secrets
backup_secrets() {
    log_info "Backing up current secrets..."
    mkdir -p "$BACKUP_DIR"

    if [ -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env" "$BACKUP_DIR/.env.backup"
        log_success "Backup created at $BACKUP_DIR/.env.backup"
    else
        log_warn ".env file not found, skipping backup"
    fi
}

# Update secret in .env file
update_env_secret() {
    local key=$1
    local value=$2
    local env_file=$3

    if [ ! -f "$env_file" ]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi

    # Escape special characters in the value
    local escaped_value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')

    if grep -q "^$key=" "$env_file"; then
        sed -i.bak "s/^$key=.*/$key=$escaped_value/" "$env_file"
        log_success "Updated $key in environment file"
    else
        echo "$key=$value" >> "$env_file"
        log_success "Added $key to environment file"
    fi
}

# Rotate symmetric encryption keys
rotate_symmetric_keys() {
    log_info "Rotating symmetric encryption keys..."
    echo ""

    for key in "${!SECRETS[@]}"; do
        log_info "Rotating $key..."
        local new_secret=$(generate_secret "${SECRETS[$key]}")
        update_env_secret "$key" "$new_secret" "$PROJECT_ROOT/.env"
        log_success "$key rotated successfully"
    done

    echo ""
}

# Update API keys (requires manual action or external provider integration)
update_api_keys() {
    log_info "Checking API keys for rotation..."
    echo ""

    for key in "${API_KEYS[@]}"; do
        log_info "Review $key - manual action may be required"
        log_info "Instructions:"

        case $key in
            OPENAI_API_KEY)
                echo "  1. Go to https://platform.openai.com/account/api-keys"
                echo "  2. Create a new API key"
                echo "  3. Update .env with the new key"
                ;;
            ANTHROPIC_API_KEY)
                echo "  1. Go to https://console.anthropic.com"
                echo "  2. Create a new API key"
                echo "  3. Update .env with the new key"
                ;;
            GITHUB_TOKEN)
                echo "  1. Go to https://github.com/settings/tokens"
                echo "  2. Create a new Personal Access Token"
                echo "  3. Update .env with the new token"
                ;;
            SLACK_BOT_TOKEN)
                echo "  1. Go to https://api.slack.com/apps"
                echo "  2. Regenerate the bot token"
                echo "  3. Update .env with the new token"
                ;;
        esac
        echo ""
    done
}

# Rotate database password
rotate_db_password() {
    log_info "Rotating database credentials..."
    echo ""

    local db_type=${1:-postgresql}

    case $db_type in
        postgresql)
            log_info "To rotate PostgreSQL password:"
            echo "  1. Connect to your database"
            echo "  2. Run: ALTER USER postgres WITH PASSWORD 'new_password';"
            echo "  3. Update DATABASE_PASSWORD in .env"
            echo "  4. Update Docker environment if using local containers"
            ;;
        mysql)
            log_info "To rotate MySQL password:"
            echo "  1. Connect to your database"
            echo "  2. Run: ALTER USER 'user'@'localhost' IDENTIFIED BY 'new_password';"
            echo "  3. Update DATABASE_PASSWORD in .env"
            ;;
        mongodb)
            log_info "To rotate MongoDB credentials:"
            echo "  1. Connect to MongoDB"
            echo "  2. Run: db.changeUserPassword('username', 'newPassword')"
            echo "  3. Update DATABASE_URL in .env"
            ;;
    esac
    echo ""
}

# Rotate Redis password
rotate_redis_password() {
    log_info "Rotating Redis password..."
    echo ""

    log_info "To rotate Redis password:"
    echo "  1. If using local Redis:"
    echo "     - Update redis.conf with new requirepass"
    echo "     - Restart Redis service"
    echo "  2. If using managed Redis (ElastiCache, Memorystore):"
    echo "     - Use the provider's console to rotate"
    echo "  3. Update REDIS_PASSWORD in .env"
    echo ""
}

# Update secrets in external secret management systems
update_external_secrets() {
    log_info "Updating external secret management systems..."
    echo ""

    log_info "GitHub Secrets (if using GitHub Actions):"
    echo "  1. Go to https://github.com/YOUR_ORG/YOUR_REPO/settings/secrets/actions"
    echo "  2. Update each secret with new values:"

    for key in "${!SECRETS[@]}"; do
        echo "     - $key"
    done

    echo ""
    echo "  Commands for GitHub CLI:"
    for key in "${!SECRETS[@]}"; do
        local new_value=$(generate_secret "${SECRETS[$key]}")
        echo "  gh secret set $key --body '$new_value'"
    done

    echo ""

    log_info "AWS Secrets Manager (if using AWS):"
    echo "  aws secretsmanager update-secret --secret-id ai-company-secrets --secret-string '{...}'"
    echo ""

    log_info "Google Secret Manager (if using GCP):"
    echo "  gcloud secrets versions add ai-company-secrets --data-file=secrets.json"
    echo ""

    log_info "HashiCorp Vault (if using Vault):"
    echo "  vault kv put secret/ai-company-platform key=value"
    echo ""
}

# Validate environment after rotation
validate_environment() {
    log_info "Validating environment configuration..."
    echo ""

    local validation_ok=true

    # Check for required secrets
    local required_secrets=("JWT_SECRET" "ENCRYPTION_KEY" "DATABASE_URL" "REDIS_URL")

    for secret in "${required_secrets[@]}"; do
        if grep -q "^$secret=" "$PROJECT_ROOT/.env"; then
            local value=$(grep "^$secret=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
            if [ -z "$value" ] || [ "$value" = "your-super-secret-jwt-key-change-in-production" ]; then
                log_warn "$secret still has default or empty value"
                validation_ok=false
            else
                log_success "$secret is configured"
            fi
        else
            log_error "$secret is missing from .env"
            validation_ok=false
        fi
    done

    echo ""
    return $([ "$validation_ok" = true ] && echo 0 || echo 1)
}

# Notify services of secret rotation
notify_services() {
    log_info "Notifying services of secret rotation..."
    echo ""

    log_info "Recommended notification steps:"
    echo "  1. Restart application services:"
    echo "     - pnpm dev (for local development)"
    echo "     - Docker containers: docker-compose restart"
    echo "     - Kubernetes pods: kubectl rollout restart deployment/app-name"
    echo ""
    echo "  2. Verify services are running:"
    echo "     - Check application logs for errors"
    echo "     - Run health checks"
    echo "     - Test critical flows"
    echo ""
    echo "  3. Update monitoring alerts if needed"
    echo ""
}

# ============================================================================
# Main Rotation Flow
# ============================================================================

main() {
    # Ensure we're in the project root
    if [ ! -f "$PROJECT_ROOT/.env.example" ]; then
        log_error "Project root not found. Please run this script from the project directory."
        exit 1
    fi

    # Check for required commands
    if ! command -v openssl >/dev/null 2>&1; then
        log_error "openssl is required but not installed"
        exit 1
    fi

    # Parse command line arguments
    local rotation_type="${1:-all}"

    echo "Secret Rotation Plan:"
    echo "  - Timestamp: $TIMESTAMP"
    echo "  - Backup: $BACKUP_DIR"
    echo "  - Rotation Type: $rotation_type"
    echo ""

    # Confirm before proceeding
    echo -e "${YELLOW}⚠️  This script will rotate secrets in your .env file${NC}"
    read -p "Are you sure you want to proceed? (yes/no): " -r confirm

    if [[ ! $confirm =~ ^[Yy][Ee][Ss]$ ]]; then
        log_warn "Secret rotation cancelled"
        exit 0
    fi

    echo ""

    # Perform rotation
    backup_secrets

    case $rotation_type in
        all)
            rotate_symmetric_keys
            update_api_keys
            rotate_db_password
            rotate_redis_password
            update_external_secrets
            ;;
        symmetric)
            rotate_symmetric_keys
            ;;
        api-keys)
            update_api_keys
            ;;
        database)
            rotate_db_password
            ;;
        redis)
            rotate_redis_password
            ;;
        external)
            update_external_secrets
            ;;
        *)
            log_error "Unknown rotation type: $rotation_type"
            echo "Valid types: all, symmetric, api-keys, database, redis, external"
            exit 1
            ;;
    esac

    # Validate and notify
    echo ""
    validate_environment || log_warn "Validation found issues"
    echo ""
    notify_services

    echo ""
    echo -e "${GREEN}========================================${NC}"
    log_success "Secret rotation process completed!"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    log_info "Backup location: $BACKUP_DIR"
    log_info "Log file: $LOG_FILE"
    echo ""
}

# Run main function
main "$@"
