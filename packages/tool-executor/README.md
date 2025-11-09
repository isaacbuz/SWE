# @ai-company/tool-executor

Secure tool executor with schema validation for LLM tool calling.

## Overview

This package provides a secure execution engine for tools defined in OpenAPI specifications. It validates inputs, enforces rate limits, implements circuit breakers, and provides comprehensive error handling.

## Features

- ✅ JSON Schema validation of inputs
- ✅ Rate limiting per tool and identifier
- ✅ Circuit breaker for failing tools
- ✅ Execution timeout handling
- ✅ Retry logic with exponential backoff
- ✅ Comprehensive error handling
- ✅ Execution logging and metrics

## Installation

```bash
pnpm add @ai-company/tool-executor
```

## Usage

### Basic Example

```typescript
import { ToolExecutor } from '@ai-company/tool-executor';
import { ToolSpec } from '@ai-company/openapi-tools';

// Create executor
const executor = new ToolExecutor();

// Define a tool spec
const toolSpec: ToolSpec = {
  name: 'createIssue',
  description: 'Create a GitHub issue',
  jsonSchema: {
    type: 'object',
    required: ['title', 'body'],
    properties: {
      title: { type: 'string' },
      body: { type: 'string' },
    },
  },
  operationId: 'createIssue',
};

// Register tool handler
executor.registerTool(toolSpec, async (args) => {
  const { title, body } = args as { title: string; body: string };
  // Execute tool logic
  return { success: true, issueId: '123' };
});

// Execute tool
const result = await executor.execute('createIssue', {
  title: 'New Issue',
  body: 'Issue description',
});

if (result.success) {
  console.log('Result:', result.result);
} else {
  console.error('Error:', result.error);
}
```

### Advanced Configuration

```typescript
import { ToolExecutor } from '@ai-company/tool-executor';

const executor = new ToolExecutor();

// Set rate limit for a tool
executor.setRateLimit('createIssue', {
  maxRequests: 10,
  windowMs: 60000, // 1 minute
  identifier: 'user-123',
});

// Execute with options
const result = await executor.execute(
  'createIssue',
  { title: 'Issue', body: 'Body' },
  {
    validateInputs: true,
    timeoutMs: 5000,
    retryOnFailure: true,
    maxRetries: 3,
    metadata: { userId: 'user-123' },
  }
);
```

## API Reference

### ToolExecutor

Main class for executing tools securely.

#### Methods

- `registerTool(toolSpec: ToolSpec, handler: ToolHandler): void` - Register a tool
- `unregisterTool(name: string): void` - Unregister a tool
- `execute(toolName: string, args: unknown, options?: ToolExecutionOptions): Promise<ToolResult>` - Execute a tool
- `setRateLimit(toolName: string, config: RateLimitConfig): void` - Set rate limit
- `getCircuitBreakerState(toolName: string): CircuitBreakerState | undefined` - Get circuit breaker state
- `resetCircuitBreaker(toolName: string): void` - Reset circuit breaker
- `hasTool(toolName: string): boolean` - Check if tool is registered
- `getRegisteredTools(): string[]` - Get list of registered tools

### ToolResult

Result of tool execution.

```typescript
interface ToolResult {
  toolName: string;
  result: unknown;
  durationMs: number;
  success: boolean;
  error?: string;
  validationErrors?: string[];
  metadata?: object;
}
```

## Security Features

### Input Validation

All inputs are validated against JSON Schema before execution. Invalid inputs are rejected with detailed error messages.

### Rate Limiting

Rate limits can be configured per tool and per identifier (user ID, IP, etc.). Requests exceeding the limit are rejected.

### Circuit Breaker

Circuit breakers automatically open after repeated failures, preventing cascading failures. They automatically recover after a cooldown period.

### Timeout Protection

All tool executions have a configurable timeout to prevent hanging operations.

## Error Handling

The executor provides detailed error information:

- **Validation errors**: Detailed JSON Schema validation errors
- **Rate limit errors**: Clear messages when rate limits are exceeded
- **Circuit breaker errors**: Information about when circuit breaker will retry
- **Execution errors**: Original error messages from tool handlers
- **Timeout errors**: Clear indication when execution times out

## Testing

```bash
# Run tests
pnpm test

# Run with coverage
pnpm test:coverage
```

## Related Packages

- `@ai-company/openapi-tools` - OpenAPI tool registry
- `@ai-company/llm-providers` - LLM provider implementations

## License

MIT

