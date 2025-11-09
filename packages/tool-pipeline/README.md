# Tool Calling Pipeline

Orchestrates multi-turn tool calling between LLM providers and OpenAPI tools.

## Features

- ✅ Multi-turn tool calling loops
- ✅ Tool discovery from OpenAPI registry
- ✅ Tool spec conversion to provider formats
- ✅ Parallel tool execution
- ✅ Result validation and integration
- ✅ Configurable turn limits and timeouts
- ✅ Error handling and retries

## Installation

```bash
pnpm add @ai-company/tool-pipeline
```

## Usage

```typescript
import { ToolCallingPipeline } from "@ai-company/tool-pipeline";
import { ToolRegistry, ToolExecutor } from "@ai-company/openapi-tools";
import { LLMProvider } from "./your-llm-provider";

// Initialize components
const registry = new ToolRegistry();
await registry.loadSpecs(["./tools/openapi/ai-dev-tools.yaml"]);

const executor = new ToolExecutor();
const llmProvider = new YourLLMProvider();

// Create pipeline
const pipeline = new ToolCallingPipeline(registry, executor, llmProvider, {
  maxTurns: 10,
  timeoutPerTurn: 30000,
});

// Register tool handlers
pipeline.registerToolHandler("createIssues", async (args) => {
  // Your implementation
  return { success: true, issues: [] };
});

// Execute tool calling conversation
const result = await pipeline.execute(
  "Create 3 GitHub issues for the openapi-tools project",
  "You are a helpful assistant that can create GitHub issues.",
);

console.log(result.finalResponse);
console.log(
  `Executed ${result.toolResults.length} tools in ${result.turns} turns`,
);
```

## Architecture

```
User Message
    ↓
LLM Provider (with tools)
    ↓
Tool Calls Detected
    ↓
Tool Executor (validates & executes)
    ↓
Tool Results
    ↓
LLM Provider (with results)
    ↓
Final Response
```

## License

MIT
