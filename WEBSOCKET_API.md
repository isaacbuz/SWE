# WebSocket API Documentation

## Overview

The WebSocket API provides real-time, bidirectional communication between the SWE Agent backend and web/mobile clients. It uses Socket.IO protocol for reliable message delivery, automatic reconnection, and fallback support.

## Connection

### Endpoint

```
ws://localhost:8000/ws
```

### Authentication

WebSocket connections require JWT authentication. Include the token when establishing the connection:

#### Method 1: Auth Header (Recommended)

```javascript
const socket = io("http://localhost:8000/ws", {
  auth: {
    token: "your-jwt-token"
  }
});
```

#### Method 2: Query Parameters (Fallback)

```javascript
const socket = io("http://localhost:8000/ws?token=your-jwt-token");
```

### Connection Lifecycle

1. **Client establishes connection** with JWT token
2. **Server validates token** and authenticates
3. **Connection established event** sent to client
4. **Auto-subscription** to user's personal room and global room
5. **Client can subscribe** to additional rooms

## Connection Events

### `connection_established`

Emitted when connection is successfully established.

**Payload:**
```json
{
  "type": "connection.established",
  "timestamp": "2024-11-08T10:30:00Z",
  "data": {
    "connection_id": "abc123xyz",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "protocol_version": "1.0"
  }
}
```

### `connection_error`

Emitted when connection fails.

**Payload:**
```json
{
  "type": "connection.error",
  "timestamp": "2024-11-08T10:30:00Z",
  "data": {
    "error_code": "AUTH_FAILED",
    "error_message": "Invalid or expired token",
    "connection_id": null
  }
}
```

## Client Commands

### Subscribe to Room

Subscribe to receive updates from a specific room.

**Request:**
```javascript
socket.emit("subscribe", {
  room: "project:550e8400-e29b-41d4-a716-446655440000"
}, (response) => {
  console.log(response); // {status: "success", room: "project:..."}
});
```

**Supported Rooms:**
- `project:<project_id>` - Project-specific updates
- `user:<user_id>` - User-specific updates (auto-subscribed)
- `agent:<agent_id>` - Agent-specific updates
- `global` - Global updates (auto-subscribed)

**Response:**
```json
{
  "status": "success",
  "room": "project:550e8400-e29b-41d4-a716-446655440000"
}
```

### Unsubscribe from Room

Unsubscribe from a room to stop receiving updates.

**Request:**
```javascript
socket.emit("unsubscribe", {
  room: "project:550e8400-e29b-41d4-a716-446655440000"
}, (response) => {
  console.log(response); // {status: "success", room: "project:..."}
});
```

**Response:**
```json
{
  "status": "success",
  "room": "project:550e8400-e29b-41d4-a716-446655440000"
}
```

### Ping/Heartbeat

Send a ping to keep connection alive and check latency.

**Request:**
```javascript
socket.emit("ping", {}, (response) => {
  console.log(response); // {status: "pong"}
});
```

**Response:**
```json
{
  "status": "pong"
}
```

## Server Events

### Project Events

#### `project.updated`

Emitted when a project is updated.

**Payload:**
```json
{
  "type": "project.updated",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "project_service",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "project_name": "AI Agent Framework",
    "repository_url": "https://github.com/user/ai-agent-framework",
    "status": "active",
    "updated_by": "660e8400-e29b-41d4-a716-446655440001",
    "changes": {
      "status": "updated",
      "fields": ["status", "description"]
    }
  }
}
```

**Room:** `project:<project_id>`, `user:<updated_by>`

#### `project.deleted`

Emitted when a project is deleted.

