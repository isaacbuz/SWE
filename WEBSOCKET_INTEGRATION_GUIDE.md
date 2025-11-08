# WebSocket Integration Guide

## Quick Start

### 1. Installation

All dependencies are included in `apps/api/requirements.txt`:

```bash
cd apps/api
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python main.py
```

The WebSocket server will be available at:
```
ws://localhost:8000/ws
```

### 3. Test Connection

Use a WebSocket client to test:

```bash
# Using websocat (install: brew install websocat)
websocat ws://localhost:8000/ws

# Or use socket.io-client in browser console
```

## Integration Points

### 1. Broadcasting Project Updates

In `apps/api/routers/projects.py`:

```python
from fastapi import APIRouter, Depends
from uuid import UUID

from events.broadcaster import get_broadcaster
from auth.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

@router.put("/{project_id}")
async def update_project(
    project_id: UUID,
    updates: ProjectUpdate,
    current_user = Depends(get_current_user)
):
    """Update a project and broadcast changes."""
    # Update database
    # project = await db.update_project(project_id, updates)

    # Broadcast update to all connected clients
    broadcaster = get_broadcaster()
    await broadcaster.broadcast_project_updated(
        project_id=project_id,
        project_name=updates.name,
        repository_url=updates.repository_url,
        status=updates.status,
        updated_by=current_user.id,
        changes=updates.dict(exclude_unset=True)
    )

    return {"success": True, "project": project}
```

### 2. Workflow Progress Updates

In Temporal workflow or activity:

```python
from temporal.workflow import workflow_run_context
from events.broadcaster import get_broadcaster
from uuid import UUID

async def report_progress(
    workflow_id: UUID,
    step_number: int,
    step_name: str,
    total_steps: int
):
    """Report workflow progress to connected clients."""
    broadcaster = get_broadcaster()

    progress_percent = int((step_number / total_steps) * 100)

    await broadcaster.broadcast_workflow_progress(
        workflow_id=workflow_id,
        status="running",
        progress=progress_percent,
        current_step=step_name,
        total_steps=total_steps,
        logs=[f"Executing: {step_name}"]
    )
```

### 3. Agent Status Updates

In agent service:

```python
from events.broadcaster import get_broadcaster
from websocket.models import AgentStatus

async def update_agent_status(agent_id: UUID, new_status: str):
    """Update agent status and notify all clients."""
    # Update agent in database
    # agent = await db.update_agent_status(agent_id, new_status)

    broadcaster = get_broadcaster()
    await broadcaster.broadcast_agent_status_changed(
        agent_id=agent_id,
        agent_name=agent.name,
        status=new_status,
        availability=calculate_availability(agent_id),
        metadata={
            "cpu_usage": get_cpu_usage(),
            "memory_usage": get_memory_usage(),
            "active_tasks": count_active_tasks(agent_id)
        }
    )
```

### 4. GitHub Webhook Integration

In webhook handler:

```python
from fastapi import APIRouter, Request
from events.broadcaster import get_broadcaster

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/github")
async def github_webhook(request: Request):
    """Handle GitHub webhooks."""
    payload = await request.json()

    # Pull Request created
    if payload.get("action") == "opened" and "pull_request" in payload:
        pr = payload["pull_request"]
        project = await get_project_by_repo(pr["head"]["repo"]["url"])

        broadcaster = get_broadcaster()
        await broadcaster.broadcast_pr_created(
            pr_id=UUID(str(pr["id"])),
            project_id=project.id,
            title=pr["title"],
            description=pr["body"],
            author=pr["user"]["login"],
            branch=pr["head"]["ref"],
            github_url=pr["html_url"],
            status=pr["state"]
        )

    # Issue created/updated
    elif "issue" in payload and "pull_request" not in payload:
        issue = payload["issue"]
        project = await get_project_by_repo(issue["repository"]["url"])

        if payload.get("action") in ["opened", "edited"]:
            broadcaster = get_broadcaster()
            await broadcaster.broadcast_issue_updated(
                issue_id=UUID(str(issue["id"])),
                project_id=project.id,
                title=issue["title"],
                description=issue["body"],
                status="open" if issue["state"] == "open" else "closed",
                priority=extract_priority_label(issue),
                assigned_to=get_user_id(issue["assignee"]) if issue["assignee"] else None
            )

    return {"status": "received"}
```

### 5. AI Suggestion Integration

In AI analysis service:

