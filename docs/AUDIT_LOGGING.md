# Audit Logging Guide

This guide covers audit logging implementation for compliance and security.

## Overview

The audit logging system provides:
- **User Action Tracking**: Track all user actions and changes
- **Compliance**: Meet regulatory requirements (SOC 2, GDPR, etc.)
- **Security Monitoring**: Detect suspicious activities
- **Change Tracking**: Track what changed and when
- **Forensics**: Investigate security incidents

## Implementation

### TypeScript/Node.js

**Location**: `packages/audit-logging/src/AuditLogger.ts`

```typescript
import { createAuditLogger, AuditEventType } from '@ai-company/audit-logging';

const auditLogger = createAuditLogger({
  serviceName: 'tool-service',
  enableStructuredLogging: true,
});

// Log user action
await auditLogger.logUserAction(
  'user-123',
  'user@example.com',
  'create',
  'project',
  'project-456'
);

// Log tool execution
await auditLogger.logToolExecution(
  'user-123',
  'github_create_issue',
  'success'
);
```

### Python/FastAPI

**Location**: `apps/api/services/audit_service.py`

```python
from services.audit_service import get_audit_logger

audit_logger = get_audit_logger()

# Log user action
await audit_logger.log_user_action(
    user_id='user-123',
    user_email='user@example.com',
    action='create',
    resource_type='project',
    resource_id='project-456'
)

# Log tool execution
await audit_logger.log_tool_execution(
    user_id='user-123',
    tool_name='github_create_issue',
    result='success'
)
```

## Database Schema

**Location**: `infrastructure/db/init.sql`

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    user_id UUID,
    user_email VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    result VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    metadata JSONB,
    changes JSONB
);
```

## API Endpoints

### Query Audit Logs

```http
GET /api/v1/audit/logs?user_id=user-123&event_type=tool.execute&limit=100
```

Returns audit log entries matching filters.

### Get Audit Log by ID

```http
GET /api/v1/audit/logs/{log_id}
```

Returns a specific audit log entry.

### Get Audit Summary

```http
GET /api/v1/audit/summary?days=7
```

Returns aggregated statistics:
- Total events
- Events by type
- Events by result
- Events by user
- Events by resource type

## Event Types

### User Events
- `user.login` - User login
- `user.logout` - User logout
- `user.create` - User creation
- `user.update` - User update
- `user.delete` - User deletion

### Project Events
- `project.create` - Project creation
- `project.update` - Project update
- `project.delete` - Project deletion

### Agent Events
- `agent.create` - Agent creation
- `agent.update` - Agent update
- `agent.delete` - Agent deletion
- `agent.execute` - Agent execution

### Tool Events
- `tool.execute` - Tool execution
- `tool.create` - Tool creation
- `tool.update` - Tool update
- `tool.delete` - Tool deletion

### API Events
- `api.access` - API access
- `api.error` - API error

### Permission Events
- `permission.grant` - Permission granted
- `permission.revoke` - Permission revoked

### System Events
- `config.change` - Configuration change
- `security.event` - Security event

## Usage Examples

### Log User Action

```typescript
await auditLogger.logUserAction(
  userId,
  userEmail,
  'update',
  'project',
  projectId,
  'success',
  { field: 'name', oldValue: 'Old', newValue: 'New' }
);
```

### Log Permission Change

```typescript
await auditLogger.logPermissionChange(
  adminUserId,
  targetUserId,
  'admin',
  'grant',
  'success'
);
```

### Log Security Event

```typescript
await auditLogger.logSecurityEvent(
  'failed_login',
  'high',
  'Multiple failed login attempts',
  { ipAddress: '1.2.3.4', attempts: 5 }
);
```

### Query Audit Logs

```typescript
const logs = await auditLogger.query({
  userId: 'user-123',
  eventType: AuditEventType.TOOL_EXECUTE,
  startDate: new Date('2025-11-01'),
  endDate: new Date('2025-11-09'),
  limit: 100,
});
```

## Compliance

### SOC 2 Requirements

- **Access Control**: Track all user access
- **Change Management**: Track configuration changes
- **Security Monitoring**: Track security events

### GDPR Requirements

- **Right to Access**: Users can query their audit logs
- **Right to Deletion**: Audit logs can be anonymized
- **Data Processing**: Track data processing activities

### HIPAA Requirements

- **Access Logs**: Track all PHI access
- **Audit Trails**: Maintain complete audit trails
- **Retention**: Retain logs for required period

## Best Practices

1. **Log Everything**: Log all user actions and system events
2. **Include Context**: Include user, resource, and request context
3. **Immutable Logs**: Never modify or delete audit logs
4. **Secure Storage**: Encrypt audit logs at rest
5. **Regular Review**: Regularly review audit logs for anomalies
6. **Retention Policy**: Define and enforce retention policies
7. **Access Control**: Restrict access to audit logs

## Retention

- **Active Logs**: 90 days in database
- **Archived Logs**: 7 years in cold storage
- **Compliance Logs**: Per regulatory requirements

## Related Documentation

- [Structured Logging](./STRUCTURED_LOGGING.md)
- [Security](./SECURITY.md)
- [Database Schema](../infrastructure/db/init.sql)

