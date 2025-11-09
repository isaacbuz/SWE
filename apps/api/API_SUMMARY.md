# SWE Agent API - Complete Endpoint Summary

## Overview

The SWE Agent API is a FastAPI-based gateway providing comprehensive endpoints for AI-powered software engineering automation. It supports project management, agent orchestration, issue resolution, PR review, and analytics.

## Base URL

```
Production: https://api.swe-agent.com
Development: http://localhost:8000
API Prefix: /api/v1
```

## Authentication

### Methods

1. **JWT Bearer Token**

   ```
   Authorization: Bearer <access_token>
   ```

2. **API Key**
   ```
   X-API-Key: swe_<api_key>
   ```

### Token Endpoints

| Method | Endpoint                  | Description                       |
| ------ | ------------------------- | --------------------------------- |
| POST   | `/auth/token`             | Obtain JWT token with credentials |
| POST   | `/auth/refresh`           | Refresh access token              |
| POST   | `/auth/github/login`      | Initiate GitHub OAuth flow        |
| GET    | `/auth/github/callback`   | GitHub OAuth callback             |
| POST   | `/auth/api-keys`          | Create API key                    |
| GET    | `/auth/api-keys`          | List API keys                     |
| DELETE | `/auth/api-keys/{key_id}` | Revoke API key                    |

## Core Endpoints

### 1. Projects API (`/api/v1/projects`)

Manage GitHub repositories and project configurations.

| Method | Endpoint         | Auth     | Rate Limit | Description                   |
| ------ | ---------------- | -------- | ---------- | ----------------------------- |
| POST   | `/projects`      | Required | 10/min     | Create new project            |
| GET    | `/projects`      | Required | 30/min     | List all projects (paginated) |
| GET    | `/projects/{id}` | Required | 30/min     | Get project by ID             |
| PATCH  | `/projects/{id}` | Required | 10/min     | Update project                |
| DELETE | `/projects/{id}` | Required | 5/min      | Delete project                |

**Request Model (POST/PATCH)**:

```json
{
  "name": "My Project",
  "description": "Project description",
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "enabled": true
}
```

**Response Model**:

```json
{
  "id": "uuid",
  "name": "My Project",
  "description": "Project description",
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "enabled": true,
  "owner_id": "uuid",
  "created_at": "2025-01-08T12:00:00Z",
  "updated_at": "2025-01-08T12:00:00Z"
}
```

### 2. Agents API (`/api/v1/agents`)

Manage AI agent deployments and executions.

| Method | Endpoint              | Auth     | Rate Limit | Description              |
| ------ | --------------------- | -------- | ---------- | ------------------------ |
| POST   | `/agents`             | Required | 10/min     | Create and start agent   |
| GET    | `/agents`             | Required | 30/min     | List agents (filtered)   |
| GET    | `/agents/{id}`        | Required | 30/min     | Get agent by ID          |
| PATCH  | `/agents/{id}`        | Required | 10/min     | Update agent config      |
| POST   | `/agents/{id}/start`  | Required | 10/min     | Start agent execution    |
| POST   | `/agents/{id}/cancel` | Required | 10/min     | Cancel running agent     |
| GET    | `/agents/{id}/logs`   | Required | 30/min     | Get agent execution logs |
| DELETE | `/agents/{id}`        | Required | 5/min      | Delete agent             |

**Agent Types**:

- `issue_resolver` - Resolves GitHub issues
- `pr_reviewer` - Reviews pull requests
- `code_analyzer` - Analyzes code quality
- `custom` - Custom agent configuration

**Agent Status**:

- `pending` - Created but not started
- `running` - Currently executing
- `completed` - Successfully finished
- `failed` - Execution failed
- `cancelled` - Cancelled by user

**Request Model (POST)**:

```json
{
  "project_id": "uuid",
  "agent_type": "issue_resolver",
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_iterations": 10
  },
  "auto_start": true
}
```

