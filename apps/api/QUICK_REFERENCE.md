# FastAPI Gateway - Quick Reference Guide

## Files Overview (37 files created)

### Core Application Files

- `main.py` - FastAPI application entry point
- `config.py` - Pydantic settings configuration
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore rules
- `run.sh` - Quick start script

### Documentation (6 files)

- `README.md` - Main documentation and quick start
- `API_SUMMARY.md` - Complete API endpoint reference
- `AUTH_FLOW.md` - Authentication flows and implementation
- `DEPLOYMENT.md` - Production deployment guide
- `ARCHITECTURE.md` - System architecture diagrams
- `IMPLEMENTATION_SUMMARY.md` - Implementation details

### Authentication Module (4 files)

- `auth/__init__.py` - Module exports
- `auth/models.py` - Pydantic models (User, Token, APIKey)
- `auth/jwt.py` - JWT/password/API key handlers
- `auth/dependencies.py` - FastAPI dependencies (RBAC)

### API Routers (6 files)

- `routers/__init__.py` - Router exports
- `routers/projects.py` - Project CRUD endpoints
- `routers/agents.py` - Agent management endpoints
- `routers/issues.py` - Issue tracking endpoints
- `routers/prs.py` - Pull request endpoints
- `routers/analytics.py` - Metrics endpoints

### Middleware (4 files)

- `middleware/__init__.py` - Middleware exports
- `middleware/cors.py` - CORS configuration
- `middleware/rate_limit.py` - Rate limiting
- `middleware/logging.py` - Structured logging

### WebSocket Support (7 files)

- `websocket/__init__.py` - WebSocket exports
- `websocket/server.py` - WebSocket server setup
- `websocket/auth.py` - WebSocket authentication
- `websocket/events.py` - Event handlers
- `websocket/models.py` - Message models
- `websocket/rooms.py` - Room management
- `websocket/README.md` - WebSocket documentation

### Event Broadcasting (3 files)

- `events/__init__.py` - Event system exports
- `events/broadcaster.py` - Redis event broadcasting
- `events/example_usage.py` - Usage examples

## Quick Commands

### Setup and Run

```bash
# Quick start
cd apps/api
./run.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py

# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Configuration

```bash
# Copy example
cp .env.example .env

# Generate secrets
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For SECRET_KEY

# Edit configuration
nano .env
```

### Access Points

- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health Check: http://localhost:8000/health
- API Root: http://localhost:8000/

## Common API Calls

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'

# Create API key
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Key", "scopes": ["projects:read"]}'
```

### Projects

```bash
# List projects
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "repository_url": "https://github.com/user/repo",
    "branch": "main"
  }'

# Get project
curl http://localhost:8000/api/v1/projects/{project_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Agents

```bash
# Create agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_UUID",
    "agent_type": "issue_resolver",
    "config": {"model": "gpt-4"},
    "auto_start": true
  }'

# List agents
curl http://localhost:8000/api/v1/agents?project_id=PROJECT_UUID \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get agent logs
curl http://localhost:8000/api/v1/agents/{agent_id}/logs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issues

```bash
# Create issue
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_UUID",
    "title": "Bug in authentication",
    "description": "Details...",
    "priority": "high"
  }'

# List issues
curl "http://localhost:8000/api/v1/issues?status=open&priority=high" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get statistics
curl http://localhost:8000/api/v1/issues/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Pull Requests

```bash
# Track PR
curl -X POST http://localhost:8000/api/v1/prs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_UUID",
    "github_pr_url": "https://github.com/user/repo/pull/123",
    "auto_review": true
  }'

# Trigger review
curl -X POST http://localhost:8000/api/v1/prs/{pr_id}/review \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get review
curl http://localhost:8000/api/v1/prs/{pr_id}/review \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Analytics

```bash
# Dashboard metrics
curl http://localhost:8000/api/v1/analytics/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"

# Project metrics
curl http://localhost:8000/api/v1/analytics/projects/{project_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# Time series
curl "http://localhost:8000/api/v1/analytics/timeseries/issues_resolved?time_range=week" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Code Examples

### Using in Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    json={"email": "user@example.com", "password": "password"}
)
tokens = response.json()
access_token = tokens["access_token"]

# Make authenticated request
headers = {"Authorization": f"Bearer {access_token}"}
projects = requests.get(
    "http://localhost:8000/api/v1/projects",
    headers=headers
).json()

print(f"Found {projects['total']} projects")
for project in projects['items']:
    print(f"- {project['name']}")
```

### Using in JavaScript

```javascript
// Login
const loginResponse = await fetch("http://localhost:8000/api/v1/auth/token", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password",
  }),
});
const tokens = await loginResponse.json();

// Make authenticated request
const projectsResponse = await fetch("http://localhost:8000/api/v1/projects", {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
const projects = await projectsResponse.json();

console.log(`Found ${projects.total} projects`);
projects.items.forEach((p) => console.log(`- ${p.name}`));
```

