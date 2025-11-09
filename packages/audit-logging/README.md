# @ai-company/audit-logging

Tool execution audit logging system with PII detection and redaction.

## Overview

Comprehensive audit logging for tool executions with automatic PII detection, redaction, and retention policies.

## Features

- ✅ Complete audit trail for all tool executions
- ✅ Automatic PII detection and redaction
- ✅ Configurable retention policies
- ✅ Query and filter capabilities
- ✅ Secure error sanitization

## Installation

```bash
pnpm add @ai-company/audit-logging
```

## Usage

### Basic Usage

```typescript
import { AuditLogger } from '@ai-company/audit-logging';

const logger = new AuditLogger({
  detectPII: true,
  includeArguments: true,
  includeResults: false,
  retentionDays: 90,
});

// Log tool execution
const logId = await logger.logExecution(
  'user-123',
  'createIssue',
  { title: 'Bug fix', body: 'Fix the bug' },
  { issueId: '123' },
  true,
  150,
  undefined,
  { ipAddress: '192.168.1.1' }
);
```

### Query Logs

```typescript
// Query logs for a user
const userLogs = await logger.queryLogs({
  userId: 'user-123',
  limit: 100,
});

// Query logs for a tool
const toolLogs = await logger.queryLogs({
  toolName: 'createIssue',
  startDate: new Date('2025-01-01'),
  success: true,
});
```

### Custom Storage

```typescript
import { AuditLogger, AuditLogStorage } from '@ai-company/audit-logging';

class DatabaseStorage implements AuditLogStorage {
  async save(entry: AuditLogEntry): Promise<void> {
    // Save to database
  }

  async query(filter: AuditLogFilter): Promise<AuditLogEntry[]> {
    // Query database
  }

  async deleteOlderThan(date: Date): Promise<number> {
    // Delete old entries
  }
}

const logger = new AuditLogger({
  storage: new DatabaseStorage(),
});
```

## PII Detection

Automatically detects and redacts:
- Email addresses
- Phone numbers
- SSNs
- Credit card numbers
- IP addresses

## Related Packages

- `@ai-company/tool-executor` - Tool execution engine

## License

MIT

