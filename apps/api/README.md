# SWE Agent API

FastAPI-based API gateway for the SWE Agent platform with authentication, rate limiting, and comprehensive endpoint coverage.

## Features

- **FastAPI 0.100+** with async/await throughout
- **JWT Authentication** with OAuth 2.0 (GitHub) support
- **API Key Authentication** for programmatic access
- **Role-Based Access Control (RBAC)**
- **Rate Limiting** per user/API key
- **Structured Logging** with correlation IDs
- **OpenAPI 3.1** documentation
- **Type hints** and Pydantic v2 validation
- **Middleware stack** (CORS, logging, rate limiting)

## Quick Start

### 1. Install Dependencies

```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Development Server

```bash
python main.py
# Or using uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Architecture

```
apps/api/
├── main.py              # FastAPI app entry point
├── config.py            # Settings (pydantic-settings)
├── auth/
│   ├── dependencies.py  # Auth dependencies
│   ├── jwt.py           # JWT utilities
│   └── models.py        # Auth models
├── routers/
│   ├── projects.py      # Project CRUD
│   ├── agents.py        # Agent management
│   ├── issues.py        # Issue operations
│   ├── prs.py           # PR operations
│   └── analytics.py     # Metrics endpoints
└── middleware/
    ├── cors.py          # CORS configuration
    ├── rate_limit.py    # Rate limiting
    └── logging.py       # Request logging
```

## API Endpoints

### Authentication

All endpoints except `/health` and `/` require authentication via:

- **Bearer Token**: `Authorization: Bearer <jwt_token>`
- **API Key**: `X-API-Key: <api_key>`

### Core Endpoints

#### Projects (`/api/v1/projects`)

- `POST /` - Create project
- `GET /` - List projects (paginated)
- `GET /{project_id}` - Get project
- `PATCH /{project_id}` - Update project
- `DELETE /{project_id}` - Delete project

#### Agents (`/api/v1/agents`)

- `POST /` - Create agent
- `GET /` - List agents (filtered)
- `GET /{agent_id}` - Get agent
- `PATCH /{agent_id}` - Update agent
- `POST /{agent_id}/start` - Start agent
- `POST /{agent_id}/cancel` - Cancel agent
- `GET /{agent_id}/logs` - Get agent logs
- `DELETE /{agent_id}` - Delete agent

#### Issues (`/api/v1/issues`)

- `POST /` - Create issue
- `GET /` - List issues (filtered)
- `GET /stats` - Get statistics
- `GET /{issue_id}` - Get issue
- `PATCH /{issue_id}` - Update issue
- `POST /{issue_id}/assign` - Assign agent
- `POST /{issue_id}/resolve` - Mark resolved
- `DELETE /{issue_id}` - Delete issue

#### Pull Requests (`/api/v1/prs`)

- `POST /` - Track PR
- `GET /` - List PRs (filtered)
- `GET /stats` - Get statistics
- `GET /{pr_id}` - Get PR
- `PATCH /{pr_id}` - Update PR
- `POST /{pr_id}/review` - Trigger review
- `GET /{pr_id}/review` - Get review
- `POST /{pr_id}/sync` - Sync with GitHub
- `DELETE /{pr_id}` - Stop tracking

#### Analytics (`/api/v1/analytics`)

- `GET /dashboard` - Dashboard metrics
- `GET /projects/{project_id}` - Project metrics
- `GET /agents/{agent_id}` - Agent metrics
- `GET /timeseries/{metric_type}` - Time series data
- `GET /performance` - System performance
- `GET /export` - Export analytics
- `POST /events` - Record custom event

## Authentication Flow

### JWT Token Flow

1. **Obtain Token** (via OAuth or credentials)

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/token \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password"}'
   ```

2. **Use Token** in subsequent requests

   ```bash
   curl http://localhost:8000/api/v1/projects \
     -H "Authorization: Bearer <access_token>"
   ```

3. **Refresh Token** when expired
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "<refresh_token>"}'
   ```

### API Key Flow

1. **Create API Key** (authenticated request)

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/api-keys \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "My API Key", "scopes": ["projects:read", "issues:write"]}'
   ```

2. **Use API Key** in requests
   ```bash
   curl http://localhost:8000/api/v1/projects \
     -H "X-API-Key: swe_abc123xyz..."
   ```

### OAuth 2.0 (GitHub)

1. **Redirect to GitHub**

   ```
   GET /api/v1/auth/github/login
   ```

2. **Handle Callback**

   ```
   GET /api/v1/auth/github/callback?code=...&state=...
   ```

3. **Receive JWT Token**

## Rate Limiting

Default rate limits:

- **60 requests/minute** per user/IP
- **1000 requests/hour** per user/IP

Rate limit headers:

- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Reset timestamp

## Role-Based Access Control

### Roles

- **admin** - Full access to all resources
- **user** - Access to own resources
- **agent** - Programmatic access for agents
- **readonly** - Read-only access

### Using Role Dependencies

```python
from auth import require_admin, require_user, RoleChecker

@router.get("/admin-only")
async def admin_endpoint(current_user = Depends(require_admin)):
    pass

@router.get("/custom-roles")
async def custom_endpoint(
    current_user = Depends(RoleChecker([UserRole.ADMIN, UserRole.USER]))
):
    pass
```

## Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2025-01-08T12:34:56.789Z",
  "level": "INFO",
  "logger": "api",
  "request_id": "abc-123-def-456",
  "method": "GET",
  "path": "/api/v1/projects",
  "status_code": 200,
  "duration_ms": 45.23,
  "client_ip": "192.168.1.1"
}
```

## Error Handling

All errors return structured JSON:

```json
{
  "error": {
    "code": 404,
    "message": "Project not found",
    "type": "http_error",
    "request_id": "abc-123-def-456"
  }
}
```

## Configuration

See `.env.example` for all configuration options.

Key settings:

- **Database**: PostgreSQL with asyncpg driver
- **Cache**: Redis for rate limiting and sessions
- **Logging**: JSON format with structlog
- **Security**: JWT with configurable expiration

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy .
```

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Using Gunicorn + Uvicorn

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## License

MIT
