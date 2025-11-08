# SWE Agent API - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Web Frontend │  │    Mobile    │  │   CLI Tool   │  │  CI/CD Bot  │ │
│  │  (React)     │  │     App      │  │   (Python)   │  │  (GitHub)   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                 │                 │                 │         │
│         └─────────────────┴─────────────────┴─────────────────┘         │
│                                    │                                     │
│                          HTTP/WebSocket                                  │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼─────────────────────────────────────┐
│                       Reverse Proxy (Nginx/Caddy)                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  • SSL/TLS Termination                                          │    │
│  │  • Load Balancing                                               │    │
│  │  • Request Routing                                              │    │
│  │  • Static File Serving                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼─────────────────────────────────────┐
│                            FastAPI Application                           │
│                                                                          │
│  ┌───────────────────────── Middleware Stack ───────────────────────┐   │
│  │                                                                   │   │
│  │  1. Logging Middleware                                           │   │
│  │     ├─ Generate correlation ID                                   │   │
│  │     ├─ Log request details                                       │   │
│  │     ├─ Track duration                                            │   │
│  │     └─ Log response/errors                                       │   │
│  │                                                                   │   │
│  │  2. CORS Middleware                                              │   │
│  │     ├─ Validate origin                                           │   │
│  │     ├─ Add CORS headers                                          │   │
│  │     └─ Handle preflight                                          │   │
│  │                                                                   │   │
│  │  3. Rate Limiting Middleware                                     │   │
│  │     ├─ Identify user/IP/key                                      │   │
│  │     ├─ Check limits (Redis)                                      │   │
│  │     ├─ Add rate limit headers                                    │   │
│  │     └─ Block if exceeded                                         │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌───────────────────── Authentication Layer ──────────────────────┐    │
│  │                                                                  │    │
│  │  JWT Handler              API Key Handler       OAuth Handler   │    │
│  │  ├─ Token validation     ├─ Key validation    ├─ GitHub flow   │    │
│  │  ├─ Token generation     ├─ Key generation    ├─ State mgmt    │    │
│  │  ├─ Token refresh        └─ Key hashing       └─ User linking  │    │
│  │  └─ Token revocation                                            │    │
│  │                                                                  │    │
│  │  Role Checker             Scope Checker                         │    │
│  │  ├─ admin               ├─ projects:read                        │    │
│  │  ├─ user                ├─ projects:write                       │    │
│  │  ├─ agent               ├─ agents:write                         │    │
│  │  └─ readonly            └─ analytics:read                       │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────── API Routers ───────────────────────────┐     │
│  │                                                                 │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │     │
│  │  │  Projects   │  │   Agents    │  │   Issues    │           │     │
│  │  │   Router    │  │   Router    │  │   Router    │           │     │
│  │  ├─────────────┤  ├─────────────┤  ├─────────────┤           │     │
│  │  │ • Create    │  │ • Create    │  │ • Create    │           │     │
│  │  │ • List      │  │ • List      │  │ • List      │           │     │
│  │  │ • Get       │  │ • Get       │  │ • Get       │           │     │
│  │  │ • Update    │  │ • Update    │  │ • Update    │           │     │
│  │  │ • Delete    │  │ • Delete    │  │ • Assign    │           │     │
│  │  │             │  │ • Start     │  │ • Resolve   │           │     │
│  │  │             │  │ • Cancel    │  │ • Stats     │           │     │
│  │  │             │  │ • Logs      │  │             │           │     │
│  │  └─────────────┘  └─────────────┘  └─────────────┘           │     │
│  │                                                                 │     │
│  │  ┌─────────────┐  ┌─────────────┐                             │     │
│  │  │     PRs     │  │  Analytics  │                             │     │
│  │  │   Router    │  │   Router    │                             │     │
│  │  ├─────────────┤  ├─────────────┤                             │     │
│  │  │ • Track     │  │ • Dashboard │                             │     │
│  │  │ • List      │  │ • Projects  │                             │     │
│  │  │ • Get       │  │ • Agents    │                             │     │
│  │  │ • Update    │  │ • Timeseries│                             │     │
│  │  │ • Review    │  │ • Performance                             │     │
│  │  │ • Sync      │  │ • Export    │                             │     │
│  │  │ • Stats     │  │ • Events    │                             │     │
│  │  └─────────────┘  └─────────────┘                             │     │
│  │                                                                 │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                     │
│  ┌──────────────────── WebSocket Server ──────────────────────────┐     │
│  │                                                                  │     │
│  │  Connection Manager         Room Manager                        │     │
│  │  ├─ Client connections     ├─ Agent rooms                       │     │
│  │  ├─ Authentication          ├─ Log rooms                        │     │
│  │  ├─ Heartbeat               └─ Broadcast                        │     │
│  │  └─ Disconnect handling                                         │     │
│  │                                                                  │     │
│  │  Event Handlers                                                 │     │
│  │  ├─ agent.status_update                                         │     │
│  │  ├─ agent.log_entry                                             │     │
│  │  ├─ issue.created                                               │     │
│  │  └─ pr.reviewed                                                 │     │
│  │                                                                  │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└────────────────────────────┬────────────┬──────────────────────────────┘
                             │            │
              ┌──────────────┘            └──────────────┐
              │                                          │
