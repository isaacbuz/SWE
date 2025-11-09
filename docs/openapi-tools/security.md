# Security Guidelines

## Overview

Security best practices for the OpenAPI Tools system.

## Credential Management

### Never Expose Credentials

```typescript
// ❌ BAD: Credentials in tool results
executor.registerTool(toolSpec, async (args) => {
  return {
    apiKey: process.env.API_KEY, // NEVER DO THIS
  };
});

// ✅ GOOD: Credentials managed separately
const vault = new CredentialVault();
const credentials = await vault.getCredentials('github');
// Use credentials internally, never return them
```

### Use Credential Vault

```typescript
import { EnvironmentCredentialVault } from '@ai-company/external-api-tools';

const vault = new EnvironmentCredentialVault();
const creds = await vault.getCredentials('github');
// Credentials never exposed to LLMs
```

## Input Validation

### Always Validate Inputs

```typescript
// Tool executor automatically validates against JSON Schema
executor.registerTool(toolSpec, async (args) => {
  // args already validated
  // Safe to use
});
```

### Sanitize User Input

```typescript
function sanitizeInput(input: string): string {
  // Remove potentially dangerous characters
  return input.replace(/[<>]/g, '');
}
```

## Audit Logging

### Log All Executions

```typescript
import { AuditLogger } from '@ai-company/audit-logging';

const logger = new AuditLogger({
  detectPII: true,
  includeArguments: true,
});

await logger.logExecution(
  userId,
  toolName,
  args,
  result,
  success,
  durationMs
);
```

### PII Detection

The audit logger automatically detects and redacts:
- Email addresses
- Phone numbers
- SSNs
- Credit card numbers
- IP addresses

## Permissions

### Use RBAC

```typescript
import { PermissionChecker, Role } from '@ai-company/permissions';

const checker = new PermissionChecker();

// Check permission before execution
if (!checker.hasPermission(userId, toolName, 'execute')) {
  throw new Error('Permission denied');
}
```

## Rate Limiting

### Enforce Rate Limits

```typescript
import { RateLimiter } from '@ai-company/rate-limiting';

const limiter = new RateLimiter();

const status = limiter.checkLimit({
  maxRequests: 100,
  windowMs: 60000,
  identifier: userId,
});

if (status.exceeded) {
  throw new Error('Rate limit exceeded');
}
```

## Best Practices

1. **Never trust LLM output**: Always validate tool arguments
2. **Use allowlists**: Only allow specific tools/operations
3. **Monitor usage**: Track all tool executions
4. **Set quotas**: Limit cost per user/team
5. **Regular audits**: Review audit logs regularly

## Related Documentation

- [Audit Logging](../../packages/audit-logging/README.md)
- [Permissions](../../packages/permissions/README.md)
- [Rate Limiting](../../packages/rate-limiting/README.md)