**Response Model**:

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "agent_type": "issue_resolver",
  "status": "running",
  "config": {...},
  "result": {...},
  "error": null,
  "created_at": "2025-01-08T12:00:00Z",
  "updated_at": "2025-01-08T12:00:00Z",
  "started_at": "2025-01-08T12:00:01Z",
  "completed_at": null
}
```

### 3. Issues API (`/api/v1/issues`)

Manage issue tracking and resolution.

| Method | Endpoint               | Auth     | Rate Limit | Description            |
| ------ | ---------------------- | -------- | ---------- | ---------------------- |
| POST   | `/issues`              | Required | 10/min     | Create issue           |
| GET    | `/issues`              | Required | 30/min     | List issues (filtered) |
| GET    | `/issues/stats`        | Required | 30/min     | Get issue statistics   |
| GET    | `/issues/{id}`         | Required | 30/min     | Get issue by ID        |
| PATCH  | `/issues/{id}`         | Required | 10/min     | Update issue           |
| POST   | `/issues/{id}/assign`  | Required | 10/min     | Assign agent to issue  |
| POST   | `/issues/{id}/resolve` | Required | 10/min     | Mark issue as resolved |
| DELETE | `/issues/{id}`         | Required | 5/min      | Delete issue           |

**Priority Levels**:

- `low` - Low priority
- `medium` - Medium priority (default)
- `high` - High priority
- `critical` - Critical priority

**Status**:

- `open` - New issue
- `in_progress` - Being worked on
- `resolved` - Fixed
- `closed` - Closed without fix

**Request Model (POST)**:

```json
{
  "project_id": "uuid",
  "title": "Bug in authentication",
  "description": "Detailed description...",
  "github_issue_url": "https://github.com/user/repo/issues/123",
  "priority": "high",
  "labels": ["bug", "security"]
}
```

**Response Model**:

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "title": "Bug in authentication",
  "description": "Detailed description...",
  "github_issue_url": "https://github.com/user/repo/issues/123",
  "github_issue_number": 123,
  "priority": "high",
  "status": "open",
  "labels": ["bug", "security"],
  "assigned_agent_id": null,
  "resolution_pr_url": null,
  "created_at": "2025-01-08T12:00:00Z",
  "updated_at": "2025-01-08T12:00:00Z",
  "resolved_at": null
}
```

### 4. Pull Requests API (`/api/v1/prs`)

Track and review pull requests.

| Method | Endpoint           | Auth     | Rate Limit | Description              |
| ------ | ------------------ | -------- | ---------- | ------------------------ |
| POST   | `/prs`             | Required | 10/min     | Track new PR             |
| GET    | `/prs`             | Required | 30/min     | List PRs (filtered)      |
| GET    | `/prs/stats`       | Required | 30/min     | Get PR statistics        |
| GET    | `/prs/{id}`        | Required | 30/min     | Get PR by ID             |
| PATCH  | `/prs/{id}`        | Required | 10/min     | Update PR                |
| POST   | `/prs/{id}/review` | Required | 5/min      | Trigger automated review |
| GET    | `/prs/{id}/review` | Required | 30/min     | Get review results       |
| POST   | `/prs/{id}/sync`   | Required | 10/min     | Sync with GitHub         |
| DELETE | `/prs/{id}`        | Required | 5/min      | Stop tracking PR         |

**Review Levels**:

- `quick` - Fast, high-level review
- `standard` - Standard comprehensive review
- `thorough` - Deep analysis with security checks

**Request Model (POST)**:

```json
{
  "project_id": "uuid",
  "github_pr_url": "https://github.com/user/repo/pull/456",
  "auto_review": true,
  "review_level": "standard"
}
```

**Review Response**:

```json
{
  "summary": "Overall review summary...",
  "approval_status": "approved",
  "comments": [
    {
      "file_path": "src/auth.py",
      "line_number": 42,
      "comment": "Consider using constant-time comparison",
      "severity": "warning"
    }
  ],
  "security_issues": [],
  "performance_issues": [],
  "code_quality_score": 8.5
}
```

