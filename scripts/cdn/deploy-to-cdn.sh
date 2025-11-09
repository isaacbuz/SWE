#!/bin/bash
#
# CDN Deployment Script
#
# Deploys frontend assets to CDN (Cloudflare Pages, AWS S3+CloudFront, etc.)
#

set -euo pipefail

# Configuration
CDN_PROVIDER="${CDN_PROVIDER:-cloudflare}"
CDN_URL="${CDN_URL:-}"
OUTPUT_DIR="${OUTPUT_DIR:-apps/web/.next}"
BUILD_DIR="${BUILD_DIR:-apps/web/.next/static}"

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
    
    case "${CDN_PROVIDER}" in
        cloudflare)
            if ! command -v wrangler &> /dev/null; then
                log_error "wrangler CLI not found. Install with: npm install -g wrangler"
                exit 1
            fi
            ;;
        aws)
            if ! command -v aws &> /dev/null; then
                log_error "AWS CLI not found"
                exit 1
            fi
            ;;
        *)
            log_error "Unknown CDN provider: ${CDN_PROVIDER}"
            exit 1
            ;;
    esac
    
    log_info "Dependencies check complete."
}

build_frontend() {
    log_info "Building frontend for CDN..."
    
    cd apps/web
    
    # Set CDN environment variables
    export CDN_URL="${CDN_URL}"
    export NEXT_PUBLIC_CDN_URL="${CDN_URL}"
    
    # Build with CDN config
    if [[ -f "next.config.cdn.js" ]]; then
        NEXT_CONFIG_FILE=next.config.cdn.js npm run build
    else
        npm run build
    fi
    
    cd ../..
    
    log_info "Frontend build complete."
}

deploy_cloudflare() {
    log_info "Deploying to Cloudflare Pages..."
    
    if [[ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
        log_error "CLOUDFLARE_ACCOUNT_ID not set"
        exit 1
    fi
    
    if [[ -z "${CLOUDFLARE_PROJECT_NAME:-}" ]]; then
        log_error "CLOUDFLARE_PROJECT_NAME not set"
        exit 1
    fi
    
    # Deploy using wrangler
    wrangler pages deploy "${OUTPUT_DIR}" \
        --project-name="${CLOUDFLARE_PROJECT_NAME}" \
        --compatibility-date=2025-11-09
    
    log_info "Cloudflare Pages deployment complete."
}

deploy_aws() {
    log_info "Deploying to AWS S3 + CloudFront..."
    
    if [[ -z "${AWS_S3_BUCKET:-}" ]]; then
        log_error "AWS_S3_BUCKET not set"
        exit 1
    fi
    
    if [[ -z "${AWS_CLOUDFRONT_DISTRIBUTION_ID:-}" ]]; then
        log_error "AWS_CLOUDFRONT_DISTRIBUTION_ID not set"
        exit 1
    fi
    
    # Sync static assets to S3
    log_info "Syncing assets to S3: ${AWS_S3_BUCKET}"
    aws s3 sync "${BUILD_DIR}" "s3://${AWS_S3_BUCKET}/_next/static/" \
        --cache-control "public, max-age=31536000, immutable" \
        --delete
    
    # Invalidate CloudFront cache
    log_info "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id "${AWS_CLOUDFRONT_DISTRIBUTION_ID}" \
        --paths "/_next/static/*"
    
    log_info "AWS deployment complete."
}

main() {
    log_info "Starting CDN deployment..."
    log_info "Provider: ${CDN_PROVIDER}"
    log_info "CDN URL: ${CDN_URL}"
    
    check_dependencies
    build_frontend
    
    case "${CDN_PROVIDER}" in
        cloudflare)
            deploy_cloudflare
            ;;
        aws)
            deploy_aws
            ;;
        *)
            log_error "Unsupported CDN provider: ${CDN_PROVIDER}"
            exit 1
            ;;
    esac
    
    log_info "CDN deployment completed successfully!"
}

main "$@"

