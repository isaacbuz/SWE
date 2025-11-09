# Adding LLM Providers Guide

## Overview

This guide explains how to add new LLM providers to the system.

## Steps

### 1. Implement LLMProvider Interface

Create a new provider class:

```typescript
import { LLMProvider, CompletionOptions, CompletionResult } from '@ai-company/llm-providers';

export class MyProvider implements LLMProvider {
  readonly name = 'my-provider:model-1';
  readonly maxContext = 128_000;
  readonly pricePerMTokIn = 10.0;
  readonly pricePerMTokOut = 30.0;
  readonly capabilities = {
    tools: true,
    vision: false,
    streaming: true,
    jsonMode: true,
  };

  async completion(opts: CompletionOptions): Promise<CompletionResult> {
    // Implement provider-specific logic
    // Convert ToolSpec[] to provider format
    // Call provider API
    // Return normalized result
  }

  async *streamCompletion(opts: CompletionOptions): AsyncIterable<CompletionChunk> {
    // Implement streaming logic
  }
}
```

### 2. Handle Tool Calling Format

Each provider has different tool calling formats:

**OpenAI Format**:
```typescript
{
  type: 'function',
  function: {
    name: 'toolName',
    parameters: { /* JSON Schema */ }
  }
}
```

**Anthropic Format**:
```typescript
{
  name: 'toolName',
  description: '...',
  input_schema: { /* JSON Schema */ }
}
```

**Google Gemini Format**:
```typescript
{
  functionDeclarations: [{
    name: 'toolName',
    description: '...',
    parameters: { /* JSON Schema */ }
  }]
}
```

### 3. Handle Errors

Map provider errors to standard error types:

```typescript
import {
  RateLimitError,
  AuthenticationError,
  InvalidRequestError,
} from '@ai-company/llm-providers';

try {
  // Call provider API
} catch (error) {
  if (error.status === 429) {
    throw new RateLimitError('Rate limit exceeded', retryAfter);
  }
  if (error.status === 401) {
    throw new AuthenticationError('Invalid API key');
  }
  throw new InvalidRequestError(error.message);
}
```

### 4. Register with MoE Router

```typescript
import { MoERouter } from '@ai-company/moe-router';

const router = new MoERouter();
router.registerProvider(new MyProvider());

const decision = router.selectProvider({
  taskType: TaskType.CODE_GENERATION,
  qualityRequirement: 0.8,
});
```

### 5. Update Quality Scores

Update the MoE router's quality scoring to include your provider:

```typescript
// In MoERouter.ts
private getQualityScore(provider: LLMProvider): number {
  if (provider.name.includes('my-provider:premium')) {
    return 0.95;
  }
  // ... other providers
}
```

## Example: Google Gemini

See `packages/llm-providers/src/providers/google/GeminiProvider.ts` for a complete example.

## Testing

```typescript
import { MyProvider } from './MyProvider';

const provider = new MyProvider('api-key');

const result = await provider.completion({
  messages: [{ role: 'user', content: 'Hello!' }],
});

expect(result.content).toBeDefined();
expect(result.usage.totalTokens).toBeGreaterThan(0);
```

## Best Practices

1. **Normalize Responses**: Convert provider responses to standard format
2. **Handle Streaming**: Implement streaming if provider supports it
3. **Error Mapping**: Map all provider errors to standard types
4. **Cost Tracking**: Accurately track token usage and costs
5. **Documentation**: Document provider-specific features

## Related Documentation

- [LLM Provider Interface](../../packages/llm-providers/src/domain/LLMProvider.ts)
- [MoE Router](../../packages/moe-router-ts/README.md)
