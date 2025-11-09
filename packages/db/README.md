# Database Package

This package contains database schemas, migrations, and utilities for the PieHr AI-First Software Engineering Platform.

## Structure

```
packages/db/
├── schema/              # SQL schema files
│   ├── users.sql
│   ├── projects.sql
│   ├── agents.sql
│   ├── issues.sql
│   ├── skills.sql
│   ├── api_keys.sql
│   ├── audit_logs.sql
│   └── evidence.sql
├── migrations/         # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   ├── 001_initial_schema.sql
│   └── versions/
│       ├── 001_initial_schema.py
│       └── 002_add_performance_indexes.py
├── seeds/              # Seed data for development
│   ├── 01_users.sql
│   ├── 02_agents.sql
│   └── 03_projects.sql
├── setup.py            # Database setup script (sync)
├── init_async.py       # Async database initialization
├── backup.py           # Backup and restore utilities
├── redis.py            # Redis client and utilities
└── README.md           # This file
```

## Database Schema

The database uses PostgreSQL 15+ with the following main tables:

- **users**: System users and service accounts
- **projects**: Software projects
- **agents**: AI agents
- **tasks**: Issues and tasks
- **skills**: Claude Skills
- **api_keys**: API key management
- **audit_logs**: Audit trail
- **evidence**: Compliance evidence

All schemas include:
- UUID primary keys
- Foreign key constraints
- Check constraints for data validation
- Indexes for performance
- JSONB fields for flexible metadata
- Timestamps (created_at, updated_at)

## Setup

### Prerequisites

- PostgreSQL 15+
- Python 3.10+
- asyncpg (for async operations)
- psycopg2 (for sync operations)

### Installation

```bash
pip install -r requirements.txt
```

### Initialize Database

#### Using Async Setup (Recommended)

```bash
python -m packages.db.init_async \
  --host localhost \
  --port 5432 \
  --database piehr \
  --user postgres \
  --password your_password
```

#### Using Sync Setup

```bash
python -m packages.db.setup \
  --host localhost \
  --port 5432 \
  --database piehr \
  --user postgres \
  --password your_password
```

### Environment Variables

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=piehr
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
```

## Migrations

### Using Alembic

```bash
# Initialize Alembic (already done)
cd packages/db

# Create a new migration
alembic revision -m "description"

# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Manual SQL Migrations

SQL migration files can be run directly:

```bash
psql -h localhost -U postgres -d piehr -f migrations/001_initial_schema.sql
```

## Backup and Restore

### Create Backup

```bash
python -m packages.db.backup backup
```

### Restore from Backup

```bash
python -m packages.db.backup restore --backup-file backups/piehr_backup_20251108_120000.sql
```

### List Backups

```bash
python -m packages.db.backup list
```

## Redis Configuration

The `redis.py` module provides:

- **RedisClient**: Singleton Redis client with connection pooling
- **CacheManager**: High-level cache abstraction
- **RateLimiter**: Rate limiting implementation
- **SessionManager**: Session management
- **DistributedLock**: Distributed locking
- **PubSubManager**: Publish-subscribe for events

### Usage

```python
from packages.db.redis import get_redis_client, get_cache_manager, get_rate_limiter

# Get Redis client
redis_client = get_redis_client()

# Cache operations
cache = get_cache_manager()
cache.set("key", "value", ttl_seconds=3600)
value = cache.get("key")

# Rate limiting
rate_limiter = get_rate_limiter()
if rate_limiter.is_allowed("user123", max_requests=100, window_seconds=60):
    # Process request
    pass
```

### Redis Configuration

Set environment variables:

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password
export REDIS_SSL=false
```

## Connection Pooling

### Async Connection Pool (asyncpg)

```python
import asyncpg
from packages.db import get_db_pool

# Create connection pool
pool = await asyncpg.create_pool(
    host="localhost",
    port=5432,
    database="piehr",
    user="postgres",
    password="password",
    min_size=5,
    max_size=20,
)

# Use pool
async with pool.acquire() as conn:
    result = await conn.fetch("SELECT * FROM users")
```

### Sync Connection Pool (psycopg2)

```python
from psycopg2 import pool

# Create connection pool
connection_pool = pool.SimpleConnectionPool(
    1, 20,
    host="localhost",
    port=5432,
    database="piehr",
    user="postgres",
    password="password"
)

# Use pool
conn = connection_pool.getconn()
# ... use connection
connection_pool.putconn(conn)
```

## Performance Optimization

### Indexes

The database includes:
- Primary key indexes (automatic)
- Foreign key indexes
- Composite indexes for common query patterns
- Full-text search indexes (where applicable)

### Query Optimization

- Use EXPLAIN ANALYZE to analyze query plans
- Monitor slow queries
- Use connection pooling
- Implement caching with Redis

## Security

### Best Practices

1. **Use parameterized queries** to prevent SQL injection
2. **Limit database user permissions** to minimum required
3. **Encrypt sensitive data** at rest and in transit
4. **Regular backups** with encryption
5. **Audit logging** for sensitive operations

### Database User Permissions

```sql
-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'password';
GRANT CONNECT ON DATABASE piehr TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Create application user
CREATE USER app_user WITH PASSWORD 'password';
GRANT CONNECT ON DATABASE piehr TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

## Monitoring

### Health Checks

```python
from packages.db.redis import get_redis_client

# Redis health check
redis_client = get_redis_client()
is_healthy = redis_client.health_check()

# Database health check
import asyncpg
conn = await asyncpg.connect("postgresql://...")
await conn.fetchval("SELECT 1")
```

### Metrics

Monitor:
- Connection pool usage
- Query execution time
- Cache hit rates
- Rate limit violations
- Database size and growth

## Troubleshooting

### Common Issues

1. **Connection refused**: Check PostgreSQL is running and accessible
2. **Authentication failed**: Verify credentials
3. **Database does not exist**: Run initialization script
4. **Migration errors**: Check migration order and dependencies
5. **Connection pool exhausted**: Increase pool size or check for connection leaks

### Debug Commands

```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Connect to database
psql -h localhost -U postgres -d piehr

# List tables
\dt

# Describe table
\d users

# Check indexes
\di

# View active connections
SELECT * FROM pg_stat_activity;
```

## Development

### Seed Data

Load seed data for development:

```bash
python -m packages.db.init_async --skip-seeds=false
```

### Reset Database

```bash
# Drop and recreate
dropdb -h localhost -U postgres piehr
createdb -h localhost -U postgres piehr
python -m packages.db.init_async
```

## Production

### Backup Strategy

1. **Daily backups** at 2 AM
2. **Weekly full backups** with 30-day retention
3. **Point-in-time recovery** enabled
4. **Test restore** monthly

### Monitoring

- Set up alerts for:
  - Database connection failures
  - Slow queries (>1s)
  - High error rates
  - Disk space usage
  - Connection pool exhaustion

## Documentation

- [Schema Documentation](SCHEMA.md)
- [Quick Start Guide](QUICK_START.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
