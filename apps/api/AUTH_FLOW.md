# Authentication Flow Documentation

## Overview

The SWE Agent API implements a comprehensive authentication system supporting multiple authentication methods:

1. **JWT Bearer Token Authentication** (Primary method for users)
2. **API Key Authentication** (For programmatic/agent access)
3. **OAuth 2.0 Integration** (GitHub social login)

## Authentication Methods

### 1. JWT Bearer Token Authentication

JWT (JSON Web Token) is the primary authentication method for user-facing applications.

#### Token Types

**Access Token**:

- Short-lived (default: 30 minutes)
- Used for API requests
- Contains user identity and permissions
- Stateless validation

**Refresh Token**:

- Long-lived (default: 7 days)
- Used to obtain new access tokens
- More secure rotation mechanism
- Can be revoked

#### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid",
    "email": "user@example.com",
    "role": "user",
    "scopes": ["projects:read", "projects:write"],
    "token_type": "access",
    "exp": 1704715200,
    "iat": 1704713400,
    "jti": "token-uuid"
  },
  "signature": "..."
}
```

#### Flow Diagram

```
┌─────────┐                                   ┌─────────┐
│ Client  │                                   │   API   │
└────┬────┘                                   └────┬────┘
     │                                             │
     │  1. POST /auth/token                        │
     │     {email, password}                       │
     │────────────────────────────────────────────>│
     │                                             │
     │                                             │ 2. Validate credentials
     │                                             │    Hash password
     │                                             │    Query database
     │                                             │
     │  3. Return tokens                           │
     │     {access_token, refresh_token}           │
     │<────────────────────────────────────────────│
     │                                             │
     │  4. Store tokens                            │
     │     (localStorage/sessionStorage)           │
     │                                             │
     │  5. API Request                             │
     │     Authorization: Bearer {access_token}    │
     │────────────────────────────────────────────>│
     │                                             │
     │                                             │ 6. Verify token
     │                                             │    Decode JWT
     │                                             │    Check expiration
     │                                             │    Validate signature
     │                                             │
     │  7. Return response                         │
     │<────────────────────────────────────────────│
     │                                             │
     │  8. Token expires                           │
     │                                             │
     │  9. POST /auth/refresh                      │
     │     {refresh_token}                         │
     │────────────────────────────────────────────>│
     │                                             │
     │                                             │ 10. Verify refresh token
     │                                             │     Generate new access token
     │                                             │
     │  11. Return new access token                │
     │<────────────────────────────────────────────│
     │                                             │
```

#### Implementation Details

**Obtaining Tokens**:

```bash
# Request
POST /api/v1/auth/token
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}

# Response
HTTP/1.1 200 OK
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Using Access Token**:

```bash
# Request
GET /api/v1/projects
Authorization: Bearer eyJhbGc...

# Response
HTTP/1.1 200 OK
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

**Refreshing Token**:

```bash
# Request
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}

# Response
HTTP/1.1 200 OK
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Token Expiration Handling**:

```javascript
// Client-side example
async function apiRequest(url, options = {}) {
  let token = getAccessToken();

  // Try request with current token
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  // If token expired, refresh and retry
  if (response.status === 401) {
    token = await refreshAccessToken();
    response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return response;
}
```

### 2. API Key Authentication

API keys provide a simpler authentication method for programmatic access, ideal for:

- CI/CD pipelines
- Automated scripts
- Agent-to-API communication
- Third-party integrations

#### API Key Structure

```
swe_<32_random_characters>

Example: swe_kj8h3f9d2n4m5p6q7r8s9t0u1v2w3x4y
```

Components:

- **Prefix** (`swe_`): Identifies the key type
- **Random Part**: Cryptographically secure random string
- **Storage**: Hashed using bcrypt (similar to passwords)

#### Flow Diagram

```
┌─────────┐                                   ┌─────────┐
│ Client  │                                   │   API   │
└────┬────┘                                   └────┬────┘
     │                                             │
     │  1. POST /auth/api-keys                     │
     │     Authorization: Bearer {token}           │
     │     {name, scopes, expires_at}              │
     │────────────────────────────────────────────>│
     │                                             │
     │                                             │ 2. Generate API key
     │                                             │    Hash key
     │                                             │    Store in database
     │                                             │
     │  3. Return API key (ONLY TIME SHOWN!)       │
     │     {key: "swe_...", ...}                   │
     │<────────────────────────────────────────────│
     │                                             │
     │  4. Store API key securely                  │
     │     (env variables, secrets manager)        │
     │                                             │
     │  5. API Request                             │
     │     X-API-Key: swe_...                      │
     │────────────────────────────────────────────>│
     │                                             │
     │                                             │ 6. Verify API key
     │                                             │    Extract prefix
     │                                             │    Query database
     │                                             │    Verify hash
     │                                             │    Check expiration
     │                                             │    Check scopes
     │                                             │    Update last_used_at
     │                                             │
     │  7. Return response                         │
     │<────────────────────────────────────────────│
     │                                             │
```