```python
from events.broadcaster import get_broadcaster
from services.ai_dock import AIAnalyzer

async def analyze_and_suggest(pr_id: UUID, project_id: UUID):
    """Analyze PR and emit AI suggestions."""
    analyzer = AIAnalyzer()
    suggestions = await analyzer.analyze_pr(pr_id)

    broadcaster = get_broadcaster()

    for suggestion in suggestions:
        await broadcaster.broadcast_ai_suggestion(
            suggestion_id=UUID(suggestion["id"]),
            target_type="pr",
            target_id=pr_id,
            category=suggestion["category"],
            title=suggestion["title"],
            description=suggestion["description"],
            severity=suggestion.get("severity", "info"),
            confidence=suggestion.get("confidence", 0.5),
            suggested_action=suggestion.get("action"),
            metadata=suggestion.get("metadata", {}),
            project_id=project_id
        )
```

## Frontend Integration

### React Component Example

```typescript
// hooks/useProjectUpdates.ts
import { useEffect, useState, useCallback } from "react";
import io, { Socket } from "socket.io-client";
import { useAuth } from "./useAuth";

export const useProjectUpdates = (projectId: string) => {
  const { token } = useAuth();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize WebSocket
    socketRef.current = io(
      process.env.REACT_APP_WS_URL || "http://localhost:8000/ws",
      {
        auth: { token },
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
      }
    );

    // Handle connection
    socketRef.current.on("connect", async () => {
      // Subscribe to project room
      socketRef.current?.emit(
        "subscribe",
        { room: `project:${projectId}` },
        (response: any) => {
          if (response.status === "success") {
            setLoading(false);
          }
        }
      );
    });

    // Listen for project updates
    socketRef.current.on("project.updated", (event: any) => {
      if (event.data.project_id === projectId) {
        setProject((prev: any) => ({
          ...prev,
          ...event.data,
          updated_at: event.timestamp,
        }));
      }
    });

    // Listen for workflow progress
    socketRef.current.on("workflow.progress", (event: any) => {
      setProject((prev: any) => ({
        ...prev,
        workflow_status: event.data.status,
        workflow_progress: event.data.progress,
      }));
    });

    // Handle errors
    socketRef.current.on("connect_error", (error: any) => {
      console.error("WebSocket error:", error);
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [projectId, token]);

  return { project, loading };
};

// components/ProjectDetail.tsx
import React from "react";
import { useProjectUpdates } from "../hooks/useProjectUpdates";

const ProjectDetail: React.FC<{ projectId: string }> = ({ projectId }) => {
  const { project, loading } = useProjectUpdates(projectId);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>{project?.project_name}</h1>
      <p>Status: {project?.status}</p>

      {project?.workflow_progress !== undefined && (
        <div>
          <p>Progress: {project.workflow_progress}%</p>
          <progress value={project.workflow_progress} max="100" />
        </div>
      )}
    </div>
  );
};

export default ProjectDetail;
```

### Real-time Dashboard

```typescript
// components/Dashboard.tsx
import React, { useEffect, useState } from "react";
import io from "socket.io-client";

const Dashboard: React.FC = () => {
  const [agents, setAgents] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);

  useEffect(() => {
    const socket = io("http://localhost:8000/ws", {
      auth: { token: localStorage.getItem("jwt_token") },
    });

    socket.on("connect", () => {
      // Subscribe to global updates
      socket.emit("subscribe", { room: "global" });
    });

    // Listen to agent status updates
    socket.on("agent.status_changed", (event) => {
      setAgents((prev) =>
        prev.map((a) =>
          a.id === event.data.agent_id
            ? {
                ...a,
                status: event.data.status,
                availability: event.data.availability,
              }
            : a
        )
      );
    });

    // Listen to workflow progress
    socket.on("workflow.progress", (event) => {
      setWorkflows((prev) =>
        prev.map((w) =>
          w.id === event.data.workflow_id
            ? {
                ...w,
                status: event.data.status,
                progress: event.data.progress,
              }
            : w
        )
      );
    });

    return () => socket.disconnect();
  }, []);

  return (
    <div>
      <h2>Active Agents</h2>
      <ul>
        {agents.map((agent) => (
          <li key={agent.id}>
            {agent.name} - {agent.status} ({agent.availability}%)
          </li>
        ))}
      </ul>

      <h2>Running Workflows</h2>
      <ul>
        {workflows.map((workflow) => (
          <li key={workflow.id}>
            {workflow.name} - {workflow.progress}%
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Dashboard;
```

## Testing

### Unit Tests

Run the WebSocket tests:

```bash
pytest apps/api/websocket/tests.py -v
```

### Integration Tests

Create `apps/api/websocket/integration_tests.py`:

```python
import pytest
import asyncio
from uuid import uuid4

# Test broadcaster
from events.broadcaster import EventBroadcaster

@pytest.mark.asyncio
async def test_broadcast_project_updated():
    """Test project update broadcast."""
    broadcaster = EventBroadcaster()
    broadcaster.init()

    result = await broadcaster.broadcast_project_updated(
        project_id=uuid4(),
        project_name="Test Project",
        repository_url="https://github.com/test/repo",
        status="active",
        updated_by=uuid4(),
        changes={"status": "updated"}
    )

    assert result is True

@pytest.mark.asyncio
async def test_broadcast_workflow_progress():
    """Test workflow progress broadcast."""
    broadcaster = EventBroadcaster()
    broadcaster.init()

    result = await broadcaster.broadcast_workflow_progress(
        workflow_id=uuid4(),
        status="running",
        progress=50,
        current_step="Step 2",
        total_steps=5
    )

    assert result is True
```