**Payload:**
```json
{
  "type": "project.deleted",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "project_service",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_by": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

**Room:** `project:<project_id>`, `user:<deleted_by>`

### Agent Events

#### `agent.status_changed`

Emitted when an agent's status changes.

**Payload:**
```json
{
  "type": "agent.status_changed",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "agent_service",
  "data": {
    "agent_id": "770e8400-e29b-41d4-a716-446655440002",
    "agent_name": "GPT-4 Code Analyst",
    "status": "online",
    "availability": 85,
    "metadata": {
      "version": "1.0",
      "last_update": "2024-11-08T10:25:00Z",
      "cpu_usage": 45.2,
      "memory_usage": 62.1
    }
  }
}
```

**Status Values:** `online`, `offline`, `busy`, `idle`, `error`

**Room:** `agent:<agent_id>`, `global`

#### `agent.connected`

Emitted when an agent connects to the system.

#### `agent.disconnected`

Emitted when an agent disconnects from the system.

### Workflow Events

#### `workflow.progress`

Emitted as a workflow executes, providing real-time progress updates.

**Payload:**
```json
{
  "type": "workflow.progress",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "workflow_service",
  "data": {
    "workflow_id": "880e8400-e29b-41d4-a716-446655440003",
    "status": "running",
    "progress": 45,
    "current_step": "Analyzing code structure",
    "total_steps": 10,
    "estimated_time_remaining": 120,
    "logs": [
      "Starting workflow execution",
      "Cloning repository",
      "Analyzing code structure"
    ],
    "errors": []
  }
}
```

**Status Values:** `pending`, `running`, `completed`, `failed`, `cancelled`

**Room:** `project:<project_id>` (if available) or `global`

#### `workflow.started`

Emitted when a workflow starts.

#### `workflow.completed`

Emitted when a workflow completes successfully.

#### `workflow.failed`

Emitted when a workflow fails.

### Pull Request Events

#### `pr.created`

Emitted when a new pull request is created.

**Payload:**
```json
{
  "type": "pr.created",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "github_service",
  "data": {
    "pr_id": "990e8400-e29b-41d4-a716-446655440004",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Fix: Improve error handling in API routes",
    "description": "This PR improves error handling across API routes...",
    "author": "john-doe",
    "branch": "feature/improve-error-handling",
    "github_url": "https://github.com/user/project/pull/42",
    "status": "open",
    "created_at": "2024-11-08T10:30:00Z"
  }
}
```

**Room:** `project:<project_id>`

#### `pr.updated`

Emitted when a pull request is updated.

**Payload:**
```json
{
  "type": "pr.updated",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "github_service",
  "data": {
    "pr_id": "990e8400-e29b-41d4-a716-446655440004",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Fix: Improve error handling in API routes",
    "status": "merged"
  }
}
```

**Room:** `project:<project_id>`

#### `pr.closed`

Emitted when a pull request is closed.

### Issue Events

#### `issue.updated`

Emitted when an issue is updated.

**Payload:**
```json
{
  "type": "issue.updated",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "github_service",
  "data": {
    "issue_id": "aa0e8400-e29b-41d4-a716-446655440005",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Support for async/await syntax",
    "description": "Add support for async/await syntax in code analysis",
    "status": "in_progress",
    "priority": "high",
    "assigned_to": "660e8400-e29b-41d4-a716-446655440001",
    "updated_at": "2024-11-08T10:30:00Z"
  }
}
```

**Status Values:** `open`, `in_progress`, `closed`, `blocked`

**Priority Values:** `low`, `medium`, `high`, `critical`

**Room:** `project:<project_id>`, `user:<assigned_to>`

#### `issue.created`

Emitted when a new issue is created.

#### `issue.closed`

Emitted when an issue is closed.

### AI Events

#### `ai.suggestion`

Emitted when an AI suggestion or recommendation is generated.

**Payload:**
```json
{
  "type": "ai.suggestion",
  "timestamp": "2024-11-08T10:30:00Z",
  "source": "ai_dock_service",
  "data": {
    "suggestion_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "target_type": "pr",
    "target_id": "990e8400-e29b-41d4-a716-446655440004",
    "category": "optimization",
    "title": "Reduce complexity in error handling",
    "description": "This function has a cyclomatic complexity of 12. Consider breaking it into smaller functions.",
    "severity": "warning",
    "confidence": 0.92,
    "suggested_action": "Refactor function into smaller utilities",
    "metadata": {
      "function_name": "handle_request",
      "line_number": 125,
      "complexity_score": 12,
      "recommended_complexity": 8
    }
  }
}
```

**Target Types:** `issue`, `pr`, `code`

**Categories:** `optimization`, `refactor`, `bug_fix`, `security`, `performance`, `maintainability`

**Severity Values:** `info`, `warning`, `critical`

**Room:** `project:<project_id>` (if available) or `global`

#### `ai.analysis_complete`

Emitted when AI analysis completes.

## Room Management

### Room Types

| Room Type | Format | Auto-Subscribe | Purpose |
|-----------|--------|----------------|---------|
| User | `user:<user_id>` | Yes | User-specific updates |
| Project | `project:<project_id>` | No | Project-specific updates |
| Agent | `agent:<agent_id>` | No | Agent-specific updates |
| Global | `global` | Yes | System-wide updates |

### Room Access Control

- Users can only subscribe to rooms they have access to
- User rooms are private and only accessible by the user
- Project rooms require project access permissions
- Agent rooms are read-only for users

## Client Implementation Examples

### JavaScript/Node.js

```javascript
import io from "socket.io-client";

