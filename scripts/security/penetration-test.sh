#!/bin/bash
#
# Penetration Testing Script
#
# Performs basic penetration testing of the application
#

set -euo pipefail

# Configuration
TARGET_URL="${TARGET_URL:-http://localhost:8000}"
TEST_DIR="${TEST_DIR:-./penetration-test-results}"
TOOLS_DIR="${TOOLS_DIR:-./tools/security}"

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

check_tools() {
    log_info "Checking penetration testing tools..."
    
    local tools=("curl" "nmap" "nikto")
    local available=()
    local missing=()
    
    for tool in "${tools[@]}"; do
        if command -v "${tool}" &> /dev/null; then
            available+=("${tool}")
        else
            missing+=("${tool}")
        fi
    done
    
    log_info "Available tools: ${available[*]}"
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_warn "Missing tools: ${missing[*]}"
    fi
}

test_authentication() {
    log_info "Testing authentication..."
    mkdir -p "${TEST_DIR}"
    
    # Test login endpoint
    local login_response=$(curl -s -w "\n%{http_code}" -X POST "${TARGET_URL}/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"test"}' || echo "000")
    
    local http_code=$(echo "${login_response}" | tail -1)
    
    if [[ "${http_code}" == "401" ]] || [[ "${http_code}" == "422" ]]; then
        log_info "Authentication endpoint properly rejects invalid credentials"
    else
        log_warn "Unexpected authentication response: ${http_code}"
    fi
    
    echo "Authentication test: HTTP ${http_code}" >> "${TEST_DIR}/auth-tests.txt"
}

test_sql_injection() {
    log_info "Testing for SQL injection vulnerabilities..."
    mkdir -p "${TEST_DIR}"
    
    # Common SQL injection payloads
    local payloads=(
        "' OR '1'='1"
        "'; DROP TABLE users; --"
        "1' UNION SELECT NULL--"
        "admin'--"
    )
    
    for payload in "${payloads[@]}"; do
        local response=$(curl -s -w "\n%{http_code}" "${TARGET_URL}/api/v1/projects?search=${payload}" || echo "000")
        local http_code=$(echo "${response}" | tail -1)
        
        if [[ "${http_code}" == "400" ]] || [[ "${http_code}" == "422" ]]; then
            log_info "SQL injection attempt properly rejected: ${payload}"
        else
            log_warn "Potential SQL injection vulnerability: ${payload} returned ${http_code}"
        fi
        
        echo "SQL injection test (${payload}): HTTP ${http_code}" >> "${TEST_DIR}/sql-injection-tests.txt"
    done
}

test_xss() {
    log_info "Testing for XSS vulnerabilities..."
    mkdir -p "${TEST_DIR}"
    
    # Common XSS payloads
    local payloads=(
        "<script>alert('XSS')</script>"
        "<img src=x onerror=alert('XSS')>"
        "javascript:alert('XSS')"
    )
    
    for payload in "${payloads[@]}"; do
        local response=$(curl -s -w "\n%{http_code}" "${TARGET_URL}/api/v1/projects?name=${payload}" || echo "000")
        local http_code=$(echo "${response}" | tail -1)
        
        # Check if payload is reflected in response
        if echo "${response}" | grep -q "${payload}"; then
            log_warn "Potential XSS vulnerability: payload reflected in response"
        else
            log_info "XSS payload properly sanitized: ${payload}"
        fi
        
        echo "XSS test (${payload}): HTTP ${http_code}" >> "${TEST_DIR}/xss-tests.txt"
    done
}

test_csrf() {
    log_info "Testing CSRF protection..."
    mkdir -p "${TEST_DIR}"
    
    # Test if endpoints require CSRF token
    local response=$(curl -s -w "\n%{http_code}" -X POST "${TARGET_URL}/api/v1/projects" \
        -H "Content-Type: application/json" \
        -d '{"name":"test"}' || echo "000")
    
    local http_code=$(echo "${response}" | tail -1)
    
    if [[ "${http_code}" == "403" ]] || [[ "${http_code}" == "401" ]]; then
        log_info "CSRF protection appears to be enabled"
    else
        log_warn "CSRF protection may be missing (HTTP ${http_code})"
    fi
    
    echo "CSRF test: HTTP ${http_code}" >> "${TEST_DIR}/csrf-tests.txt"
}

test_rate_limiting() {
    log_info "Testing rate limiting..."
    mkdir -p "${TEST_DIR}"
    
    local success_count=0
    local rate_limited_count=0
    
    # Send rapid requests
    for i in {1..100}; do
        local response=$(curl -s -w "\n%{http_code}" "${TARGET_URL}/health" || echo "000")
        local http_code=$(echo "${response}" | tail -1)
        
        if [[ "${http_code}" == "200" ]]; then
            ((success_count++))
        elif [[ "${http_code}" == "429" ]]; then
            ((rate_limited_count++))
        fi
    done
    
    if [[ ${rate_limited_count} -gt 0 ]]; then
        log_info "Rate limiting is active (${rate_limited_count} requests rate limited)"
    else
        log_warn "Rate limiting may not be configured properly"
    fi
    
    echo "Rate limiting test: ${success_count} success, ${rate_limited_count} rate limited" >> "${TEST_DIR}/rate-limiting-tests.txt"
}

test_headers() {
    log_info "Testing security headers..."
    mkdir -p "${TEST_DIR}"
    
    local response=$(curl -s -I "${TARGET_URL}/health" || echo "")
    
    local headers=(
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
        "Strict-Transport-Security"
        "Content-Security-Policy"
    )
    
    for header in "${headers[@]}"; do
        if echo "${response}" | grep -qi "${header}"; then
            log_info "Security header present: ${header}"
        else
            log_warn "Security header missing: ${header}"
        fi
    done
    
    echo "${response}" > "${TEST_DIR}/security-headers.txt"
}

scan_ports() {
    if ! command -v nmap &> /dev/null; then
        log_warn "nmap not available. Skipping port scan."
        return 0
    fi
    
    log_info "Scanning open ports..."
    mkdir -p "${TEST_DIR}"
    
    local host=$(echo "${TARGET_URL}" | sed -E 's|https?://([^/:]+).*|\1|')
    
    nmap -p 80,443,8000,3000,5432,6379 "${host}" > "${TEST_DIR}/nmap-scan.txt" 2>&1 || true
    
    log_info "Port scan complete."
}

generate_report() {
    log_info "Generating penetration test report..."
    
    local report_file="${TEST_DIR}/penetration-test-report.md"
    
    cat > "${report_file}" <<EOF
# Penetration Test Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Target**: ${TARGET_URL}

## Summary

This report contains the results of automated penetration testing.

## Tests Performed

- Authentication Testing
- SQL Injection Testing
- XSS Testing
- CSRF Testing
- Rate Limiting Testing
- Security Headers Testing
- Port Scanning

## Results

See individual test files in this directory for detailed results.

## Findings

### Critical Issues
- Review test results for critical vulnerabilities

### High Priority Issues
- Review test results for high-priority vulnerabilities

### Medium Priority Issues
- Review test results for medium-priority vulnerabilities

### Low Priority Issues
- Review test results for low-priority vulnerabilities

## Recommendations

1. Address all critical and high-priority findings
2. Review and fix medium-priority issues
3. Consider low-priority improvements
4. Schedule follow-up testing

## Next Steps

1. Review all findings
2. Prioritize fixes
3. Create tickets for vulnerabilities
4. Schedule retest after fixes
EOF
    
    log_info "Penetration test report generated: ${report_file}"
}

main() {
    log_info "Starting penetration testing..."
    log_info "Target: ${TARGET_URL}"
    log_info "Output directory: ${TEST_DIR}"
    
    check_tools
    mkdir -p "${TEST_DIR}"
    
    test_authentication
    test_sql_injection
    test_xss
    test_csrf
    test_rate_limiting
    test_headers
    scan_ports
    
    generate_report
    
    log_info "Penetration testing complete!"
    log_info "Results available in: ${TEST_DIR}"
}

main "$@"

