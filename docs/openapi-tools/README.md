# OpenAPI Tools Documentation

Complete documentation for the OpenAPI tool calling system.

## Table of Contents

- [Architecture Overview](./architecture.md)
- [Adding Tools](./adding-tools.md)
- [Adding Providers](./adding-providers.md)
- [Tutorial: Build Your First Tool](./tutorial-first-tool.md)
- [MoE Routing](./moe-routing.md)
- [Security](./security.md)
- [API Reference](./api-reference.md)
- [Troubleshooting](./troubleshooting.md)

## Quick Start

### 1. Load Tools

```typescript
import { ToolRegistry } from '@ai-company/openapi-tools';

const registry = new ToolRegistry();
await registry.loadSpecs(['./tools/openapi/ai-dev-tools.yaml']);

const tools = registry.getToolSpecs();
```

### 2. Execute Tools

```typescript
import { ToolExecutor } from '@ai-company/tool-executor';

const executor = new ToolExecutor();
executor.registerTool(toolSpec, async (args) => {
  // Execute tool logic
  return { success: true };
});

const result = await executor.execute('createIssue', {
  title: 'New Issue',
  body: 'Description',
});
```

### 3. Use with LLM

```typescript
import { ToolCallingPipeline } from '@ai-company/tool-pipeline';
import { OpenAIProvider } from '@ai-company/llm-providers';

const provider = new OpenAIProvider(apiKey);
const pipeline = new ToolCallingPipeline(registry, executor, provider);

const result = await pipeline.executeWithTools(
  'Create a GitHub issue',
  ['createIssues']
);
```

## Key Concepts

### Tool Registry

The `ToolRegistry` loads and manages OpenAPI tool specifications. It supports:
- Multiple OpenAPI spec files
- Tool discovery by name, tag, or endpoint
- Validation and merging

### Tool Executor

The `ToolExecutor` securely executes tools with:
- JSON Schema validation
- Rate limiting
- Circuit breakers
- Timeout protection
- Retry logic

### Tool Pipeline

The `ToolCallingPipeline` orchestrates multi-turn conversations:
- LLM generates tool calls
- Tools are executed
- Results fed back to LLM
- Process repeats until completion

## Related Documentation

- [MoE Router Documentation](../architecture/MOE_ROUTER.md)
- [Skills System Documentation](../architecture/CLAUDE_SKILLS.md)
- [Frontend Architecture](../architecture/FRONTEND.md)

