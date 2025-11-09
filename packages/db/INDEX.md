# Database Package Index

Quick navigation guide for the database package documentation and code.

## Quick Links

- **Quick Start**: [QUICK_START.md](./QUICK_START.md) - 1-minute setup
- **Full Setup**: [README.md](./README.md) - Complete documentation
- **Schema Reference**: [SCHEMA.md](./SCHEMA.md) - All tables and fields
- **Implementation**: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Project overview

## Directory Contents

### Schema Definitions (`schema/`)

- **users.sql** - User accounts, authentication, GitHub OAuth
- **projects.sql** - Software projects with repository integration
- **agents.sql** - AI agent registry with capabilities
- **issues.sql** - Tasks, issues, and pull requests
- **evidence.sql** - Evidence registry with credibility scoring
- **audit_logs.sql** - Immutable event trail for compliance

### Migrations (`migrations/`)

- **001_initial_schema.sql** - Complete initial schema (all tables in one file)

### Seed Data (`seeds/`)

- **01_users.sql** - Sample users (5 records)
- **02_agents.sql** - Core agents (10 records)
- **03_projects.sql** - Sample projects (5 records)

### Python Modules

- **redis.py** - Redis utilities (cache, rate limit, sessions, locks)
- **setup.py** - Database initialization script
- ****init**.py** - Package exports

### Configuration

- **requirements.txt** - Python dependencies
- **INDEX.md** - This file

## Getting Started

### For Developers

1. Read [QUICK_START.md](./QUICK_START.md)
2. Set up PostgreSQL and Redis
3. Run `python setup.py`
4. Explore schema in [SCHEMA.md](./SCHEMA.md)

### For DevOps/Infrastructure

1. Review [README.md](./README.md) architecture section
2. Check Docker setup in [QUICK_START.md](./QUICK_START.md)
3. Review performance tips in [README.md](./README.md)
4. Plan backup strategy

### For Data Analysis

1. Review table structures in [SCHEMA.md](./SCHEMA.md)
2. Check indexes for query optimization
3. See seed data in `seeds/` directory

## Key Concepts

### Evidence-Driven Architecture

Every AI decision is traceable to sources with credibility scoring (0.0-1.0).
See `evidence.sql` and [SCHEMA.md](./SCHEMA.md#5-evidence) for details.

### Immutable Audit Logs

Complete event history for compliance.
See `audit_logs.sql` and [README.md](./README.md#audit-logs) for details.

### Redis Utilities

Production-ready caching, rate limiting, and session management.
See `redis.py` and [README.md](./README.md#using-redis-utilities) for usage.

## File Sizes

| File                      | Lines | Purpose            |
| ------------------------- | ----- | ------------------ |
| README.md                 | 450+  | Full documentation |
| QUICK_START.md            | 350+  | Fast setup         |
| SCHEMA.md                 | 600+  | Complete reference |
| IMPLEMENTATION_SUMMARY.md | 400+  | Project overview   |
| 001_initial_schema.sql    | 547   | Complete schema    |
| redis.py                  | 683   | Redis utilities    |
| setup.py                  | 279   | Setup script       |
| Schema files (6)          | 617   | Individual tables  |
| Seed files (3)            | 190   | Test data          |

## Common Tasks

### Setup Database

```bash
python setup.py --host localhost --user postgres
```

### Load Seeds Only

```bash
python setup.py --skip-migrations
```

### Verify Setup

```bash
python setup.py --verify-only
```

### Use Cache in Code

```python
from packages.db import get_cache_manager
cache = get_cache_manager()
cache.set("key", value, ttl_seconds=3600)
```

### Use Rate Limiting

```python
from packages.db import get_rate_limiter
limiter = get_rate_limiter()
if limiter.is_allowed("user_id", max_requests=100):
    # Process request
```

## Documentation Map

```
├── QUICK_START.md
│   ├── 1-minute setup
│   ├── Docker setup
│   ├── Python examples
│   └── Troubleshooting
├── README.md
│   ├── Full setup instructions
│   ├── Table documentation
│   ├── Performance tips
│   ├── Monitoring
│   └── Troubleshooting
├── SCHEMA.md
│   ├── ER diagram
│   ├── Table specs
│   ├── Index strategy
│   └── Performance notes
└── IMPLEMENTATION_SUMMARY.md
    ├── Project overview
    ├── Design decisions
    ├── Scalability
    └── Next steps
```

## Tables Overview

| Table            | Purpose            | Rows | Indexes |
| ---------------- | ------------------ | ---- | ------- |
| users            | User accounts      | 5+   | 6       |
| projects         | Software projects  | 5+   | 7       |
| agents           | AI agent registry  | 10+  | 7       |
| tasks            | Issues/PRs         | 1M+  | 11+     |
| evidence         | Decision sources   | 1M+  | 7       |
| agent_executions | Agent runs         | 10M+ | 6       |
| task_comments    | Task comments      | 5M+  | 4       |
| task_attachments | File storage       | 1M+  | 3       |
| audit_logs       | Event trail        | 10M+ | 9       |
| activity_feed    | Activity summaries | 1M+  | 6       |

## Performance Characteristics

- UUID lookups: O(1)
- Task listings: O(n log n)
- Evidence search: O(log n)
- Audit queries: O(n log n)

See [SCHEMA.md](./SCHEMA.md#performance-characteristics) for details.

## Technology Stack

- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Languages**: SQL, Python 3.10+
- **Drivers**: psycopg2-binary, redis

## Support Resources

- [PostgreSQL Docs](https://www.postgresql.org/docs/15/)
- [Redis Docs](https://redis.io/documentation)
- [Architecture Overview](../../docs/architecture/)

## Version History

- **v0.1.0** - Initial release (November 8, 2025)
  - 10 core tables
  - 67+ indexes
  - Redis utilities
  - Complete documentation

## Next Steps

1. **Development**: See [QUICK_START.md](./QUICK_START.md)
2. **Integration**: See [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md#next-steps)
3. **Production**: See [README.md](./README.md#backup-and-recovery)

---

Last Updated: November 8, 2025
Status: Production Ready ✓
