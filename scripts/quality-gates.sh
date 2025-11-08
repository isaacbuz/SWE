#!/bin/bash

# Quality Gates Script
# This script runs all quality checks and tests before allowing code to be merged
# Exit code 0 = all checks passed, non-zero = at least one check failed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Track overall status
OVERALL_STATUS=0

# Create reports directory
REPORTS_DIR="./quality-reports"
mkdir -p "$REPORTS_DIR"

log_info "Starting quality gates checks..."
echo "========================================"

# 1. Type checking
log_info "Running TypeScript type checking..."
if cd apps/web && npm run typecheck && cd ../..; then
    log_success "TypeScript type checking passed"
else
    log_error "TypeScript type checking failed"
    OVERALL_STATUS=1
fi
echo ""

# 2. Linting - Frontend
log_info "Running frontend linting..."
if cd apps/web && npm run lint && cd ../..; then
    log_success "Frontend linting passed"
else
    log_error "Frontend linting failed"
    OVERALL_STATUS=1
fi
echo ""

# 3. Linting - Backend
log_info "Running backend linting..."
if cd apps/api && python -m flake8 src/ --max-line-length=100 --statistics --output-file="$REPORTS_DIR/flake8-report.txt" && cd ../..; then
    log_success "Backend linting passed"
else
    log_error "Backend linting failed"
    OVERALL_STATUS=1
fi
echo ""

# 4. Unit Tests - Frontend
log_info "Running frontend unit tests..."
if cd apps/web && npm run test:coverage -- --reporter=json --outputFile="$REPORTS_DIR/vitest-report.json" && cd ../..; then
    log_success "Frontend unit tests passed"
else
    log_error "Frontend unit tests failed"
    OVERALL_STATUS=1
fi
echo ""

# 5. Unit Tests - Backend
log_info "Running backend unit tests..."
if cd apps/api && pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=json --cov-report=term --junitxml="$REPORTS_DIR/pytest-unit-report.xml" && cd ../..; then
    log_success "Backend unit tests passed"
else
    log_error "Backend unit tests failed"
    OVERALL_STATUS=1
fi
echo ""

# 6. Integration Tests - Backend
log_info "Running backend integration tests..."
if cd apps/api && pytest tests/integration/ -v --junitxml="$REPORTS_DIR/pytest-integration-report.xml" && cd ../..; then
    log_success "Backend integration tests passed"
else
    log_error "Backend integration tests failed"
    OVERALL_STATUS=1
fi
echo ""

# 7. Coverage Check
log_info "Checking test coverage thresholds..."
FRONTEND_COVERAGE=$(cd apps/web && npm run test:coverage -- --reporter=json 2>&1 | grep -oP '"lines":\s*\K[0-9.]+' || echo "0")
BACKEND_COVERAGE=$(cd apps/api && pytest --cov=src --cov-report=term-missing | grep TOTAL | awk '{print $4}' | sed 's/%//' || echo "0")

if (( $(echo "$FRONTEND_COVERAGE >= 80" | bc -l) )); then
    log_success "Frontend coverage: ${FRONTEND_COVERAGE}% (>= 80%)"
else
    log_error "Frontend coverage: ${FRONTEND_COVERAGE}% (< 80%)"
    OVERALL_STATUS=1
fi

if (( $(echo "$BACKEND_COVERAGE >= 80" | bc -l) )); then
    log_success "Backend coverage: ${BACKEND_COVERAGE}% (>= 80%)"
else
    log_error "Backend coverage: ${BACKEND_COVERAGE}% (< 80%)"
    OVERALL_STATUS=1
fi
echo ""

# 8. Security Scanning - Frontend
log_info "Running frontend security audit..."
if cd apps/web && npm audit --audit-level=moderate --json > "$REPORTS_DIR/npm-audit.json" 2>&1 && cd ../..; then
    log_success "Frontend security audit passed"
else
    log_warning "Frontend has security vulnerabilities (check $REPORTS_DIR/npm-audit.json)"
    # Not failing build for security issues, just warning
fi
echo ""

# 9. Security Scanning - Backend
log_info "Running backend security scan..."
if cd apps/api && pip-audit --format=json --output "$REPORTS_DIR/pip-audit.json" 2>&1 && cd ../..; then
    log_success "Backend security scan passed"
else
    log_warning "Backend has security vulnerabilities (check $REPORTS_DIR/pip-audit.json)"
    # Not failing build for security issues, just warning
fi
echo ""

# 10. Build Check - Frontend
log_info "Checking frontend build..."
if cd apps/web && npm run build && cd ../..; then
    log_success "Frontend build passed"
else
    log_error "Frontend build failed"
    OVERALL_STATUS=1
fi
echo ""

# 11. E2E Tests (Optional - can be slow)
if [ "$RUN_E2E" = "true" ]; then
    log_info "Running E2E tests..."
    if cd apps/web && npm run test:e2e && cd ../..; then
        log_success "E2E tests passed"
    else
        log_error "E2E tests failed"
        OVERALL_STATUS=1
    fi
    echo ""
fi

# 12. Mutation Testing (Optional - very slow)
if [ "$RUN_MUTATION" = "true" ]; then
    log_info "Running mutation testing..."
    if cd apps/web && npx stryker run && cd ../..; then
        log_success "Frontend mutation testing passed"
    else
        log_warning "Frontend mutation score below threshold"
    fi

    if cd apps/api && mutmut run && cd ../..; then
        log_success "Backend mutation testing passed"
    else
        log_warning "Backend mutation score below threshold"
    fi
    echo ""
fi

# Generate summary report
log_info "Generating quality report..."
cat > "$REPORTS_DIR/quality-summary.txt" << EOF
Quality Gates Summary
=====================

Timestamp: $(date)

Frontend Coverage: ${FRONTEND_COVERAGE}%
Backend Coverage: ${BACKEND_COVERAGE}%

Status:
- TypeScript Check: $([ $OVERALL_STATUS -eq 0 ] && echo "PASSED" || echo "CHECK LOGS")
- Frontend Linting: $([ $OVERALL_STATUS -eq 0 ] && echo "PASSED" || echo "CHECK LOGS")
- Backend Linting: $([ $OVERALL_STATUS -eq 0 ] && echo "PASSED" || echo "CHECK LOGS")
- Frontend Tests: $([ $OVERALL_STATUS -eq 0 ] && echo "PASSED" || echo "CHECK LOGS")
- Backend Tests: $([ $OVERALL_STATUS -eq 0 ] && echo "PASSED" || echo "CHECK LOGS")
- Coverage Check: $([ $OVERALL_STATUS -eq 0 ] && echo "PASSED" || echo "FAILED")
- Security Audit: CHECK REPORTS
- Build Check: $([ $OVERALL_STATUS -eq 0 ] && echo "PASSED" || echo "CHECK LOGS")

Overall Status: $([ $OVERALL_STATUS -eq 0 ] && echo "✓ PASSED" || echo "✗ FAILED")

Reports Location: $REPORTS_DIR
EOF

cat "$REPORTS_DIR/quality-summary.txt"

# Final result
echo ""
echo "========================================"
if [ $OVERALL_STATUS -eq 0 ]; then
    log_success "All quality gates passed! ✓"
    exit 0
else
    log_error "Quality gates failed! ✗"
    log_info "Check detailed reports in: $REPORTS_DIR"
    exit 1
fi
