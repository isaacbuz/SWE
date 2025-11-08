# Database Package (`packages/db`)

This package contains all database schemas, migrations, seed data, and Redis utilities for the AI-First Software Engineering Platform.

## Overview

The database layer provides:

- **PostgreSQL 15+**: Primary relational database with advanced features (JSONB, UUIDs, GIN indexes)
- **Redis 7+**: Caching, session management, rate limiting, and pub/sub
- **Evidence-Driven Architecture**: Every decision backed by traceable evidence with credibility scores
- **Immutable Audit Trail**: Complete event history for compliance and forensics
- **Agent Execution Tracking**: Full visibility into AI agent operations and costs

## Directory Structure

```
packages/db/
├── schema/                          # SQL schema definitions
│   ├── users.sql                   # User accounts and authentication
│   ├── projects.sql                # Software projects
│   ├── agents.sql                  # AI agent registry
│   ├── issues.sql                  # Tasks, issues, PRs
│   ├── evidence.sql                # Evidence registry with credibility
│   └── audit_logs.sql              # Immutable event trail
├── migrations/                      # Migration files
│   └── 001_initial_schema.sql      # Initial schema setup
├── seeds/                           # Seed data for development
│   ├── 01_users.sql                # Sample users
│   ├── 02_agents.sql               # Core agent definitions
│   └── 03_projects.sql             # Sample projects
├── redis.py                         # Redis utilities and abstractions
└── README.md                        # This file
```

## Database Schema

### Core Tables

#### `users`
User accounts including humans and service accounts.

**Key Fields:**
- `user_id`: UUID primary identifier
- `username`, `email`: Unique identifiers
- `role`: admin, manager, user, service
- `github_*`: OAuth/SSO integration
- `metadata`, `preferences`: JSONB for extensibility

**Indexes:** username, email, github_username, is_active, created_at

#### `projects`
Software projects managed by the platform.

**Key Fields:**
- `project_id`: UUID primary identifier
- `slug`: URL-friendly identifier
- `repository_url`: GitHub/GitLab repository link
- `owner_id`: FK to users
- `technology_stack`: JSONB array of technologies
- `pr_merge_rate`, `test_coverage_percent`: Performance metrics

**Indexes:** project_id, slug, owner_id, repository_url, status

#### `agents`
AI agent registry with capabilities and performance tracking.

**Key Fields:**
- `agent_id`: UUID primary identifier
- `name`, `agent_type`: Unique agent identification
- `model_provider`, `model_name`: LLM configuration
- `capabilities`: JSONB defining agent capabilities
- `success_rate`, `avg_execution_time_ms`: Performance metrics
- `is_active`, `is_experimental`: Deployment status

**Indexes:** agent_id, name, type, is_active, model_provider, tags

#### `tasks`
Issues, pull requests, and tasks.

**Key Fields:**
- `task_id`: UUID primary identifier
- `project_id`: FK to projects
- `github_issue_number`, `github_pr_number`: GitHub integration
- `type`: bug, feature, refactor, test, documentation, task, chore
- `status`: open, in_progress, in_review, blocked, closed, draft
- `priority`: critical, high, medium, low
- `assigned_to_user_id`, `assigned_to_agent_id`: Flexible assignment
- `ai_analysis`, `ai_suggestions`: JSONB for AI processing results

**Indexes:** task_id, project_id, status, priority, type, assigned_to_user, assigned_to_agent, github_issue, github_pr

#### `evidence`
Evidence registry for decision traceability and credibility scoring.

**Key Fields:**
- `evidence_id`: UUID primary identifier
- `task_id`, `project_id`: FKs for relationship
- `source_type`: Code analysis, test result, AI output, etc.
- `credibility_score`: 0.0-1.0 indicating reliability
- `is_verified`: Attestation status
- `related_evidence`, `contradicting_evidence`: JSONB for relationships

**Indexes:** evidence_id, task_id, project_id, source_type, credibility_score, is_verified, tags

#### `agent_executions`
Complete audit trail for every agent execution.

**Key Fields:**
- `execution_id`: UUID primary identifier
- `agent_id`: FK to agents
- `task_id`, `project_id`: FKs for context
- `input_tokens`, `output_tokens`, `cost_usd`: Billing metrics
- `status`: pending, running, success, failure, timeout
- `result`: JSONB containing execution output
- `evidence_id`: Link to supporting evidence

**Indexes:** execution_id, agent_id, task_id, project_id, status, created_at

#### `audit_logs`
Immutable event log for compliance and forensics.

**Key Fields:**
- `log_id`: UUID primary identifier
- `user_id`, `agent_id`: Actor information
- `event_type`: Specific event (task_created, code_pushed, etc.)
- `resource_type`, `resource_id`: What was affected
- `old_values`, `new_values`: JSONB for change tracking
- `ip_address`, `user_agent`: Request context
- `is_immutable`: Constraint ensuring no updates