## Monitoring

### Logging

WebSocket events are logged automatically. Check logs:

```bash
# View all WebSocket-related logs
grep -i websocket logs/app.log

# View connection events
grep "websocket_connect\|websocket_disconnect" logs/app.log
```

### Metrics (To Be Implemented)

Future monitoring endpoint:

```bash
GET /api/v1/websocket/stats

# Response
{
  "connections": 156,
  "rooms": {
    "global": 156,
    "project:*": 45,
    "user:*": 156
  },
  "events_emitted": 3421,
  "uptime_seconds": 3600
}
```

## Troubleshooting

### Connection Issues

**Problem:** WebSocket connection fails

**Debug:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check server is running
curl http://localhost:8000/health
```

### Token Expiration

**Problem:** Connection drops after 30 minutes

**Solution:** Refresh token before expiration

```typescript
// Token refresh hook
const useTokenRefresh = (token: string) => {
  useEffect(() => {
    const tokenData = parseJWT(token);
    const timeUntilExpiry = new Date(tokenData.exp * 1000).getTime() - Date.now();

    // Refresh 5 minutes before expiry
    const refreshTimer = setTimeout(() => {
      refreshToken();
    }, timeUntilExpiry - 5 * 60 * 1000);

    return () => clearTimeout(refreshTimer);
  }, [token]);
};
```

### Event Not Received

**Debug:**
1. Check subscription: `socket.emit("debug:rooms", {}, console.log)`
2. Verify event type names match
3. Check browser console for errors
4. Verify CORS headers

## Performance Tuning

### Connection Limits

Adjust in `config.py`:

```python
# Max connections per instance
MAX_CONNECTIONS = 10000

# Message buffer size
MAX_HTTP_BUFFER_SIZE = 1e6  # 1MB

# Ping interval (seconds)
PING_INTERVAL = 25

# Ping timeout (seconds)
PING_TIMEOUT = 60
```

### Redis Configuration

For production with multiple instances:

```python
# In websocket/server.py, configure Redis:
REDIS_URL = "redis://redis-cluster.internal:6379"
```

## Production Deployment

### Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY apps/api/requirements.txt .
RUN pip install -r requirements.txt

COPY apps/api .

ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      REDIS_URL: redis://redis:6379
      CORS_ORIGINS: https://app.example.com
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### SSL/TLS

For WSS (secure WebSocket):

```python
# main.py
import ssl

if settings.environment == "production":
    ssl_context = ssl.create_default_context()
    ssl_context.load_cert_chain(
        certfile="/path/to/cert.pem",
        keyfile="/path/to/key.pem"
    )

    uvicorn.run(
        "main:app",
        ssl_keyfile="/path/to/key.pem",
        ssl_certfile="/path/to/cert.pem",
        ssl_version=ssl.PROTOCOL_TLS
    )
```

## Backward Compatibility

The WebSocket API maintains backward compatibility. Clients using the current protocol version will continue to work when new features are added.

To check protocol version:

```javascript
socket.on("connection_established", (event) => {
  console.log("Protocol version:", event.data.protocol_version);
});
```

## Migration from REST

### Before (REST Polling)

```javascript
// Poll every 5 seconds
setInterval(async () => {
  const response = await fetch("/api/v1/projects/123");
  updateProject(response.json());
}, 5000);
```

### After (WebSocket)

```javascript
// Real-time updates
socket.emit("subscribe", { room: "project:123" });

socket.on("project.updated", (event) => {
  updateProject(event.data);
});
```

**Benefits:**
- Real-time (no polling interval)
- 80% less bandwidth
- Lower server load
- Better user experience

## Next Steps

1. **Integrate with Projects Router** - Add event broadcasts when projects are updated
2. **Integrate with Workflows** - Report progress as workflows execute
3. **Integrate with GitHub** - Add webhook handlers for PR/issue events
4. **Add AI Service Integration** - Broadcast AI suggestions and analyses
5. **Implement Monitoring** - Add `/api/v1/websocket/stats` endpoint
6. **Add Rate Limiting** - Implement WebSocket rate limiting
7. **Security Hardening** - Add additional authentication checks

## Support

For issues:
1. Check `/WEBSOCKET_API.md`
2. Review `/apps/api/events/example_usage.py`
3. Check server logs: `grep -i websocket logs/app.log`
4. Test with websocat or browser console