┌─────────────┴──────────────┐            ┌─────────────┴─────────────┐
│      PostgreSQL DB         │            │        Redis Cache        │
│  ┌──────────────────────┐  │            │  ┌────────────────────┐  │
│  │  Tables:             │  │            │  │  Keys:             │  │
│  │  • users             │  │            │  │  • rate_limits     │  │
│  │  • projects          │  │            │  │  • sessions        │  │
│  │  • agents            │  │            │  │  • token_revoke    │  │
│  │  • issues            │  │            │  │  • cache:*         │  │
│  │  • pull_requests     │  │            │  │  • ws:rooms:*      │  │
│  │  • api_keys          │  │            │  └────────────────────┘  │
│  │  • analytics_events  │  │            │                          │
│  │  • agent_logs        │  │            │  Pub/Sub Channels:       │
│  └──────────────────────┘  │            │  • agent_events          │
│                            │            │  • system_events         │
│  Connection Pool:          │            └──────────────────────────┘
│  • Size: 50                │
│  • Overflow: 20            │
│  • Timeout: 30s            │
└────────────────────────────┘
              │
              │
┌─────────────┴──────────────┐
│   External Services        │
│  ┌──────────────────────┐  │
│  │  GitHub API          │  │
│  │  • OAuth             │  │
│  │  • Repository data   │  │
│  │  • Issues/PRs        │  │
│  │  • Webhooks          │  │
│  └──────────────────────┘  │
└────────────────────────────┘
```

## Request Flow

### 1. Authentication Flow (JWT)

```
┌──────┐                                     ┌──────────────┐
│Client│                                     │  FastAPI App │
└──┬───┘                                     └──────┬───────┘
   │                                                │
   │ POST /api/v1/auth/token                       │
   │ {email, password}                             │
   ├──────────────────────────────────────────────>│
   │                                                │
   │                                         ┌──────┴──────┐
   │                                         │ Middleware  │
   │                                         │ • Logging   │
   │                                         │ • CORS      │
   │                                         └──────┬──────┘
   │                                                │
   │                                         ┌──────┴──────────┐
   │                                         │ Auth Router     │
   │                                         │ • Hash password │
   │                                         │ • Query DB      │
   │                                         └──────┬──────────┘
   │                                                │
   │                                         ┌──────┴──────────┐
   │                                         │ JWT Handler     │
   │                                         │ • Create tokens │
   │                                         │ • Sign with key │
   │                                         └──────┬──────────┘
   │                                                │
   │ 200 OK                                         │
   │ {access_token, refresh_token}                  │
   │<───────────────────────────────────────────────┤
   │                                                │
   │ Store tokens                                   │
   │                                                │
   │ GET /api/v1/projects                           │
   │ Authorization: Bearer <token>                  │
   ├──────────────────────────────────────────────>│
   │                                                │
   │                                         ┌──────┴────────┐
   │                                         │ Middleware    │
   │                                         │ • Logging     │
   │                                         │ • CORS        │
   │                                         │ • Rate limit  │
   │                                         └──────┬────────┘
   │                                                │
   │                                         ┌──────┴────────────┐
   │                                         │ Auth Dependency   │
   │                                         │ • Extract token   │
   │                                         │ • Verify token    │
   │                                         │ • Load user       │
   │                                         │ • Check role      │
   │                                         └──────┬────────────┘
   │                                                │
   │                                         ┌──────┴────────┐
   │                                         │ Projects      │
   │                                         │ Router        │
   │                                         │ • Query DB    │
   │                                         │ • Paginate    │
   │                                         └──────┬────────┘
   │                                                │
   │ 200 OK                                         │
   │ {items: [...], total: 10}                      │
   │<───────────────────────────────────────────────┤
   │                                                │
