#!/bin/bash
#
# Database Optimization Script
#
# Analyzes and optimizes database performance
#

set -euo pipefail

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-swe_db}"
DB_USER="${DB_USER:-swe_user}"
DB_PASSWORD="${DB_PASSWORD:-}"

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

analyze_tables() {
    log_info "Analyzing database tables..."
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" <<EOF
-- Analyze all tables
ANALYZE;

-- Show table statistics
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
EOF
    
    log_info "Table analysis complete."
}

find_slow_queries() {
    log_info "Finding slow queries..."
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" <<EOF
-- Enable pg_stat_statements if not enabled
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    (total_exec_time / 1000 / 60) as total_minutes
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- Queries > 100ms
ORDER BY mean_exec_time DESC
LIMIT 10;
EOF
    
    log_info "Slow query analysis complete."
}

check_indexes() {
    log_info "Checking indexes..."
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" <<EOF
-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
EOF
    
    log_info "Index analysis complete."
}

vacuum_database() {
    log_info "Running VACUUM ANALYZE..."
    
    export PGPASSWORD="${DB_PASSWORD}"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" <<EOF
VACUUM ANALYZE;
EOF
    
    log_info "VACUUM ANALYZE complete."
}

main() {
    log_info "Starting database optimization..."
    log_info "Database: ${DB_NAME}"
    log_info "Host: ${DB_HOST}:${DB_PORT}"
    
    analyze_tables
    find_slow_queries
    check_indexes
    
    read -p "Run VACUUM ANALYZE? (yes/no): " confirm
    if [[ "${confirm}" == "yes" ]]; then
        vacuum_database
    fi
    
    log_info "Database optimization complete!"
}

main "$@"