// Connect with authentication
const socket = io("http://localhost:8000/ws", {
  auth: {
    token: localStorage.getItem("jwt_token")
  },
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5
});

// Handle connection established
socket.on("connection_established", (event) => {
  console.log("Connected:", event.data.connection_id);
});

// Listen for project updates
socket.on("project.updated", (event) => {
  console.log("Project updated:", event.data);
  // Update UI
});

// Listen for workflow progress
socket.on("workflow.progress", (event) => {
  console.log("Progress:", event.data.progress + "%");
  // Update progress bar
});

// Subscribe to project room
socket.emit("subscribe", {
  room: "project:550e8400-e29b-41d4-a716-446655440000"
}, (response) => {
  if (response.status === "success") {
    console.log("Subscribed to project");
  }
});

// Handle errors
socket.on("connect_error", (error) => {
  console.error("Connection error:", error);
});

socket.on("disconnect", (reason) => {
  console.log("Disconnected:", reason);
});
```

### React Hook

```typescript
import { useEffect, useRef, useCallback } from "react";
import io, { Socket } from "socket.io-client";

export const useWebSocket = (token: string) => {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    socketRef.current = io("http://localhost:8000/ws", {
      auth: { token }
    });

    socketRef.current.on("connect", () => setConnected(true));
    socketRef.current.on("disconnect", () => setConnected(false));

    return () => {
      socketRef.current?.disconnect();
    };
  }, [token]);

  const subscribe = useCallback((room: string) => {
    return new Promise((resolve) => {
      socketRef.current?.emit("subscribe", { room }, resolve);
    });
  }, []);

  const unsubscribe = useCallback((room: string) => {
    return new Promise((resolve) => {
      socketRef.current?.emit("unsubscribe", { room }, resolve);
    });
  }, []);

  const on = useCallback((event: string, handler: (...args: any[]) => void) => {
    socketRef.current?.on(event, handler);
  }, []);

  const off = useCallback((event: string) => {
    socketRef.current?.off(event);
  }, []);

  return { connected, subscribe, unsubscribe, on, off };
};
```

### Python (Backend Integration)

```python
from events.broadcaster import get_broadcaster
from uuid import UUID

async def send_project_update():
    broadcaster = get_broadcaster()

    await broadcaster.broadcast_project_updated(
        project_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        project_name="AI Agent Framework",
        repository_url="https://github.com/user/ai-agent-framework",
        status="active",
        updated_by=UUID("660e8400-e29b-41d4-a716-446655440001"),
        changes={"status": "updated"}
    )
```

## Error Handling

### Connection Errors

| Error Code | Message | Action |
|------------|---------|--------|
| `AUTH_FAILED` | Invalid or expired token | Refresh token and reconnect |
| `AUTH_MISSING` | No authentication provided | Provide valid JWT token |
| `ROOM_ACCESS_DENIED` | Access denied to room | Check permissions |
| `INVALID_ROOM` | Invalid room format | Use valid room name |

### Recovery Strategy

1. **Automatic Reconnection**: Socket.IO handles reconnection automatically
2. **Token Refresh**: Refresh JWT before expiration
3. **Manual Reconnection**: Call `socket.connect()` if needed
4. **Fallback Protocol**: Falls back to HTTP long-polling if WebSocket unavailable

## Performance Considerations

### Connection Limits

- **Default:** 10,000 concurrent connections per instance
- **With Redis adapter:** Unlimited (scales horizontally)

### Message Size

- **Maximum payload:** 1MB per message
- **Recommended:** Keep payloads under 100KB

### Rate Limiting

- **No built-in WebSocket rate limiting** (implement in client/server as needed)
- **Use application-level validation** for sensitive operations

## Monitoring and Debugging

### Enable Debug Logging

```javascript
// Browser
localStorage.debug = "socket.io-client:*";

