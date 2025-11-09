# Troubleshooting Guide

## Common Issues

### Tool Not Found

**Problem**: `Tool ${name} not found`

**Solution**:
1. Check tool is loaded in registry
2. Verify operationId matches
3. Ensure spec file is loaded

```typescript
const tool = registry.getToolByName('myTool');
if (!tool) {
  console.error('Tool not found');
}
```

### Validation Errors

**Problem**: Input validation fails

**Solution**:
1. Check JSON Schema matches input
2. Verify required fields are provided
3. Check data types match

```typescript
const result = await executor.execute('myTool', args);
if (!result.success && result.validationErrors) {
  console.error('Validation errors:', result.validationErrors);
}
```

### Rate Limit Exceeded

**Problem**: Rate limit errors

**Solution**:
1. Check rate limit configuration
2. Implement exponential backoff
3. Use rate limit status to wait

```typescript
const status = limiter.getStatus(config);
if (status.exceeded) {
  const waitMs = status.resetAt.getTime() - Date.now();
  await new Promise((resolve) => setTimeout(resolve, waitMs));
}
```

### Provider Errors

**Problem**: LLM provider errors

**Solution**:
1. Check API key is valid
2. Verify model name is correct
3. Check rate limits
4. Review error messages

```typescript
try {
  const result = await provider.completion({ ... });
} catch (error) {
  if (error instanceof RateLimitError) {
    // Handle rate limit
  } else if (error instanceof AuthenticationError) {
    // Check API key
  }
}
```

### Pipeline Timeout

**Problem**: Pipeline exceeds max turns

**Solution**:
1. Increase maxTurns
2. Check for infinite loops
3. Verify tools complete successfully

```typescript
const result = await pipeline.executeWithTools(
  prompt,
  tools,
  { maxTurns: 10 } // Increase if needed
);
```

## Debugging Tips

### Enable Logging

```typescript
// Enable verbose logging
process.env.DEBUG = 'tool-pipeline:*';
```

### Check Tool Registry

```typescript
console.log('Loaded tools:', registry.getToolSpecs().map(t => t.name));
console.log('Tool count:', registry.getToolCount());
```

### Monitor Performance

```typescript
const start = Date.now();
const result = await executor.execute('myTool', args);
console.log(`Execution time: ${Date.now() - start}ms`);
```

## Getting Help

- Check [API Reference](./api-reference.md)
- Review [Architecture](./architecture.md)
- See [Examples](../../packages/tool-pipeline/README.md)

