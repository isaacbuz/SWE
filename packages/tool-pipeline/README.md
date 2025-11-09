# Tool Calling Pipeline

End-to-end tool calling orchestration between LLM providers and OpenAPI-defined tools.

## Overview

The Tool Calling Pipeline connects LLM providers with tools defined in OpenAPI specifications, enabling multi-turn tool calling where the LLM can discover, call, and receive results from tools in a conversational loop.

## Features

- **Multi-turn Tool Calling**: Supports tool → LLM → tool loops
- **Provider Agnostic**: Works with any LLM provider implementing the interface
- **OpenAPI Integration**: Automatically loads tools from OpenAPI specs
- **Validation**: Uses ToolExecutor for schema validation and security
- **Logging**: Comprehensive logging of tool calls and results
- **Error Handling**: Graceful error handling with retries

## Installation

```bash
pnpm add @ai-company/tool-pipeline
```

## Usage

```typescript
import { ToolRegistry, ToolExecutor } from '@ai-company/openapi-tools';
import { ToolCallingPipeline } from '@ai-company/tool-pipeline';

// Initialize components
const registry = new ToolRegistry({
  specPaths: ['tools/openapi/ai-dev-tools.yaml']
});
await registry.loadSpecs(['tools/openapi/ai-dev-tools.yaml']);

const executor = new ToolExecutor({
  enableRateLimit: true,
  enableSanitization: true,
});

// Register tool handlers
executor.register('createIssue', async (args) => {
  // Your implementation
  return { issueNumber: 123 };
});

// Create LLM provider adapter
const provider: LLMProvider = {
  async complete(messages, tools, options) {
    // Call your LLM provider
    // Return { content, toolCalls, usage, model }
  }
};

// Create pipeline
const pipeline = new ToolCallingPipeline(
  registry,
  executor,
  provider,
  {
    maxTurns: 5,
    verbose: true
  }
);

// Execute with tools
const result = await pipeline.executeWithTools(
  "Create an issue for fixing the authentication bug",
  ['createIssue', 'listIssues'], // Available tools
  "You are a helpful assistant that can create GitHub issues."
);

console.log(result.content);
console.log(result.toolCalls);
```

## Architecture

```
┌─────────────┐
│   LLM       │
│  Provider   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Tool Calling    │
│    Pipeline     │
└──────┬──────────┘
       │
       ▼
┌─────────────┐    ┌──────────────┐
│   Tool      │───▶│   Tool       │
│  Registry   │    │  Executor    │
└─────────────┘    └──────┬───────┘
                          │
                          ▼
                    ┌─────────────┐
                    │   Tools      │
                    │ (GitHub API) │
                    └─────────────┘
```

## API Reference

### ToolCallingPipeline

Main pipeline class for orchestrating tool calls.

#### Constructor

```typescript
new ToolCallingPipeline(
  registry: ToolRegistry,
  executor: ToolExecutor,
  provider: LLMProvider,
  options?: PipelineOptions
)
```

#### Methods

**executeWithTools**
```typescript
executeWithTools(
  prompt: string,
  availableToolNames?: string[],
  systemPrompt?: string
): Promise<PipelineResult>
```

Executes a prompt with tool calling support, handling multi-turn conversations.

## Examples

See `examples/` directory for complete examples.

## License

MIT

