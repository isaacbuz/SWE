# OpenAPI Tools & LLM Provider System

A comprehensive system for:

- Defining tools via OpenAPI specifications
- Executing tools safely with schema validation
- Routing requests to optimal LLM providers
- Managing costs, permissions, and rate limits

## Quick Start

```typescript
import { ToolCallingPipeline } from "@ai-company/tool-pipeline";
import { ToolRegistry, ToolExecutor } from "@ai-company/openapi-tools";
import { OpenAIProvider } from "./your-llm-provider";

// Initialize components
const registry = new ToolRegistry();
await registry.loadSpecs(["./tools/openapi/ai-dev-tools.yaml"]);

const executor = new ToolExecutor();
const llmProvider = new OpenAIProvider(process.env.OPENAI_API_KEY);

// Create pipeline
const pipeline = new ToolCallingPipeline(registry, executor, llmProvider);

// Execute tool calling conversation
const result = await pipeline.execute(
  "Create a GitHub issue for this bug",
  "You are a helpful assistant.",
);

console.log(result.finalResponse);
```

## Documentation

- [Getting Started](./getting-started.md) - Setup and first steps
- [Architecture](./architecture.md) - System architecture overview
- [Adding Tools](./adding-tools.md) - How to add new tools
- [Adding Providers](./adding-providers.md) - How to add LLM providers
- [Tutorial: Build Your First Tool](./tutorial-first-tool.md) - Step-by-step guide
- [MoE Routing](./moe-routing.md) - MoE router explained
- [Security](./security.md) - Security guidelines
- [API Reference](./api-reference.md) - Complete API documentation
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions

## Examples

See the [examples](./examples/) directory for working code samples.

## License

MIT
