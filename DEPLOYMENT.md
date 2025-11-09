# Deployment Guide

## Quick Start

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## Services

### 1. PostgreSQL Database
- **Port**: 5432
- **Database**: swe_db
- **User**: swe_user
- **Password**: Set via `POSTGRES_PASSWORD` environment variable

### 2. Redis Cache
- **Port**: 6379
- Used for caching and rate limiting

### 3. Python FastAPI Backend
- **Port**: 8000
- **Health**: http://localhost:8000/health
- **Docs**: http://localhost:8000/docs

### 4. Node.js Tool Service
- **Port**: 3001
- **Health**: http://localhost:3001/health

### 5. Next.js Frontend
- **Port**: 3000
- **URL**: http://localhost:3000

### 6. Nginx (Production)
- **Port**: 80 (HTTP), 443 (HTTPS)
- Reverse proxy for all services

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `POSTGRES_PASSWORD` - Database password
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT signing key
- `DATABASE_URL` - Full database connection string
- `NEXT_PUBLIC_API_URL` - Frontend API URL

## Building Images

### Development
```bash
docker-compose build
```

### Production
```bash
docker-compose -f docker-compose.prod.yml build
```

## Database Migrations

Run migrations in the API container:

```bash
docker-compose exec api alembic upgrade head
```

## Health Checks

All services include health checks. Check status:

```bash
docker-compose ps
```

## Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f tool-service
docker-compose logs -f web
```

### Resource Usage
```bash
docker stats
```

## Troubleshooting

### Services won't start
1. Check logs: `docker-compose logs`
2. Verify environment variables
3. Check port conflicts
4. Ensure Docker has enough resources

### Database connection issues
1. Verify PostgreSQL is healthy: `docker-compose ps postgres`
2. Check DATABASE_URL format
3. Verify network connectivity

### Tool service not responding
1. Check tool service logs: `docker-compose logs tool-service`
2. Verify TOOL_SERVICE_URL is correct
3. Check if OpenAPI specs are mounted correctly

## Production Checklist

- [ ] Set strong passwords for all services
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Configure rate limiting
- [ ] Set up CDN for static assets
- [ ] Configure firewall rules
- [ ] Set up health check endpoints
- [ ] Configure auto-scaling (if using Kubernetes)

## Kubernetes Deployment

For Kubernetes deployment, see `k8s/` directory (to be created).

## Scaling

### Horizontal Scaling
- API: Scale with `docker-compose scale api=3`
- Tool Service: Scale with `docker-compose scale tool-service=2`
- Frontend: Scale with `docker-compose scale web=2`

### Load Balancing
Nginx automatically load balances between scaled services.

## Backup and Recovery

### Database Backup
```bash
docker-compose exec postgres pg_dump -U swe_user swe_db > backup.sql
```

### Database Restore
```bash
docker-compose exec -T postgres psql -U swe_user swe_db < backup.sql
```

## Security

1. **Change default passwords**
2. **Use secrets management** (Docker secrets, Kubernetes secrets)
3. **Enable SSL/TLS** in production
4. **Configure firewall rules**
5. **Regular security updates**
6. **Monitor for vulnerabilities**

---

For more details, see individual service READMEs in `apps/` directories.

