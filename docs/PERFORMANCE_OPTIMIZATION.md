# Performance Optimization Guide

This guide covers performance optimization strategies and load testing for the SWE Platform.

## Overview

Performance optimization ensures the platform can handle production workloads efficiently with acceptable response times and resource usage.

## Performance Objectives

### Response Time Targets

| Endpoint | Target (p95) | Target (p99) |
|----------|-------------|--------------|
| Health Check | < 100ms | < 200ms |
| API Endpoints | < 500ms | < 1s |
| Tool Execution | < 2s | < 5s |
| Database Queries | < 100ms | < 500ms |

### Throughput Targets

- **API Requests**: 1000+ requests/second
- **Concurrent Users**: 500+ concurrent users
- **Database Connections**: 100+ concurrent connections

## Load Testing

### k6 Load Testing

**Installation**:
```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### Running Tests

**Smoke Test** (Quick validation):
```bash
./scripts/performance/run-load-tests.sh smoke
```

**Load Test** (Normal load):
```bash
./scripts/performance/run-load-tests.sh load
```

**Stress Test** (Find breaking point):
```bash
./scripts/performance/run-load-tests.sh stress
```

**All Tests**:
```bash
./scripts/performance/run-load-tests.sh all
```

### Test Scenarios

1. **Smoke Test**: 1 VU for 1 minute
2. **Load Test**: Ramp up to 200 users over 21 minutes
3. **Stress Test**: Ramp up to 400 users to find breaking point

## Database Optimization

### Query Optimization

**Indexes**:
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit.audit_log(timestamp DESC);
```

**Query Analysis**:
```sql
-- Enable query logging
SET log_min_duration_statement = 100; -- Log queries > 100ms

-- Analyze slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Connection Pooling

**Python (SQLAlchemy)**:
```python
# Configure connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

**Node.js (pg)**:
```typescript
const pool = new Pool({
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

### Database Tuning

**PostgreSQL Configuration**:
```conf
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

## Caching Strategies

### Redis Caching

**Cache Frequently Accessed Data**:
```python
# Cache user data
@cache(ttl=300)  # 5 minutes
def get_user(user_id: str):
    return db.query(User).filter(User.id == user_id).first()

# Cache API responses
@cache(ttl=60)  # 1 minute
def get_tools():
    return tool_registry.list_tools()
```

**Cache Invalidation**:
```python
# Invalidate cache on update
def update_user(user_id: str, data: dict):
    db.update_user(user_id, data)
    cache.delete(f"user:{user_id}")
```

### Application-Level Caching

**In-Memory Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_config(key: str):
    return db.get_config(key)
```

## API Optimization

### Response Compression

**Nginx**:
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1000;
gzip_types text/plain text/css application/json application/javascript;
```

**FastAPI**:
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Pagination

**Implement Pagination**:
```python
@router.get("/projects")
async def list_projects(
    skip: int = 0,
    limit: int = 100,
):
    return db.query(Project).offset(skip).limit(limit).all()
```

### Database Query Optimization

**Use Eager Loading**:
```python
# Bad: N+1 queries
projects = db.query(Project).all()
for project in projects:
    print(project.user.email)  # Query for each project

# Good: Eager loading
projects = db.query(Project).options(joinedload(Project.user)).all()
for project in projects:
    print(project.user.email)  # No additional queries
```

## Frontend Optimization

### Code Splitting

**Next.js**:
```typescript
// Dynamic imports
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Loading />,
  ssr: false,
});
```

### Image Optimization

**Next.js Image Component**:
```typescript
import Image from 'next/image';

<Image
  src="/image.jpg"
  width={800}
  height={600}
  quality={85}
  priority={false}
  loading="lazy"
/>
```

### Bundle Optimization

**Analyze Bundle Size**:
```bash
npm run build
npm run analyze
```

## Monitoring Performance

### Metrics to Monitor

- **Response Time**: p50, p95, p99
- **Throughput**: Requests per second
- **Error Rate**: Percentage of failed requests
- **Resource Usage**: CPU, memory, disk I/O
- **Database Performance**: Query time, connection pool usage

### Prometheus Metrics

**Custom Metrics**:
```python
from prometheus_client import Histogram

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method']
)
```

### Grafana Dashboards

- **API Performance**: Response times, throughput
- **Database Performance**: Query times, connection pool
- **System Resources**: CPU, memory, disk

## Performance Testing Results

### Baseline Metrics

Run load tests and document:
- Maximum throughput
- Response times at different load levels
- Resource usage patterns
- Breaking points

### Optimization Checklist

- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Caching implemented
- [ ] Response compression enabled
- [ ] Pagination implemented
- [ ] Query optimization completed
- [ ] Frontend bundle optimized
- [ ] CDN configured
- [ ] Load testing completed
- [ ] Performance monitoring set up

## Best Practices

1. **Profile First**: Use profiling tools to identify bottlenecks
2. **Optimize Queries**: Add indexes and optimize slow queries
3. **Cache Aggressively**: Cache frequently accessed data
4. **Monitor Continuously**: Set up performance monitoring
5. **Test Regularly**: Run load tests before deployments
6. **Scale Horizontally**: Use multiple instances for high load
7. **Use CDN**: Serve static assets from CDN
8. **Optimize Database**: Tune PostgreSQL configuration

## Troubleshooting

### High Response Times

1. Check database query performance
2. Review slow query logs
3. Check cache hit rates
4. Monitor resource usage
5. Review application logs

### High Error Rates

1. Check application logs for errors
2. Review database connection pool
3. Check resource limits
4. Review rate limiting configuration

### Memory Leaks

1. Monitor memory usage over time
2. Use memory profiling tools
3. Review object lifecycle
4. Check for unclosed connections

## Related Documentation

- [Load Testing Scripts](../scripts/performance/)
- [Database Backups](./DATABASE_BACKUPS.md)
- [CDN Setup](./CDN_SETUP.md)
- [Observability](./OBSERVABILITY.md)

## Support

For performance issues:
1. Check this documentation
2. Review load test results
3. Check monitoring dashboards
4. Review application logs
5. Contact platform team

