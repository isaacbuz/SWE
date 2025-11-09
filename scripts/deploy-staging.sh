#!/bin/bash

# Deploy SWE Platform to Staging Environment
# Usage: ./scripts/deploy-staging.sh [--build] [--restart]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Check if .env.staging exists
if [ ! -f ".env.staging" ]; then
    log_error ".env.staging file not found!"
    log_info "Creating .env.staging from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env.staging
        log_warn "Please update .env.staging with your staging configuration"
    else
        log_error ".env.example not found. Please create .env.staging manually."
        exit 1
    fi
fi

# Load environment variables
export $(cat .env.staging | grep -v '^#' | xargs)

# Parse arguments
BUILD=false
RESTART=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD=true
            shift
            ;;
        --restart)
            RESTART=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Stop existing containers if restarting
if [ "$RESTART" = true ]; then
    log_info "Stopping existing staging containers..."
    docker-compose -f docker-compose.staging.yml down || true
fi

# Build images if requested
if [ "$BUILD" = true ]; then
    log_info "Building Docker images..."
    docker-compose -f docker-compose.staging.yml build --no-cache
fi

# Start services
log_info "Starting staging environment..."
docker-compose -f docker-compose.staging.yml up -d

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

# Check health endpoints
log_info "Checking service health..."

# API health check
if curl -f http://localhost:${API_PORT:-8000}/health > /dev/null 2>&1; then
    log_info "✓ API service is healthy"
else
    log_warn "✗ API service health check failed"
fi

# Tool service health check
if curl -f http://localhost:${TOOL_SERVICE_PORT:-3001}/health > /dev/null 2>&1; then
    log_info "✓ Tool service is healthy"
else
    log_warn "✗ Tool service health check failed"
fi

# Prometheus health check
if curl -f http://localhost:${PROMETHEUS_PORT:-9090}/-/healthy > /dev/null 2>&1; then
    log_info "✓ Prometheus is healthy"
else
    log_warn "✗ Prometheus health check failed"
fi

# Grafana health check
if curl -f http://localhost:${GRAFANA_PORT:-3000}/api/health > /dev/null 2>&1; then
    log_info "✓ Grafana is healthy"
else
    log_warn "✗ Grafana health check failed"
fi

# Display service URLs
log_info ""
log_info "=== Staging Environment Deployed ==="
log_info ""
log_info "Service URLs:"
log_info "  API:              http://localhost:${API_PORT:-8000}"
log_info "  API Docs:         http://localhost:${API_PORT:-8000}/docs"
log_info "  Tool Service:     http://localhost:${TOOL_SERVICE_PORT:-3001}"
log_info "  Web Frontend:     http://localhost:${WEB_PORT:-3000}"
log_info "  Prometheus:       http://localhost:${PROMETHEUS_PORT:-9090}"
log_info "  Grafana:          http://localhost:${GRAFANA_PORT:-3000}"
log_info ""
log_info "Grafana Credentials:"
log_info "  Username: admin"
log_info "  Password: ${GRAFANA_PASSWORD:-admin}"
log_info ""
log_info "To view logs:"
log_info "  docker-compose -f docker-compose.staging.yml logs -f [service-name]"
log_info ""
log_info "To stop:"
log_info "  docker-compose -f docker-compose.staging.yml down"
log_info ""