**Indexes:** log_id, user_id, agent_id, event_type, resource_type, resource_id, created_at

#### `task_comments`
Comments on tasks/PRs with AI metadata.

**Key Fields:**
- `comment_id`: UUID primary identifier
- `task_id`: FK to tasks
- `author_id`, `agent_id`: Flexible authorship
- `github_comment_id`: GitHub integration
- `is_ai_generated`: Flag for AI-authored comments
- `ai_metadata`: JSONB for generation context

**Indexes:** comment_id, task_id, author_id, created_at

#### `task_attachments`
Files and evidence links for tasks.

**Key Fields:**
- `attachment_id`: UUID primary identifier
- `task_id`: FK to tasks
- `storage_path`: Object storage reference
- `is_evidence`: Link to evidence table
- `evidence_id`: FK to evidence

**Indexes:** attachment_id, task_id, is_evidence

#### `activity_feed`
High-level activity summaries for UI.

**Key Fields:**
- `activity_id`: UUID primary identifier
- `project_id`, `task_id`: Context
- `user_id`, `agent_id`: Actor
- `activity_type`: Category of activity
- `is_public`: Visibility control

**Indexes:** activity_id, project_id, task_id, user_id, created_at, is_public

## Setup Instructions

### Prerequisites

- PostgreSQL 15+ running and accessible
- Redis 7+ running and accessible
- Python 3.10+
- `psql` CLI tool

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/ai_company_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_company_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_SSL=false
```

### 2. Create Database

```bash
# Create the database
createdb -U postgres ai_company_db

# Or using psql
psql -U postgres -c "CREATE DATABASE ai_company_db;"
```

### 3. Run Migrations

```bash
# Using psql to execute the migration file
psql -U postgres -d ai_company_db -f packages/db/migrations/001_initial_schema.sql

# Or run individual schema files
psql -U postgres -d ai_company_db -f packages/db/schema/users.sql
psql -U postgres -d ai_company_db -f packages/db/schema/projects.sql
psql -U postgres -d ai_company_db -f packages/db/schema/agents.sql
psql -U postgres -d ai_company_db -f packages/db/schema/issues.sql
psql -U postgres -d ai_company_db -f packages/db/schema/evidence.sql
psql -U postgres -d ai_company_db -f packages/db/schema/audit_logs.sql
```

### 4. Load Seed Data

```bash
# Load seed data (optional, for development)
psql -U postgres -d ai_company_db -f packages/db/seeds/01_users.sql
psql -U postgres -d ai_company_db -f packages/db/seeds/02_agents.sql
psql -U postgres -d ai_company_db -f packages/db/seeds/03_projects.sql
```

### 5. Verify Setup

```bash
# Check tables
psql -U postgres -d ai_company_db -c "\dt"

# Check if seed data loaded
psql -U postgres -d ai_company_db -c "SELECT COUNT(*) FROM users;"
```

### 6. Python Dependencies

Add to your `requirements.txt` or `pyproject.toml`:

```
psycopg2-binary>=2.9.0
redis>=5.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0  # Optional: for advanced migrations
```

Install:

```bash
pip install -r requirements.txt
```

## Using Redis Utilities

### Cache Management

```python
from packages.db.redis import get_cache_manager, cache_result

# Get cache manager
cache = get_cache_manager()

# Set and get values
cache.set("user:123:profile", {"name": "John"}, ttl_seconds=3600)
profile = cache.get("user:123:profile")

# Use decorator for automatic caching
@cache_result(ttl_seconds=3600)
def expensive_function(user_id):
    # Expensive operation
    return result

# Clear pattern
cache.clear_pattern("user:*")
```

### Rate Limiting

```python
from packages.db.redis import get_rate_limiter

limiter = get_rate_limiter()

# Check if request allowed
user_id = "user:123"
if limiter.is_allowed(user_id, max_requests=100, window_seconds=60):
    # Process request
else:
    # Rate limited - return 429
    pass

# Get remaining requests
remaining = limiter.get_remaining(user_id, max_requests=100)
```

### Session Management

```python
from packages.db.redis import get_session_manager

sessions = get_session_manager()

# Create session
session_id = "sess_abc123"
sessions.create(session_id, {
    "user_id": "user:123",
    "permissions": ["read", "write"]
})

# Get session
session_data = sessions.get(session_id)

# Refresh expiry
sessions.refresh(session_id, ttl_seconds=7200)

# Delete session
sessions.delete(session_id)
```

### Distributed Locking

```python
from packages.db.redis import DistributedLock, get_redis_client

redis_client = get_redis_client()
lock = DistributedLock(redis_client, timeout_seconds=30)

