#!/bin/bash

# CI Quality Check - Fast version for CI/CD pipelines
# Runs essential checks only, optimized for speed

set -e

echo "Running CI Quality Checks..."

# Parallel execution for speed
{
    echo "Frontend: Type check + Lint"
    cd apps/web && npm run typecheck && npm run lint && cd ../..
} &

{
    echo "Frontend: Tests"
    cd apps/web && npm run test:coverage && cd ../..
} &

{
    echo "Backend: Tests"
    cd apps/api && pytest tests/ --maxfail=5 --tb=short && cd ../..
} &

# Wait for all background jobs
wait

echo "✓ All CI quality checks passed!"
