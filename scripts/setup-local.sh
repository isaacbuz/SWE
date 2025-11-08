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
LOG_FILE="$PROJECT_ROOT/setup.log"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get installed version
get_version() {
    local cmd="$1"
    local flag="${2:---version}"
    $cmd $flag 2>/dev/null | head -n 1
}

# Initialize log file
> "$LOG_FILE"

echo ""
log_info "Starting AI Company Platform local environment setup..."
echo ""

# ============================================================================
# 1. Check Dependencies
# ============================================================================
log_info "Checking dependencies..."

check_node() {
    if command_exists node; then
        local version=$(get_version node)
        log_success "Node.js found: $version"

        # Check minimum version (14.x)
        local major_version=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$major_version" -lt 14 ]; then
            log_error "Node.js 14.x or higher required"
            return 1
        fi
        return 0
    else
        log_error "Node.js is not installed"
        log_info "Install from: https://nodejs.org/"
        return 1
    fi
}

check_npm() {
    if command_exists npm; then
        local version=$(get_version npm)
        log_success "npm found: $version"
        return 0
    else
        log_error "npm is not installed"
        return 1
    fi
}

check_pnpm() {
    if command_exists pnpm; then
        local version=$(get_version pnpm)
        log_success "pnpm found: $version"
        return 0
    else
        log_warn "pnpm is not installed, installing globally..."
        npm install -g pnpm >> "$LOG_FILE" 2>&1
        log_success "pnpm installed globally"
        return 0
    fi
}

check_docker() {
    if command_exists docker; then
        local version=$(get_version docker)
        log_success "Docker found: $version"

        if ! docker ps >/dev/null 2>&1; then
            log_error "Docker daemon is not running"
            log_info "Start Docker Desktop or the Docker daemon"
            return 1
        fi
        return 0
    else
        log_error "Docker is not installed"
        log_info "Install from: https://www.docker.com/products/docker-desktop"
        return 1
    fi
}

check_docker_compose() {
    if command_exists docker-compose; then
        local version=$(get_version docker-compose)
        log_success "Docker Compose found: $version"
        return 0
    else
        log_warn "docker-compose not found, checking Docker Compose V2..."
        if docker compose version >/dev/null 2>&1; then
            log_success "Docker Compose V2 found"
            return 0
        else
            log_error "Docker Compose is not installed"
            return 1
        fi
    fi
}

check_python() {
    if command_exists python3; then
        local version=$(get_version python3)
        log_success "Python 3 found: $version"
        return 0
    else
        log_warn "Python 3 is not installed (optional for this project)"
        return 0
    fi
}

check_git() {
    if command_exists git; then
        local version=$(get_version git)
        log_success "Git found: $version"
        return 0
    else
        log_error "Git is not installed"
        return 1
    fi
}

# Run dependency checks
dependencies_ok=true
check_node || dependencies_ok=false
check_npm || dependencies_ok=false
check_pnpm || dependencies_ok=false
check_docker || dependencies_ok=false
check_docker_compose || dependencies_ok=false
check_python || true
check_git || dependencies_ok=false

if [ "$dependencies_ok" = false ]; then
    log_error "Missing critical dependencies. Please install them and try again."
    exit 1
fi

echo ""

# ============================================================================
# 2. Setup Environment Files
# ============================================================================
log_info "Setting up environment configuration..."

if [ ! -f "$PROJECT_ROOT/.env.example" ]; then
    log_error ".env.example not found at $PROJECT_ROOT"
    exit 1
fi

if [ -f "$PROJECT_ROOT/.env" ]; then
    log_warn ".env already exists, backing up to .env.backup"
    cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.env.backup"
else
    log_info "Creating .env from .env.example"
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    log_success ".env file created"
fi

# Validate required environment variables
log_info "Validating required environment variables..."

required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "NODE_ENV"
    "JWT_SECRET"
)

missing_vars=false
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" "$PROJECT_ROOT/.env"; then
        log_warn "Required variable $var not found in .env"
        missing_vars=true
    fi
done

if [ "$missing_vars" = true ]; then
    log_warn "Some required variables are missing. Please update .env file manually."
fi

# Set development defaults if not already set
if ! grep -q "^NODE_ENV=" "$PROJECT_ROOT/.env"; then
    echo "NODE_ENV=development" >> "$PROJECT_ROOT/.env"