```

### 2. Rate Limiting Flow

```
Request → Middleware → Rate Limiter
                         │
                         ├─ Get identifier (user ID/API key/IP)
                         │
                         ├─ Check Redis
                         │   ├─ Key: ratelimit:{identifier}:minute
                         │   └─ Key: ratelimit:{identifier}:hour
                         │
                         ├─ Increment counters
                         │
                         ├─ Compare with limits
                         │
                         ├─ If exceeded → 429 Too Many Requests
                         │
                         └─ If OK → Continue + Add headers
                                     │
                                     └─ X-RateLimit-Remaining: 55
                                        X-RateLimit-Reset: 1704715200
```

### 3. WebSocket Flow

```
┌──────┐                                     ┌──────────────┐
│Client│                                     │  FastAPI App │
└──┬───┘                                     └──────┬───────┘
   │                                                │
   │ WS Connect /ws/agents/{agent_id}               │
   │ ?token=<jwt_token>                             │
   ├──────────────────────────────────────────────>│
   │                                                │
   │                                         ┌──────┴──────────┐
   │                                         │ WS Auth         │
   │                                         │ • Verify token  │
   │                                         │ • Check access  │
   │                                         └──────┬──────────┘
   │                                                │
   │ WS Connected                                   │
   │<───────────────────────────────────────────────┤
   │                                                │
   │                                         ┌──────┴──────────┐
   │                                         │ Room Manager    │
   │                                         │ • Join room     │
   │                                         │ • Subscribe     │
   │                                         └──────┬──────────┘
   │                                                │
   │                                         [Agent starts]
   │                                                │
   │                                         ┌──────┴──────────┐
   │                                         │ Event Broadcast │
   │                                         │ • Publish Redis │
   │                                         └──────┬──────────┘
   │                                                │
   │                                         ┌──────┴──────────┐
   │                                         │ WS Handler      │
   │                                         │ • Receive event │
   │                                         │ • Send to room  │
   │                                         └──────┬──────────┘
   │                                                │
   │ WS Message                                     │
   │ {type: "status", status: "running"}            │
   │<───────────────────────────────────────────────┤
   │                                                │
```

## Component Responsibilities

### Main Application (`main.py`)
- Application initialization
- Middleware registration
- Router registration
- Exception handling
- Lifespan management
- Health checks

### Configuration (`config.py`)
- Environment variable loading
- Settings validation
- Default values
- Type safety

### Authentication Module (`auth/`)
- JWT token creation/validation
- Password hashing/verification
- API key generation/validation
- OAuth integration
- RBAC enforcement
- User authentication dependencies

### Routers (`routers/`)
- Endpoint definitions
- Request validation
- Response serialization
- Business logic orchestration
- Database queries (when implemented)

### Middleware (`middleware/`)
- **CORS**: Cross-origin request handling
- **Rate Limiting**: Request throttling per user/IP
- **Logging**: Structured logging with correlation IDs

### WebSocket (`websocket/`)
- Real-time connections
- Room management
- Event broadcasting
- Authentication
- Message routing

## Data Flow

### Write Operation (Create Project)

```
Client Request
    ↓
Middleware (Logging, CORS, Rate Limit)
    ↓
Authentication (Verify JWT/API Key)
    ↓
Authorization (Check Role/Scopes)
    ↓
Request Validation (Pydantic)
    ↓
Router Handler (projects.py)
    ↓
Business Logic (validate repository, etc.)
    ↓
Database Write (PostgreSQL)
    ↓
Cache Invalidation (Redis)
    ↓
Event Broadcast (WebSocket/Redis)
    ↓
Response Serialization (Pydantic)
    ↓
Middleware (Add headers, log response)
    ↓
Client Response
```

### Read Operation (List Projects)

```
Client Request
    ↓
Middleware (Logging, CORS, Rate Limit)
    ↓
Authentication (Verify JWT/API Key)
    ↓
Authorization (Check Role/Scopes)
    ↓
Request Validation (Query params)
    ↓
Router Handler (projects.py)
    ↓
Cache Check (Redis)
    ├─ Hit → Return cached data
    └─ Miss ↓
