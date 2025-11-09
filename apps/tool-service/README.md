# Tool Service

HTTP service for tool execution that bridges TypeScript packages with the Python FastAPI backend.

## Overview

This Node.js/Express service provides an HTTP API for:
- Listing available tools
- Executing tools
- Querying audit logs
- Health checks

## Quick Start

### 1. Install Dependencies

```bash
cd apps/tool-service
pnpm install
```

### 2. Build

```bash
pnpm build
```

### 3. Run

```bash
# Development
pnpm dev

# Production
pnpm start
```

The service will start on port 3001 by default (configurable via `PORT` environment variable).

## API Endpoints

### Health Check

```
GET /health
```

### List Tools

```
GET /tools?tag=github&search=issue
```

### Get Tool Details

```
GET /tools/:name
```

### Execute Tool

```
POST /tools/execute
Content-Type: application/json

{
  "toolName": "createIssues",
  "arguments": {
    "owner": "example",
    "repo": "repo",
    "tasks": [...]
  },
  "userId": "user-123",
  "options": {}
}
```

### Get Audit Logs

```
GET /tools/audit?userId=user-123&toolName=createIssues&page=1&pageSize=50
```

## Environment Variables

- `PORT` - Server port (default: 3001)
- `TOOL_SERVICE_URL` - Used by Python backend to connect

## Integration with Python Backend

The Python FastAPI backend calls this service via HTTP. Set the `TOOL_SERVICE_URL` environment variable in the Python backend:

```bash
export TOOL_SERVICE_URL=http://localhost:3001
```

## Development

The service uses:
- Express.js for HTTP server
- TypeScript packages from `packages/`
- CORS enabled for cross-origin requests

## Related

- `apps/api/` - Python FastAPI backend
- `packages/openapi-tools/` - Tool registry
- `packages/tool-executor/` - Tool execution engine