fi

echo ""

# ============================================================================
# 3. Install Dependencies
# ============================================================================
log_info "Installing Node.js dependencies..."

cd "$PROJECT_ROOT"
pnpm install >> "$LOG_FILE" 2>&1
log_success "Dependencies installed"

echo ""

# ============================================================================
# 4. Docker Setup
# ============================================================================
log_info "Setting up Docker containers..."

if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    log_warn "docker-compose.yml not found, skipping container setup"
else
    log_info "Starting Docker containers..."

    # Stop any existing containers
    docker-compose down >> "$LOG_FILE" 2>&1 || true

    # Start containers
    docker-compose up -d >> "$LOG_FILE" 2>&1

    log_success "Docker containers started"

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 5

    # Check if PostgreSQL is ready
    if command_exists psql; then
        local max_attempts=30
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if PGPASSWORD=postgres psql -h localhost -U postgres -d ai_company_db -c "SELECT 1" > /dev/null 2>&1; then
                log_success "PostgreSQL is ready"
                break
            fi
            attempt=$((attempt + 1))
            sleep 1
        done

        if [ $attempt -eq $max_attempts ]; then
            log_warn "PostgreSQL took longer than expected to start"
        fi
    fi
fi

echo ""

# ============================================================================
# 5. Database Setup
# ============================================================================
log_info "Setting up database..."

# Check if migrations exist
if [ -d "$PROJECT_ROOT/packages/database/migrations" ] || [ -d "$PROJECT_ROOT/migrations" ]; then
    log_info "Running database migrations..."

    if [ -f "$PROJECT_ROOT/package.json" ] && grep -q "prisma" "$PROJECT_ROOT/package.json"; then
        log_info "Using Prisma for migrations..."
        cd "$PROJECT_ROOT"
        pnpm exec prisma migrate deploy >> "$LOG_FILE" 2>&1 || {
            log_warn "Prisma migration had issues, this may be expected on first run"
        }
    fi
else
    log_info "No migrations found, skipping migration step"
fi

echo ""

# ============================================================================
# 6. Development Tools Setup
# ============================================================================
log_info "Setting up development tools..."

# Install Husky for git hooks if available
if [ -f "$PROJECT_ROOT/package.json" ] && grep -q "husky" "$PROJECT_ROOT/package.json"; then
    log_info "Setting up Husky git hooks..."
    cd "$PROJECT_ROOT"
    pnpm exec husky install >> "$LOG_FILE" 2>&1 || {
        log_warn "Husky setup had issues, skipping"
    }
fi

# Setup pre-commit hooks
if [ -f "$PROJECT_ROOT/.githooks/pre-commit" ]; then
    log_info "Configuring git hooks..."
    git config core.hooksPath .githooks >> "$LOG_FILE" 2>&1
fi

echo ""

# ============================================================================
# 7. Environment Validation
# ============================================================================
log_info "Validating environment setup..."

# Check required directories
required_dirs=(
    "apps"
    "packages"
    "infrastructure"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$PROJECT_ROOT/$dir" ]; then
        log_warn "Expected directory not found: $PROJECT_ROOT/$dir"
    fi
done

echo ""

# ============================================================================
# 8. Quick Start Information
# ============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
log_success "Setup completed successfully!"
echo -e "${GREEN}========================================${NC}"
echo ""
log_info "Next steps:"
echo "  1. Update .env file with your actual credentials"
echo "  2. Run: pnpm install (already done)"
echo "  3. Run: pnpm dev (to start development servers)"
echo "  4. Run: docker-compose logs -f (to monitor containers)"
echo ""
log_info "Useful commands:"
echo "  - pnpm dev              Start development servers"
echo "  - pnpm build            Build for production"
echo "  - pnpm test             Run tests"
echo "  - pnpm lint             Run linters"
echo "  - docker-compose logs   View Docker container logs"
echo "  - docker-compose down   Stop all containers"
echo ""
log_info "Documentation:"
echo "  - Setup Guide: $PROJECT_ROOT/docs/SETUP.md"
echo "  - Env Variables: $PROJECT_ROOT/.env.example"
echo "  - Infrastructure: $PROJECT_ROOT/infrastructure/"
echo ""
log_info "Setup log saved to: $LOG_FILE"
echo ""

exit 0