# Acquire lock
if lock.acquire("deploy-production"):
    try:
        # Critical section
        pass
    finally:
        lock.release("deploy-production")
```

## Performance Optimization

### Indexing Strategy

The schema includes optimized indexes for:
- UUID lookups (`*_id` columns)
- Status queries (`status`, `is_active`)
- Date range queries (`created_at`)
- JSONB column searches (GIN indexes on `tags`, `labels`)
- Foreign key relationships

### Query Optimization Tips

1. **Always use UUIDs for JOINs** - More efficient than integer IDs for distributed systems
2. **Use JSONB GIN indexes** - For queries on JSON array/object content
3. **Partition large tables** - Consider monthly partitioning for `audit_logs`
4. **Batch operations** - Use INSERT ... ON CONFLICT for upserts
5. **Connection pooling** - Use pgBouncer or similar for many connections

### Redis Optimization

1. **Key expiration** - Always set TTL on temporary data
2. **Pattern efficiency** - Use well-structured key hierarchies
3. **Memory limits** - Configure `maxmemory-policy eviction-policy`
4. **Persistence** - Use RDB snapshots or AOF for critical data

## Monitoring

### PostgreSQL Monitoring

```bash
# Check index usage
psql -d ai_company_db -c "SELECT * FROM pg_stat_user_indexes ORDER BY idx_scan;"

# Check table sizes
psql -d ai_company_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public';"

# Check slow queries (if log_statement = 'all' configured)
psql -d ai_company_db -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Redis Monitoring

```bash
# Check Redis info
redis-cli INFO

# Monitor commands in real-time
redis-cli MONITOR

# Check memory usage
redis-cli INFO MEMORY

# Check key patterns
redis-cli KEYS "*"
```

## Backup and Recovery

### PostgreSQL Backup

```bash
# Full backup
pg_dump -U postgres ai_company_db > backup.sql

# Compressed backup
pg_dump -U postgres ai_company_db | gzip > backup.sql.gz

# Custom format (faster restore)
pg_dump -U postgres -F c ai_company_db > backup.dump
```

### PostgreSQL Restore

```bash
# From SQL file
psql -U postgres ai_company_db < backup.sql

# From custom format
pg_restore -U postgres -d ai_company_db backup.dump
```

### Redis Backup

```bash
# RDB snapshot (point-in-time)
redis-cli BGSAVE

# AOF rewrite
redis-cli BGREWRITEAOF

# Copy dump files
cp /var/lib/redis/dump.rdb ./redis_backup.rdb
```

## Key Design Decisions

### 1. UUID-Based Primary Keys
- **Why**: Better for distributed systems and replication
- **Trade-off**: Larger index size vs. easier federation
- **Implementation**: `gen_random_uuid()` default

### 2. JSONB for Flexibility
- **Why**: Extensible metadata without schema migrations
- **Examples**: `metadata`, `preferences`, `ai_analysis`, `capabilities`
- **Trade-off**: Less query efficiency vs. schema flexibility

### 3. Immutable Audit Logs
- **Why**: Compliance, forensics, and accountability
- **Implementation**: CHECK constraint on `is_immutable`
- **Consideration**: Consider archival strategy for retention policies

### 4. Evidence-Driven Architecture
- **Why**: Traceable AI decision-making
- **Credibility Scoring**: 0.0-1.0 confidence metric
- **Usage**: Link evidence to tasks, agent executions, and policy decisions

### 5. Separate Agent Executions Table
- **Why**: Detailed audit trail for AI agent operations
- **Tracking**: Tokens, cost, duration, and results
- **Analysis**: Performance monitoring and cost optimization

### 6. Task Comments & Attachments Separation
- **Why**: Efficient querying of comments vs. attachments
- **Flexibility**: Support both human and AI-generated comments
- **Extensibility**: Link attachments to evidence registry

## Future Enhancements

1. **Materialized Views** - Pre-computed statistics for dashboards
2. **Table Partitioning** - Yearly/monthly partitions for audit_logs
3. **Event Sourcing** - Event store pattern for critical entities
4. **Time-Series** - TimescaleDB extension for metrics
5. **Full-Text Search** - PostgreSQL FTS for task descriptions
6. **Replication** - Primary-replica setup for HA
7. **Sharding** - Horizontal scaling strategy for scale

## Troubleshooting

### Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -h localhost -d ai_company_db -c "SELECT 1"

# Test Redis connection
redis-cli ping
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `FATAL: database does not exist` | DB not created | Run `createdb ai_company_db` |
| `could not connect to server` | Service not running | Start PostgreSQL/Redis |
| `UNIQUE violation` | Duplicate key | Check seed data idempotency |
| `permission denied` | User privileges | Grant permissions with `GRANT` |

## Support and Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [Redis Documentation](https://redis.io/documentation)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Project Architecture](../../docs/architecture/)