Database Query (PostgreSQL with pagination)
    ↓
Cache Write (Redis with TTL)
    ↓
Response Serialization (Pydantic)
    ↓
Middleware (Add headers, log response)
    ↓
Client Response
```

## Security Layers

```
┌────────────────────────────────────────┐
│  Layer 1: Network Security             │
│  • HTTPS/TLS                           │
│  • Reverse proxy                       │
│  • Firewall rules                      │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│  Layer 2: Request Validation           │
│  • CORS origin check                   │
│  • Content-Type validation             │
│  • Request size limits                 │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│  Layer 3: Rate Limiting                │
│  • Per-user limits                     │
│  • Per-IP limits                       │
│  • Per-endpoint limits                 │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│  Layer 4: Authentication               │
│  • JWT verification                    │
│  • API key validation                  │
│  • Token expiration check              │
│  • Revocation check                    │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│  Layer 5: Authorization                │
│  • Role-based access (RBAC)            │
│  • Scope-based permissions             │
│  • Resource ownership check            │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│  Layer 6: Input Validation             │
│  • Pydantic model validation           │
│  • Type checking                       │
│  • Business rule validation            │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│  Layer 7: Data Security                │
│  • SQL injection prevention            │
│  • Parameterized queries               │
│  • Password hashing (bcrypt)           │
│  • Sensitive data masking in logs      │
└────────────────────────────────────────┘
```

## Scalability

### Horizontal Scaling

```
                    Load Balancer
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───┴───┐        ┌───┴───┐        ┌───┴───┐
    │ API   │        │ API   │        │ API   │
    │ Pod 1 │        │ Pod 2 │        │ Pod 3 │
    └───┬───┘        └───┬───┘        └───┬───┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───┴───────┐   ┌────┴────┐   ┌──────┴──────┐
    │ PostgreSQL│   │  Redis  │   │   GitHub    │
    │ (Primary) │   │ Cluster │   │     API     │
    └───────────┘   └─────────┘   └─────────────┘
```

### Caching Strategy

```
Request
    ↓
L1: Application Cache (in-memory)
    ├─ Hit → Return
    └─ Miss ↓
L2: Redis Cache (distributed)
    ├─ Hit → Return + Update L1
    └─ Miss ↓
L3: Database (PostgreSQL)
    ↓
Update L2 + L1
    ↓
Return Response
```

## Monitoring Points

```
┌─────────────────────────────────────────┐
│  Metrics Collection                     │
│                                         │
│  • Request count (per endpoint)         │
│  • Response time (p50, p95, p99)        │
│  • Error rate (per error type)          │
│  • Active connections                   │
│  • Database query time                  │
│  • Cache hit rate                       │
│  • Rate limit violations                │
│  • Authentication failures              │
│                                         │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Logging                                │
│                                         │
│  • Structured JSON logs                 │
│  • Correlation IDs                      │
│  • Request/Response logs                │
│  • Error stack traces                   │
│  • Security events                      │
│                                         │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Alerting                               │
│                                         │
│  • High error rate (> 5%)               │
│  • Slow responses (> 1s)                │
│  • Database connection pool exhaustion  │
│  • High memory usage (> 80%)            │
│  • Failed authentication spike          │
│                                         │
└─────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────── Production Environment ───────────────────┐
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Nginx      │         │   Certbot    │                  │
│  │ (Port 80/443)│◄────────┤ (SSL Certs)  │                  │
│  └──────┬───────┘         └──────────────┘                  │
│         │                                                    │
│         │ Reverse Proxy                                     │
│         ↓                                                    │
│  ┌────────────────────────────────────┐                     │
│  │   FastAPI (Uvicorn Workers)        │                     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐       │                     │
│  │  │  W1  │ │  W2  │ │  W3  │       │                     │
│  │  └──┬───┘ └──┬───┘ └──┬───┘       │                     │
│  └─────┼────────┼────────┼────────────┘                     │
│        │        │        │                                   │
│        └────────┼────────┘                                   │
│                 │                                            │
│         ┌───────┴────────┐                                   │
│         │                │                                   │
│    ┌────┴──────┐   ┌─────┴─────┐                           │
│    │PostgreSQL │   │   Redis   │                           │
│    │(Managed)  │   │ (Managed) │                           │
│    └───────────┘   └───────────┘                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

This architecture provides a robust, scalable, and secure foundation for the SWE Agent API!