### 5. Analytics API (`/api/v1/analytics`)

Retrieve metrics and performance data.

| Method | Endpoint                       | Auth     | Rate Limit | Description                |
| ------ | ------------------------------ | -------- | ---------- | -------------------------- |
| GET    | `/analytics/dashboard`         | Required | 30/min     | Dashboard overview metrics |
| GET    | `/analytics/projects/{id}`     | Required | 30/min     | Project-specific metrics   |
| GET    | `/analytics/agents/{id}`       | Required | 30/min     | Agent performance metrics  |
| GET    | `/analytics/timeseries/{type}` | Required | 30/min     | Time series data           |
| GET    | `/analytics/performance`       | Required | 30/min     | System performance         |
| GET    | `/analytics/export`            | Required | 5/min      | Export analytics data      |
| POST   | `/analytics/events`            | Required | 60/min     | Record custom event        |

**Metric Types**:

- `issues_resolved` - Issues resolved over time
- `prs_reviewed` - PRs reviewed over time
- `agent_executions` - Agent runs over time
- `code_quality_score` - Code quality trends
- `response_time` - API response times

**Time Ranges**:

- `day` - Last 24 hours
- `week` - Last 7 days
- `month` - Last 30 days
- `quarter` - Last 90 days
- `year` - Last 365 days

**Dashboard Response**:

```json
{
  "total_projects": 10,
  "total_issues": 150,
  "resolved_issues": 120,
  "total_prs": 75,
  "reviewed_prs": 60,
  "active_agents": 5,
  "recent_activity": [...]
}
```

## Query Parameters

### Pagination

All list endpoints support pagination:

```
?page=1&page_size=20
```

- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

### Filtering

Endpoints support various filters:

**Projects**:

```
?enabled=true
```

**Agents**:

```
?project_id=uuid&agent_type=issue_resolver&status=running
```

**Issues**:

```
?project_id=uuid&status=open&priority=high&labels=bug,security
```

**PRs**:

```
?project_id=uuid&status=pending
```

## Response Format

### Success Response

```json
{
  "data": {...},
  "metadata": {
    "request_id": "abc-123-def-456"
  }
}
```

### List Response

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

### Error Response

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

## Rate Limiting

### Default Limits

- **60 requests/minute** per user/IP
- **1000 requests/hour** per user/IP

### Response Headers

```
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1704715200
```

### Rate Limit Exceeded

```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "retry_after": 30
  }
}
```

## WebSocket Endpoints

### Real-time Agent Updates

```
ws://localhost:8000/api/v1/ws/agents/{agent_id}
```

Streams real-time agent execution updates:

```json
{
  "type": "status_update",
  "agent_id": "uuid",
  "status": "running",
  "progress": 45,
  "message": "Analyzing code..."
}
```

### Real-time Logs

```
ws://localhost:8000/api/v1/ws/logs/{agent_id}
```

Streams agent logs in real-time.

## Health & Status

### Health Check

```
GET /health
```

Response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### API Root

```
GET /
```

Response:

```json
{
  "name": "SWE Agent API",
  "version": "1.0.0",
  "environment": "production",
  "docs_url": "/docs",
  "redoc_url": "/redoc"
}
```

## OpenAPI Documentation

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## HTTP Status Codes

| Code | Meaning               |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Created               |
| 204  | No Content            |
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not Found             |
| 422  | Validation Error      |
| 429  | Rate Limit Exceeded   |
| 500  | Internal Server Error |
| 501  | Not Implemented       |

## CORS

Allowed origins configured via `CORS_ORIGINS` environment variable.

Default development origins:

- `http://localhost:3000`
- `http://localhost:3001`

## Security

- **JWT tokens** expire in 30 minutes (configurable)
- **Refresh tokens** expire in 7 days (configurable)
- **API keys** support scopes and expiration
- **HTTPS** required in production
- **Rate limiting** prevents abuse
- **CORS** restrictions enforce origin policies
