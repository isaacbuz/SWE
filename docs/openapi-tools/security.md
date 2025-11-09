# Security Best Practices

## Credential Management

### Never Log Credentials

```typescript
// ❌ BAD
console.log(`API Key: ${apiKey}`);

// ✅ GOOD
logger.info("API call made", { tool: "github/createPR" });
```

### Use Credential Vault

```typescript
import { CredentialVault } from "@ai-company/external-api-tools";

const vault = new CredentialVault();
vault.setCredentials("github", {
  apiKey: process.env.GITHUB_TOKEN, // From environment
});

// Credentials never exposed
const headers = vault.getAuthHeader("github");
```

### Rotate Credentials Regularly

- Set expiration dates
- Monitor credential usage
- Rotate on compromise

## Input Validation

### Always Validate Against Schema

```typescript
// ToolExecutor validates automatically
const result = await executor.execute(
  "myTool",
  userInput, // Automatically validated
  toolSpec,
);
```

### Sanitize User Inputs

```typescript
// ToolExecutor sanitizes automatically
// Additional sanitization if needed:
function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, "") // Remove HTML tags
    .trim()
    .slice(0, 1000); // Limit length
}
```

## Permission Enforcement

### Check Permissions Before Execution

```typescript
const executor = new ToolExecutor({
  checkPermissions: true,
  permissionChecker: permissionChecker,
});

// Permission checked automatically
await executor.execute("myTool", args, spec, userId);
```

### Use Least Privilege

- Grant minimum required permissions
- Use role-based access control
- Review permissions regularly

## Rate Limiting

### Enforce Rate Limits

```typescript
const executor = new ToolExecutor({
  rateLimit: true,
  rateLimiter: enhancedRateLimiter,
});

// Rate limits enforced automatically
```

### Monitor Usage

```typescript
const usage = await rateLimiter.getUsage(userId);
if (usage.costToday > usage.quotaDaily * 0.8) {
  // Alert user
}
```

## Audit Logging

### Log All Executions

```typescript
import { AuditLogger } from "@ai-company/observability";

await auditLogger.log_tool_execution(
  toolName="myTool",
  operation="execute",
  inputs={...}, // Sanitized
  outputs={...}, // Sanitized
  userId=userId,
  success=true
);
```

### PII Detection

- Audit logger automatically detects and redacts PII
- Never log credentials or sensitive data
- Review logs regularly

## Secure Communication

### Use HTTPS

- All external API calls use HTTPS
- Never send credentials over HTTP

### Validate Certificates

- Verify SSL certificates
- Use certificate pinning for critical APIs

## Error Handling

### Don't Expose Internal Details

```typescript
// ❌ BAD
throw new Error(`Database error: ${dbError.message}`);

// ✅ GOOD
throw new Error("Tool execution failed. Please try again.");
```

### Log Errors Securely

```typescript
logger.error("Tool execution failed", {
  tool: toolName,
  error: error.message, // No stack traces in production
  userId: userId,
});
```

## Compliance

### Data Retention

- Follow data retention policies
- Delete old audit logs per policy
- Encrypt sensitive data at rest

### Access Control

- Implement role-based access control
- Review access regularly
- Revoke access immediately on termination

## Security Checklist

- [ ] Credentials stored securely (never in code)
- [ ] All inputs validated against schemas
- [ ] Permissions checked before execution
- [ ] Rate limits enforced
- [ ] All executions logged
- [ ] PII detected and redacted
- [ ] Errors don't expose internal details
- [ ] HTTPS used for all external calls
- [ ] Certificates validated
- [ ] Access reviewed regularly