### WebSocket Connection

```javascript
// Connect to agent updates
const ws = new WebSocket(
  `ws://localhost:8000/ws/agents/${agentId}?token=${accessToken}`,
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Agent update:", data);
};

ws.onopen = () => console.log("Connected to agent updates");
ws.onerror = (error) => console.error("WebSocket error:", error);
```

## Environment Variables Reference

### Required

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/swe_agent
REDIS_URL=redis://host:6379/0
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
SECRET_KEY=<generate-with-openssl-rand-hex-32>
```

### Optional

```bash
ENVIRONMENT=development|production
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
CORS_ORIGINS=["http://localhost:3000"]
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### OAuth (GitHub)

```bash
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback
```

## Rate Limits

| Endpoint Type     | Rate Limit |
| ----------------- | ---------- |
| Authentication    | 5/min      |
| Create operations | 10/min     |
| Read operations   | 30/min     |
| Delete operations | 5/min      |
| Analytics export  | 5/min      |
| Custom events     | 60/min     |

## User Roles

| Role       | Description   | Permissions      |
| ---------- | ------------- | ---------------- |
| `admin`    | Administrator | All operations   |
| `user`     | Regular user  | Own resources    |
| `agent`    | Programmatic  | Agent operations |
| `readonly` | View-only     | Read operations  |

## API Key Scopes

- `projects:read` - View projects
- `projects:write` - Create/update projects
- `projects:delete` - Delete projects
- `agents:read` - View agents
- `agents:write` - Create/control agents
- `issues:read` - View issues
- `issues:write` - Create/update issues
- `prs:read` - View PRs
- `prs:write` - Create/update PRs
- `analytics:read` - View analytics

## Response Codes

| Code | Meaning           | When                     |
| ---- | ----------------- | ------------------------ |
| 200  | OK                | Successful request       |
| 201  | Created           | Resource created         |
| 204  | No Content        | Successful deletion      |
| 400  | Bad Request       | Invalid input            |
| 401  | Unauthorized      | Missing/invalid auth     |
| 403  | Forbidden         | Insufficient permissions |
| 404  | Not Found         | Resource not found       |
| 422  | Validation Error  | Invalid data format      |
| 429  | Too Many Requests | Rate limit exceeded      |
| 500  | Server Error      | Internal error           |
| 501  | Not Implemented   | Feature not ready        |

## Error Response Format

```json
{
  "error": {
    "code": 404,
    "message": "Resource not found",
    "type": "http_error",
    "request_id": "abc-123-def-456"
  }
}
```

## Pagination

All list endpoints support:

```bash
?page=1&page_size=20
```

Response format:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

## Filtering

### Projects

```bash
?enabled=true
```

### Agents

```bash
?project_id=UUID&agent_type=issue_resolver&status=running
```

### Issues

```bash
?project_id=UUID&status=open&priority=high&labels=bug,security
```

### PRs

```bash
?project_id=UUID&status=pending
```

## Testing

### Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### Validate OpenAPI Spec

```bash
curl http://localhost:8000/openapi.json | jq .
```

## Troubleshooting

### Port already in use

```bash
# Find process on port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Dependencies issues

```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Check logs

```bash
# View application logs
tail -f logs/app.log

# View systemd logs (if deployed)
journalctl -u swe-api -f
```

## Production Checklist

- [ ] Generate strong JWT_SECRET_KEY
- [ ] Generate strong SECRET_KEY
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=false
- [ ] Configure production DATABASE_URL
- [ ] Configure production REDIS_URL
- [ ] Set production CORS_ORIGINS
- [ ] Configure GitHub OAuth credentials
- [ ] Enable HTTPS/TLS
- [ ] Set up reverse proxy (Nginx/Caddy)
- [ ] Configure rate limiting
- [ ] Set up database backups
- [ ] Configure monitoring/alerting
- [ ] Review security settings
- [ ] Test disaster recovery

## Support Resources

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **README**: See README.md
- **API Reference**: See API_SUMMARY.md
- **Auth Guide**: See AUTH_FLOW.md
- **Architecture**: See ARCHITECTURE.md
- **Deployment**: See DEPLOYMENT.md

## Performance Tips

1. **Database Connection Pool**: Increase for high traffic

   ```bash
   DATABASE_POOL_SIZE=100
   DATABASE_MAX_OVERFLOW=50
   ```

2. **Workers**: Scale based on CPU cores

   ```bash
   WORKERS=17  # (4 cores * 2) + 1
   ```

3. **Redis**: Use for caching and sessions

   ```bash
   REDIS_TTL=3600  # 1 hour cache
   ```

4. **Rate Limiting**: Adjust based on needs
   ```bash
   RATE_LIMIT_PER_MINUTE=100
   RATE_LIMIT_PER_HOUR=5000
   ```

This quick reference should help you get started with the FastAPI Gateway!
