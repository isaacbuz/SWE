#!/bin/bash
#
# Load Testing Runner Script
#
# Runs k6 load tests with different scenarios
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_URL="${API_URL:-http://localhost:8000}"
OUTPUT_DIR="${OUTPUT_DIR:-./load-test-results}"

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

check_k6() {
    if ! command -v k6 &> /dev/null; then
        log_error "k6 not found. Please install k6 first."
        echo "Installation: https://k6.io/docs/getting-started/installation/"
        exit 1
    fi
    
    log_info "k6 version: $(k6 version)"
}

run_smoke_test() {
    log_info "Running smoke test..."
    mkdir -p "${OUTPUT_DIR}"
    
    k6 run \
        --env API_URL="${API_URL}" \
        --out json="${OUTPUT_DIR}/smoke-test-$(date +%Y%m%d_%H%M%S).json" \
        "${SCRIPT_DIR}/load-test-smoke.js"
}

run_load_test() {
    log_info "Running load test..."
    mkdir -p "${OUTPUT_DIR}"
    
    k6 run \
        --env API_URL="${API_URL}" \
        --out json="${OUTPUT_DIR}/load-test-$(date +%Y%m%d_%H%M%S).json" \
        "${SCRIPT_DIR}/load-test.js"
}

run_stress_test() {
    log_info "Running stress test..."
    mkdir -p "${OUTPUT_DIR}"
    
    k6 run \
        --env API_URL="${API_URL}" \
        --out json="${OUTPUT_DIR}/stress-test-$(date +%Y%m%d_%H%M%S).json" \
        "${SCRIPT_DIR}/load-test-stress.js"
}

run_all_tests() {
    log_info "Running all load tests..."
    
    run_smoke_test
    sleep 5
    
    run_load_test
    sleep 5
    
    run_stress_test
    
    log_info "All tests completed. Results in: ${OUTPUT_DIR}"
}

main() {
    local test_type="${1:-all}"
    
    log_info "Starting load testing..."
    log_info "API URL: ${API_URL}"
    log_info "Test type: ${test_type}"
    
    check_k6
    
    case "${test_type}" in
        smoke)
            run_smoke_test
            ;;
        load)
            run_load_test
            ;;
        stress)
            run_stress_test
            ;;
        all)
            run_all_tests
            ;;
        *)
            echo "Usage: $0 {smoke|load|stress|all}"
            exit 1
            ;;
    esac
    
    log_info "Load testing complete!"
}

main "$@"