#### Implementation Details

**Creating API Key**:

```bash
# Request (requires authentication)
POST /api/v1/auth/api-keys
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "name": "CI/CD Pipeline",
  "description": "For automated deployments",
  "scopes": ["projects:read", "agents:write"],
  "expires_at": "2026-01-08T00:00:00Z"
}

# Response (key shown ONLY on creation!)
HTTP/1.1 201 Created
{
  "id": "key-uuid",
  "user_id": "user-uuid",
  "name": "CI/CD Pipeline",
  "key": "swe_kj8h3f9d2n4m5p6q7r8s9t0u1v2w3x4y",
  "key_prefix": "swe_kj8h",
  "scopes": ["projects:read", "agents:write"],
  "is_active": true,
  "expires_at": "2026-01-08T00:00:00Z",
  "last_used_at": null,
  "created_at": "2025-01-08T12:00:00Z"
}
```

**Using API Key**:

```bash
# Request
GET /api/v1/projects
X-API-Key: swe_kj8h3f9d2n4m5p6q7r8s9t0u1v2w3x4y

# Response
HTTP/1.1 200 OK
{
  "items": [...],
  "total": 10
}
```

**Listing API Keys**:

```bash
# Request
GET /api/v1/auth/api-keys
Authorization: Bearer eyJhbGc...

# Response (full key never returned)
HTTP/1.1 200 OK
{
  "items": [
    {
      "id": "key-uuid",
      "name": "CI/CD Pipeline",
      "key_prefix": "swe_kj8h",
      "scopes": ["projects:read", "agents:write"],
      "is_active": true,
      "last_used_at": "2025-01-08T13:00:00Z",
      "created_at": "2025-01-08T12:00:00Z"
    }
  ]
}
```

**Revoking API Key**:

```bash
# Request
DELETE /api/v1/auth/api-keys/{key_id}
Authorization: Bearer eyJhbGc...

# Response
HTTP/1.1 204 No Content
```

### 3. OAuth 2.0 (GitHub Integration)

OAuth 2.0 allows users to authenticate using their GitHub accounts.

#### Flow Diagram

```
┌─────────┐         ┌─────────┐         ┌─────────┐
│ Client  │         │   API   │         │ GitHub  │
└────┬────┘         └────┬────┘         └────┬────┘
     │                   │                   │
     │  1. Initiate      │                   │
     │     Login         │                   │
     │──────────────────>│                   │
     │                   │                   │
     │                   │ 2. Generate state │
     │                   │    (CSRF token)   │
     │                   │                   │
     │  3. Redirect to   │                   │
     │     GitHub        │                   │
     │<──────────────────│                   │
     │                                       │
     │  4. GitHub Auth                       │
     │──────────────────────────────────────>│
     │                                       │
     │                                       │ 5. User authorizes
     │                                       │
     │  6. Redirect with code & state        │
     │<──────────────────────────────────────│
     │                                       │
     │  7. Send code & state                 │
     │──────────────────>│                   │
     │                   │                   │
     │                   │ 8. Verify state   │
     │                   │    (CSRF check)   │
     │                   │                   │
     │                   │ 9. Exchange code  │
     │                   │    for token      │
     │                   │──────────────────>│
     │                   │                   │
     │                   │ 10. GitHub token  │
     │                   │<──────────────────│
     │                   │                   │
     │                   │ 11. Get user info │
     │                   │──────────────────>│
     │                   │                   │
     │                   │ 12. User data     │
     │                   │<──────────────────│
     │                   │                   │
     │                   │ 13. Create/update │
     │                   │     user in DB    │
     │                   │                   │
     │                   │ 14. Generate JWT  │
     │                   │                   │
     │  15. JWT tokens   │                   │
     │<──────────────────│                   │
     │                   │                   │
```

#### Implementation Details

**Step 1: Initiate Login**:

```bash
# Request
GET /api/v1/auth/github/login?redirect_uri=http://localhost:3000/dashboard

# Response (redirect)
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?
  client_id=<github_client_id>&
  redirect_uri=http://localhost:8000/api/v1/auth/github/callback&
  scope=read:user,user:email&
  state=<random_state_token>
```

**Step 2: User Authorizes on GitHub**

User grants permissions on GitHub's authorization page.

**Step 3: GitHub Redirects Back**:

```
GET /api/v1/auth/github/callback?
  code=<authorization_code>&
  state=<state_token>
```

**Step 4: API Exchanges Code**:

Backend exchanges authorization code for access token and user info.

**Step 5: Return JWT Tokens**:

```bash
# Response (final redirect to frontend)
HTTP/1.1 302 Found
Location: http://localhost:3000/dashboard?
  access_token=<jwt_access_token>&
  refresh_token=<jwt_refresh_token>
```

Frontend extracts tokens from URL and stores them.

## Role-Based Access Control (RBAC)

### User Roles

| Role       | Description        | Permissions                  |
| ---------- | ------------------ | ---------------------------- |
| `admin`    | Administrator      | Full access to all resources |
| `user`     | Regular user       | Access to own resources      |
| `agent`    | Programmatic agent | Limited to agent operations  |
| `readonly` | Read-only user     | View-only access             |

### Permission Scopes

Fine-grained permissions for API keys and tokens:

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

### Enforcement

**Route-level**:

```python
@router.get("/admin-only")
async def admin_endpoint(user = Depends(require_admin)):
    # Only admins can access
    pass
```

**Scope-level**:

```python
@router.post("/projects")
async def create_project(
    user = Depends(ScopeChecker(["projects:write"]))
):
    # Requires projects:write scope
    pass
```

## Security Best Practices

### Token Storage

**Frontend**:

- ✅ Use `httpOnly` cookies (if supporting cookies)
- ✅ Use secure session storage
- ❌ Never use `localStorage` for sensitive tokens
- ✅ Clear tokens on logout

**Backend**:

- ✅ Hash API keys with bcrypt
- ✅ Use strong JWT secret (min 32 bytes)
- ✅ Rotate JWT secrets periodically
- ✅ Implement token revocation list (Redis)

### Token Expiration

**Short-lived Access Tokens**:

- Default: 30 minutes
- Reduces impact of token compromise
- Forces regular refresh

**Long-lived Refresh Tokens**:

- Default: 7 days
- Stored more securely
- Can be rotated on use

### HTTPS Requirements

- ✅ **Production**: Always use HTTPS
- ✅ Prevent token interception
- ✅ Enable HSTS headers
- ✅ Use secure cookies

### Rate Limiting

Prevent brute force attacks:

- 5 login attempts per minute
- 60 API requests per minute
- Track by IP and user ID

### CSRF Protection

For OAuth flows:

- Generate random state token
- Store in session/cookie
- Verify on callback
- Single-use tokens

## Error Handling

### Authentication Errors

**Invalid Credentials**:

```json
{
  "error": {
    "code": 401,
    "message": "Invalid email or password",
    "type": "authentication_error"
  }
}
```

**Expired Token**:

```json
{
  "error": {
    "code": 401,
    "message": "Token has expired",
    "type": "token_expired"
  }
}
```

**Invalid Token**:

```json
{
  "error": {
    "code": 401,
    "message": "Invalid or malformed token",
    "type": "invalid_token"
  }
}
```

**Insufficient Permissions**:

```json
{
  "error": {
    "code": 403,
    "message": "Insufficient permissions",
    "type": "permission_denied",
    "required_role": "admin"
  }
}
```

## Testing Authentication

### cURL Examples

**JWT Login**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

**Authenticated Request**:

```bash
TOKEN="eyJhbGc..."
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN"
```

**API Key Request**:

```bash
API_KEY="swe_abc123..."
curl http://localhost:8000/api/v1/projects \
  -H "X-API-Key: $API_KEY"
```

### Python Example

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    json={"email": "user@example.com", "password": "password"}
)
tokens = response.json()

# Use token
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
projects = requests.get(
    "http://localhost:8000/api/v1/projects",
    headers=headers
).json()
```

### JavaScript Example

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

// Use token
const projectsResponse = await fetch("http://localhost:8000/api/v1/projects", {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
const projects = await projectsResponse.json();
```

## Conclusion

The SWE Agent API provides flexible, secure authentication supporting:

- **JWT tokens** for user sessions
- **API keys** for programmatic access
- **OAuth 2.0** for social login
- **RBAC** for fine-grained permissions
- **Comprehensive security** measures
