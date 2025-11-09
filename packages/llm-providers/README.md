# @ai-company/llm-providers

Provider-agnostic LLM interface for TypeScript/Node.js.

## Overview

This package defines a unified interface that all LLM providers (OpenAI, Anthropic, Google, etc.) must implement, enabling the MoE router to work with any provider seamlessly.

## Features

- ✅ Provider-agnostic interface
- ✅ Tool/function calling support
- ✅ Streaming responses
- ✅ JSON mode support
- ✅ Standardized error types
- ✅ TypeScript-first design
- ✅ OpenAI provider implementation
- ✅ Anthropic provider implementation

## Installation

```bash
pnpm add @ai-company/llm-providers
```

## Usage

### Using OpenAI Provider

```typescript
import { OpenAIProvider } from '@ai-company/llm-providers';

const provider = new OpenAIProvider(process.env.OPENAI_API_KEY!, 'gpt-4-turbo-preview');

const result = await provider.completion({
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
  temperature: 0.7,
  maxTokens: 1000,
});

console.log(result.content);
```

### Using Anthropic Provider

```typescript
import { AnthropicProvider } from '@ai-company/llm-providers';

const provider = new AnthropicProvider(process.env.ANTHROPIC_API_KEY!, 'claude-3-sonnet-20240229');

const result = await provider.completion({
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
  temperature: 0.7,
  maxTokens: 1000,
});

console.log(result.content);
```

### Using with Tools

```typescript
import { OpenAIProvider } from '@ai-company/llm-providers';

const provider = new OpenAIProvider(process.env.OPENAI_API_KEY!);

const result = await provider.completion({
  messages: [
    { role: 'user', content: 'What is the weather in San Francisco?' }
  ],
  tools: [
    {
      name: 'get_weather',
      description: 'Get the current weather for a location',
      jsonSchema: {
        type: 'object',
        properties: {
          location: { type: 'string' },
        },
        required: ['location'],
      },
    },
  ],
});

if (result.toolCalls) {
  // Handle tool calls
  for (const toolCall of result.toolCalls) {
    console.log(`Tool: ${toolCall.function.name}`);
    console.log(`Args: ${toolCall.function.arguments}`);
  }
}
```

### Streaming

```typescript
import { OpenAIProvider } from '@ai-company/llm-providers';

const provider = new OpenAIProvider(process.env.OPENAI_API_KEY!);

for await (const chunk of provider.streamCompletion({
  messages: [{ role: 'user', content: 'Tell me a story' }],
})) {
  process.stdout.write(chunk.content);
}
```

## API Reference

### LLMProvider Interface

```typescript
interface LLMProvider {
  readonly name: string;
  readonly maxContext: number;
  readonly pricePerMTokIn: number;
  readonly pricePerMTokOut: number;
  readonly capabilities: ProviderCapabilities;
  
  completion(opts: CompletionOptions): Promise<CompletionResult>;
  streamCompletion(opts: CompletionOptions): AsyncIterable<CompletionChunk>;
}
```

### OpenAIProvider

```typescript
class OpenAIProvider implements LLMProvider {
  constructor(
    apiKey: string,
    model?: string,
    options?: {
      baseURL?: string;
      maxContext?: number;
      pricePerMTokIn?: number;
      pricePerMTokOut?: number;
    }
  );
}
```

### AnthropicProvider

```typescript
class AnthropicProvider implements LLMProvider {
  constructor(
    apiKey: string,
    model?: string,
    options?: {
      baseURL?: string;
      maxContext?: number;
      pricePerMTokIn?: number;
      pricePerMTokOut?: number;
    }
  );
}
```

## Error Handling

The package provides standardized error types:

- `LLMProviderError` - Base error class
- `RateLimitError` - Rate limit exceeded (includes `retryAfter`)
- `AuthenticationError` - Authentication failed
- `InvalidRequestError` - Invalid request parameters
- `ModelNotFoundError` - Model not found

```typescript
import { RateLimitError } from '@ai-company/llm-providers';

try {
  const result = await provider.completion({ ... });
} catch (error) {
  if (error instanceof RateLimitError) {
    console.log(`Retry after ${error.retryAfter} seconds`);
  }
}
```

## Related Packages

- `@ai-company/openapi-tools` - OpenAPI tool registry
- `@ai-company/tool-executor` - Tool execution engine
- `@ai-company/moe-router` - MoE routing intelligence

## License

MIT
