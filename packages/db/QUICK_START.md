# Database Quick Start Guide

Fast setup guide for the database infrastructure.

## 1-Minute Setup (Development)

### Prerequisites

- PostgreSQL 15+ installed locally
- Redis 7+ installed locally
- `psql` CLI tool available

### Steps

```bash
# 1. Start PostgreSQL and Redis
# On macOS with Homebrew:
brew services start postgresql@15
brew services start redis

# 2. Create database and load schema
psql -U postgres -c "CREATE DATABASE ai_company_db;"
psql -U postgres -d ai_company_db -f packages/db/migrations/001_initial_schema.sql

# 3. Load seed data (optional)
psql -U postgres -d ai_company_db -f packages/db/seeds/01_users.sql
psql -U postgres -d ai_company_db -f packages/db/seeds/02_agents.sql
psql -U postgres -d ai_company_db -f packages/db/seeds/03_projects.sql

# 4. Verify setup
psql -U postgres -d ai_company_db -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"
```

### Verify Connection

```bash
# Test PostgreSQL
psql -U postgres -d ai_company_db -c "SELECT 1 as postgres_connected;"

# Test Redis
redis-cli ping
# Should return: PONG
```

## Using Python Setup Script

```bash
# From project root
cd packages/db

# Run full setup
python setup.py --host localhost --port 5432 --user postgres

# Or with password
python setup.py --password yourpassword

# Verify only (no modifications)
python setup.py --verify-only

# Skip seed data
python setup.py --skip-seeds
```

## Docker Setup (Development)

### Using Docker Compose

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ai_company_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./packages/db/migrations/001_initial_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./packages/db/seeds/01_users.sql:/docker-entrypoint-initdb.d/02-users.sql
      - ./packages/db/seeds/02_agents.sql:/docker-entrypoint-initdb.d/03-agents.sql
      - ./packages/db/seeds/03_projects.sql:/docker-entrypoint-initdb.d/04-projects.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF

# Start services
docker-compose up -d

# Verify
docker-compose exec postgres psql -U postgres -d ai_company_db -c "SELECT 1;"
docker-compose exec redis redis-cli ping
```

## Environment Variables

Create `.env` in project root:

```bash
# PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_company_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_company_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_SSL=false
```

## Using Database in Python Code

### Initialize Redis Client

```python
from packages.db import (
    RedisClient,
    get_cache_manager,
    get_rate_limiter,
    get_session_manager,
)

# Initialize
redis = RedisClient()

# Health check
if redis.health_check():
    print("Redis is healthy!")
```

### Using Cache

```python
from packages.db import get_cache_manager

cache = get_cache_manager()

# Set value
cache.set("user:123", {"name": "John"}, ttl_seconds=3600)

# Get value
user = cache.get("user:123")

# Cached function
from packages.db import cache_result

@cache_result(ttl_seconds=3600)
def get_expensive_data(user_id):
    # Heavy computation
    return data
```

### Using Rate Limiter

```python
from packages.db import get_rate_limiter

limiter = get_rate_limiter()

# Check limit
if limiter.is_allowed("user:123", max_requests=100, window_seconds=60):
    # Process request
    pass
else:
    # Rate limited
    raise RateLimitExceeded()
```

### Using Sessions

```python
from packages.db import get_session_manager
import uuid

sessions = get_session_manager()

# Create session
session_id = str(uuid.uuid4())
sessions.create(session_id, {
    "user_id": "user:123",
    "permissions": ["read", "write"]
})

# Get session
user_session = sessions.get(session_id)

# Refresh
sessions.refresh(session_id)

# Logout
sessions.delete(session_id)
```

## Common Tasks

### Check Database Status

```bash
# List tables
psql -d ai_company_db -c "\dt"

# List databases
psql -c "\l"

# Check table sizes
psql -d ai_company_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Reset Database (CAUTION)

```bash
# Drop and recreate
psql -U postgres -c "DROP DATABASE IF EXISTS ai_company_db;"
psql -U postgres -c "CREATE DATABASE ai_company_db;"

# Reload schema
psql -U postgres -d ai_company_db -f packages/db/migrations/001_initial_schema.sql
```

### Backup Database

```bash
# SQL backup
pg_dump -U postgres ai_company_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Custom format (faster)
pg_dump -U postgres -F c ai_company_db > backup_$(date +%Y%m%d_%H%M%S).dump
```

### Restore Database

```bash
# From SQL
psql -U postgres -d ai_company_db < backup.sql

# From custom format
pg_restore -U postgres -d ai_company_db backup.dump
```

## Troubleshooting

### PostgreSQL Connection Failed

```bash
# Check if running
# macOS
brew services list | grep postgresql

# Linux
systemctl status postgresql

# Start if needed
brew services start postgresql@15
```

### Redis Connection Failed

```bash
# Check if running
redis-cli ping
# Should return: PONG

# Start if needed
brew services start redis
```

### "Database already exists"

This is fine - the schema will be created within the existing database.

### "Permission denied" for user postgres

Try: `sudo -u postgres psql`

### Seeds Already Loaded Error

Use: `psql -d ai_company_db -f seeds/01_users.sql` with idempotent SQL (uses `ON CONFLICT DO NOTHING`)

## Performance Tips

1. **Connection Pooling**: Use pgBouncer for production
2. **Indexes**: Check indexes with `SELECT * FROM pg_stat_user_indexes;`
3. **Query Analysis**: Use `EXPLAIN ANALYZE` for slow queries
4. **Redis Memory**: Monitor with `redis-cli INFO MEMORY`
5. **Backups**: Schedule regular PostgreSQL backups

## Next Steps

1. Review [README.md](./README.md) for detailed documentation
2. Check [schema/](./schema/) for table definitions
3. Explore [migrations/](./migrations/) for schema evolution
4. Run integration tests with the Python API layer

## Support

For issues, check:

- PostgreSQL logs: `/var/log/postgresql/postgresql.log`
- Redis logs: `redis-cli MONITOR`
- Application logs for connection errors
