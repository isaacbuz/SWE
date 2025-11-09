# Audit Logging

Comprehensive audit logging for compliance and security.

## Installation

```bash
pnpm add @ai-company/audit-logging
```

## Usage

### Basic Setup

```typescript
import { createAuditLogger, AuditEventType } from '@ai-company/audit-logging';
import { createLogger } from '@ai-company/observability';

const structuredLogger = createLogger({ serviceName: 'my-service' });
const auditLogger = createAuditLogger({
  serviceName: 'my-service',
  enableStructuredLogging: true,
  structuredLogger,
});

// Log user action
await auditLogger.logUserAction(
  'user-123',
  'user@example.com',
  'create',
  'project',
  'project-456',
  'success'
);

// Log tool execution
await auditLogger.logToolExecution(
  'user-123',
  'github_create_issue',
  'success',
  { issueId: '789' }
);

// Query audit logs
const logs = await auditLogger.query({
  userId: 'user-123',
  eventType: AuditEventType.TOOL_EXECUTE,
  limit: 100,
});
```

## Event Types

- `USER_LOGIN`, `USER_LOGOUT`
- `USER_CREATE`, `USER_UPDATE`, `USER_DELETE`
- `PROJECT_CREATE`, `PROJECT_UPDATE`, `PROJECT_DELETE`
- `AGENT_CREATE`, `AGENT_UPDATE`, `AGENT_DELETE`, `AGENT_EXECUTE`
- `TOOL_EXECUTE`, `TOOL_CREATE`, `TOOL_UPDATE`, `TOOL_DELETE`
- `API_ACCESS`, `API_ERROR`
- `PERMISSION_GRANT`, `PERMISSION_REVOKE`
- `CONFIG_CHANGE`, `SECURITY_EVENT`

## Query Filters

```typescript
const filters: AuditLogFilters = {
  userId: 'user-123',
  eventType: AuditEventType.TOOL_EXECUTE,
  resourceType: 'tool',
  startDate: new Date('2025-11-01'),
  endDate: new Date('2025-11-09'),
  result: 'success',
  limit: 100,
  offset: 0,
};

const logs = await auditLogger.query(filters);
```

## Related

- [Structured Logging](../observability/src/logging/README.md)
- [Audit Logging API](../../apps/api/routers/audit.py)
