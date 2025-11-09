# Troubleshooting Guide

## Common Issues

### "Tool not found"

**Symptoms**: Error message "Tool 'toolName' not found"

**Causes**:
- Tool not registered in OpenAPI spec
- Tool name doesn't match operationId
- Tool registry hasn't loaded the spec

**Solutions**:
1. Check tool is defined in OpenAPI spec with `operationId`
2. Verify tool name matches `operationId` exactly
3. Ensure registry loaded the spec:
   ```typescript
   await registry.loadSpecs(["./tools/openapi/my-tools.yaml"]);
   ```
4. Check tool is registered:
   ```typescript
   const tool = registry.getToolByName("toolName");
   console.log(tool); // Should not be undefined
   ```

---

### "Permission denied"

**Symptoms**: Error message "User 'userId' does not have permission to execute 'toolName'"

**Causes**:
- User doesn't have required role
- Tool permissions not configured
- Permission conditions not met

**Solutions**:
1. Check user roles:
   ```typescript
   const userPerms = permissionChecker.getUserPermissions(userId);
   console.log(userPerms.roles);
   ```
2. Verify tool permissions:
   ```typescript
   const permissions = await permissionChecker.getUserPermissionsList(userId);
   console.log(permissions);
   ```
3. Grant permission if needed:
   ```typescript
   await permissionChecker.grantPermission(userId, {
     toolName: "toolName",
     operations: ["execute"],
   });
   ```

---

### "Rate limit exceeded"

**Symptoms**: Error message "Rate limit exceeded"

**Causes**:
- Too many requests in time window
- Per-user limit reached
- Per-tool limit reached
- Global limit reached

**Solutions**:
1. Check current usage:
   ```typescript
   const usage = await rateLimiter.getUsage(userId);
   console.log(usage);
   ```
2. Wait for reset time
3. Request quota increase if needed
4. Adjust rate limit configuration

---

### "Validation failed"

**Symptoms**: Error message "Validation failed: ..."

**Causes**:
- Invalid input arguments
- Missing required fields
- Type mismatches
- Constraint violations

**Solutions**:
1. Check error message for specific field
2. Verify input matches schema:
   ```typescript
   const toolSpec = registry.getToolByName("toolName");
   console.log(toolSpec.jsonSchema);
   ```
3. Fix input to match schema requirements
4. Check for type mismatches (string vs number, etc.)

---

### "Circuit breaker is open"

**Symptoms**: Error message "Circuit breaker is open for tool 'toolName'"

**Causes**:
- Tool has failed multiple times
- Circuit breaker opened due to failures
- Tool is temporarily disabled

**Solutions**:
1. Wait for reset timeout
2. Check tool handler for errors
3. Fix underlying issue
4. Manually reset circuit breaker if needed

---

### Tool execution timeout

**Symptoms**: Error message "Tool execution timed out"

**Causes**:
- Tool handler taking too long
- External API slow or unresponsive
- Timeout configured too low

**Solutions**:
1. Increase timeout:
   ```typescript
   const executor = new ToolExecutor({
     timeout: 60000, // 60 seconds
   });
   ```
2. Optimize tool handler performance
3. Check external API status
4. Implement async operations properly

---

### LLM not calling tools

**Symptoms**: LLM responds with text instead of tool calls

**Causes**:
- Tools not provided to LLM
- LLM provider doesn't support tool calling
- Tool specs not converted correctly

**Solutions**:
1. Verify tools are passed to LLM:
   ```typescript
   const tools = registry.getToolSpecs();
   const completion = await llmProvider.complete(messages, tools);
   ```
2. Check LLM provider supports tool calling
3. Verify tool spec conversion:
   ```typescript
   const llmTools = convertToolsToLLMFormat(toolSpecs);
   console.log(llmTools);
   ```

---

## Debugging Tips

### Enable Debug Logging

```typescript
// Set log level
process.env.LOG_LEVEL = "debug";
```

### Check Pipeline State

```typescript
const stats = pipeline.getStats();
console.log(stats);
```

### Inspect Tool Specs

```typescript
const tool = registry.getToolByName("toolName");
console.log(JSON.stringify(tool, null, 2));
```

### Test Tool Handler Directly

```typescript
const handler = toolExecutor.getRegisteredTools();
const result = await handler("myTool", { arg: "value" });
console.log(result);
```

## Getting Help

1. Check this troubleshooting guide
2. Review [API Reference](./api-reference.md)
3. See [Examples](./examples/) for working code
4. Check GitHub issues for similar problems