// Node.js
process.env.DEBUG = "socket.io-client:*";
```

### Check Connection Status

```javascript
socket.on("connect", () => console.log("Connected"));
socket.on("disconnect", (reason) => console.log("Disconnected:", reason));
socket.on("connect_error", (error) => console.log("Error:", error));
```

### Monitor Room Membership

Access WebSocket statistics via HTTP endpoint (when implemented):

```bash
GET /api/v1/websocket/stats
```

Response:
```json
{
  "connections": 156,
  "rooms": {
    "global": 156,
    "user:550e8400-e29b-41d4-a716-446655440000": 1,
    "project:660e8400-e29b-41d4-a716-446655440001": 23
  }
}
```

## Security Best Practices

1. **Always use HTTPS/WSS in production**
2. **Validate JWT tokens** on every connection
3. **Implement rate limiting** for sensitive rooms
4. **Use Redis adapter** for horizontal scaling
5. **Sanitize all event data** before sending to clients
6. **Implement room access control** based on permissions
7. **Log all WebSocket connections** for security audit
8. **Implement token refresh** before expiration
9. **Use secure random tokens** for authentication
10. **Monitor for unusual patterns** (e.g., rapid reconnects)

## Deployment

### Docker Compose Example

```yaml
version: "3.8"

services:
  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    environment:
      REDIS_URL: redis://redis:6379
      CORS_ORIGINS: "http://localhost:3000"
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Production Checklist

- [ ] Use WSS (WebSocket Secure) protocol
- [ ] Configure Redis for message queue
- [ ] Set up monitoring and alerting
- [ ] Configure CORS for production domain
- [ ] Implement rate limiting
- [ ] Set up SSL/TLS certificates
- [ ] Configure connection timeouts
- [ ] Implement graceful shutdown
- [ ] Set up logging and metrics
- [ ] Test failover scenarios

## Troubleshooting

### Connection Refused

**Problem:** WebSocket connection is refused

**Solutions:**
1. Check API server is running
2. Verify WebSocket endpoint is mounted
3. Check CORS configuration
4. Verify JWT token is valid

### Disconnection Loops

**Problem:** Client keeps disconnecting and reconnecting

**Solutions:**
1. Check token expiration time
2. Verify server-side logging
3. Check network connectivity
4. Increase ping timeout

### Events Not Received

**Problem:** Events are not being received by client

**Solutions:**
1. Verify subscription to correct room
2. Check server-side event emission
3. Verify event type names
4. Check browser console for errors
5. Verify CORS headers

## Migration Guide

### From REST Polling to WebSocket

Before (REST polling):
```javascript
setInterval(async () => {
  const response = await fetch("/api/v1/projects/123");
  setProject(response.json());
}, 5000);
```

After (WebSocket):
```javascript
socket.emit("subscribe", { room: "project:123" });

socket.on("project.updated", (event) => {
  setProject(event.data);
});
```

Benefits:
- Real-time updates (no polling interval)
- Lower bandwidth usage
- Lower server load
- Better user experience

## Support and Issues

For issues or questions:
1. Check this documentation
2. Review example code in `/apps/api/events/example_usage.py`
3. Check WebSocket server logs
4. Review Socket.IO documentation: https://socket.io/docs/

## API Versioning

- **Current Version:** 1.0
- **Namespace:** `/ws`
- **Protocol:** Socket.IO 4.x

## Changelog

### Version 1.0 (2024-11-08)

- Initial WebSocket API implementation
- Support for project, agent, workflow, PR, issue, and AI events
- JWT authentication
- Room-based subscriptions
- Redis adapter for scaling
- Event broadcaster utilities
