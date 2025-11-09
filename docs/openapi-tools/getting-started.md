# Getting Started with OpenAPI Tools

This guide will help you get started with the OpenAPI Tools system.

## Installation

```bash
# Install packages
pnpm add @ai-company/openapi-tools
pnpm add @ai-company/tool-pipeline
pnpm add @ai-company/external-api-tools
```

## Basic Setup

### 1. Create an OpenAPI Specification

Create a file `tools/openapi/my-tools.yaml`:

```yaml
openapi: 3.1.0
info:
  title: My Tools API
  version: 1.0.0
paths:
  /my-service/do-something:
    post:
      operationId: doSomething
      summary: Does something useful
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [input]
              properties:
                input: { type: string }
```

### 2. Load Tools

```typescript
import { ToolRegistry } from "@ai-company/openapi-tools";

const registry = new ToolRegistry();
await registry.loadSpecs(["./tools/openapi/my-tools.yaml"]);

// Get all tools
const tools = registry.getToolSpecs();
console.log(`Loaded ${tools.length} tools`);
```

### 3. Register Tool Handlers

```typescript
import { ToolExecutor } from "@ai-company/openapi-tools";

const executor = new ToolExecutor();

executor.registerTool("doSomething", async (args) => {
  // Your implementation
  return { result: `Processed: ${args.input}` };
});
```

### 4. Execute Tools

```typescript
const result = await executor.execute(
  "doSomething",
  { input: "Hello" },
  registry.getToolByName("doSomething"),
);

console.log(result.result); // { result: "Processed: Hello" }
```

## Using with LLM Providers

### Complete Example

```typescript
import { ToolCallingPipeline } from "@ai-company/tool-pipeline";
import { ToolRegistry, ToolExecutor } from "@ai-company/openapi-tools";

// Setup
const registry = new ToolRegistry();
await registry.loadSpecs(["./tools/openapi/ai-dev-tools.yaml"]);

const executor = new ToolExecutor();
executor.registerTool("createIssues", async (args) => {
  // Your GitHub API implementation
  return { success: true, issues: [] };
});

// Create LLM provider (implement LLMProvider interface)
const llmProvider = {
  name: "openai:gpt-4",
  async complete(messages, tools, systemPrompt) {
    // Call OpenAI API
    // Return { content: string, toolCalls?: ToolCall[] }
  },
};

// Create pipeline
const pipeline = new ToolCallingPipeline(registry, executor, llmProvider);

// Execute
const result = await pipeline.execute(
  "Create 3 GitHub issues for the openapi-tools project",
  "You are a helpful assistant.",
);

console.log(result.finalResponse);
console.log(`Executed ${result.toolResults.length} tools`);
```

## Next Steps

- Read [Adding Tools](./adding-tools.md) to learn how to add new tools
- Check [Architecture](./architecture.md) to understand the system design
- See [Examples](./examples/) for more code samples
