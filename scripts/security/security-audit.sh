#!/bin/bash
#
# Security Audit Script
#
# Performs comprehensive security audit of the codebase and infrastructure
#

set -euo pipefail

# Configuration
AUDIT_DIR="${AUDIT_DIR:-./security-audit-results}"
SCAN_DEPENDENCIES="${SCAN_DEPENDENCIES:-true}"
SCAN_SECRETS="${SCAN_SECRETS:-true}"
SCAN_CONTAINERS="${SCAN_CONTAINERS:-true}"
SCAN_CODE="${SCAN_CODE:-true}"

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
    log_info "Checking security scanning tools..."
    
    local tools=("npm" "pip" "docker")
    local missing=()
    
    for tool in "${tools[@]}"; do
        if ! command -v "${tool}" &> /dev/null; then
            missing+=("${tool}")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_warn "Missing tools: ${missing[*]}"
        log_info "Some security scans may be skipped"
    else
        log_info "All required tools available"
    fi
}

scan_dependencies() {
    if [[ "${SCAN_DEPENDENCIES}" != "true" ]]; then
        return 0
    fi
    
    log_info "Scanning dependencies for vulnerabilities..."
    mkdir -p "${AUDIT_DIR}"
    
    # Node.js dependencies
    if [[ -f "package.json" ]]; then
        log_info "Scanning Node.js dependencies..."
        if command -v npm &> /dev/null; then
            npm audit --audit-level=moderate > "${AUDIT_DIR}/npm-audit.txt" 2>&1 || true
        fi
    fi
    
    # Python dependencies
    if [[ -f "requirements.txt" ]] || [[ -f "apps/api/requirements.txt" ]]; then
        log_info "Scanning Python dependencies..."
        if command -v pip &> /dev/null; then
            pip-audit --format=json > "${AUDIT_DIR}/pip-audit.json" 2>&1 || {
                log_warn "pip-audit not installed. Install with: pip install pip-audit"
            }
        fi
    fi
    
    log_info "Dependency scanning complete."
}

scan_secrets() {
    if [[ "${SCAN_SECRETS}" != "true" ]]; then
        return 0
    fi
    
    log_info "Scanning for secrets and credentials..."
    mkdir -p "${AUDIT_DIR}"
    
    # Use truffleHog or similar
    if command -v trufflehog &> /dev/null; then
        log_info "Running TruffleHog scan..."
        trufflehog filesystem . --json > "${AUDIT_DIR}/secrets-scan.json" 2>&1 || true
    elif command -v gitleaks &> /dev/null; then
        log_info "Running Gitleaks scan..."
        gitleaks detect --source . --report-path "${AUDIT_DIR}/gitleaks-report.json" || true
    else
        log_warn "No secret scanning tool found. Install trufflehog or gitleaks"
        # Basic grep for common patterns
        log_info "Running basic secret pattern scan..."
        grep -r -E "(api[_-]?key|secret|password|token|credential)" --include="*.py" --include="*.js" --include="*.ts" --include="*.env*" . > "${AUDIT_DIR}/secret-patterns.txt" 2>&1 || true
    fi
    
    log_info "Secret scanning complete."
}

scan_containers() {
    if [[ "${SCAN_CONTAINERS}" != "true" ]]; then
        return 0
    fi
    
    log_info "Scanning Docker containers for vulnerabilities..."
    mkdir -p "${AUDIT_DIR}"
    
    if command -v trivy &> /dev/null; then
        # Scan Dockerfiles
        find . -name "Dockerfile" -o -name "*.dockerfile" | while read -r dockerfile; do
            log_info "Scanning: ${dockerfile}"
            trivy fs --format json --output "${AUDIT_DIR}/trivy-$(basename ${dockerfile}).json" "${dockerfile}" || true
        done
        
        # Scan images if available
        if command -v docker &> /dev/null; then
            docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(swe|platform)" | while read -r image; do
                log_info "Scanning image: ${image}"
                trivy image --format json --output "${AUDIT_DIR}/trivy-${image//\//-}.json" "${image}" || true
            done
        fi
    else
        log_warn "Trivy not installed. Install with: brew install trivy"
    fi
    
    log_info "Container scanning complete."
}

scan_code() {
    if [[ "${SCAN_CODE}" != "true" ]]; then
        return 0
    fi
    
    log_info "Scanning code for security issues..."
    mkdir -p "${AUDIT_DIR}"
    
    # Python code scanning
    if command -v bandit &> /dev/null; then
        log_info "Running Bandit scan (Python)..."
        bandit -r apps/api packages -f json -o "${AUDIT_DIR}/bandit-report.json" || true
    else
        log_warn "Bandit not installed. Install with: pip install bandit"
    fi
    
    # TypeScript/JavaScript scanning
    if command -v npm &> /dev/null && [[ -f "package.json" ]]; then
        log_info "Running ESLint security scan..."
        if npm list eslint-plugin-security &> /dev/null; then
            npm run lint -- --format json > "${AUDIT_DIR}/eslint-security.json" 2>&1 || true
        fi
    fi
    
    log_info "Code scanning complete."
}

generate_report() {
    log_info "Generating security audit report..."
    
    local report_file="${AUDIT_DIR}/security-audit-report.md"
    
    cat > "${report_file}" <<EOF
# Security Audit Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Environment**: ${ENVIRONMENT:-production}

## Summary

This report contains the results of automated security scanning.

## Scans Performed

- Dependency Vulnerability Scanning: ${SCAN_DEPENDENCIES}
- Secret Scanning: ${SCAN_SECRETS}
- Container Scanning: ${SCAN_CONTAINERS}
- Code Security Scanning: ${SCAN_CODE}

## Results

### Dependency Vulnerabilities

See: \`npm-audit.txt\`, \`pip-audit.json\`

### Secrets Found

See: \`secrets-scan.json\`, \`gitleaks-report.json\`, \`secret-patterns.txt\`

### Container Vulnerabilities

See: \`trivy-*.json\`

### Code Security Issues

See: \`bandit-report.json\`, \`eslint-security.json\`

## Recommendations

1. Review all identified vulnerabilities
2. Update dependencies with known vulnerabilities
3. Remove or rotate any exposed secrets
4. Patch container vulnerabilities
5. Fix code security issues
6. Re-run scans after fixes

## Next Steps

1. Review findings
2. Prioritize critical issues
3. Create tickets for fixes
4. Schedule follow-up audit
EOF
    
    log_info "Security audit report generated: ${report_file}"
}

main() {
    log_info "Starting security audit..."
    log_info "Output directory: ${AUDIT_DIR}"
    
    check_dependencies
    mkdir -p "${AUDIT_DIR}"
    
    scan_dependencies
    scan_secrets
    scan_containers
    scan_code
    
    generate_report
    
    log_info "Security audit complete!"
    log_info "Results available in: ${AUDIT_DIR}"
}

main "$@"

