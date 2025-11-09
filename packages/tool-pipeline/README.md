# @ai-company/tool-pipeline

End-to-end tool calling pipeline for LLM providers.

## Overview

This package provides a complete pipeline for orchestrating multi-turn conversations between LLMs and tools. It handles tool discovery, execution, and result feeding back to the LLM until a final answer is reached.

## Features

- ✅ Multi-turn tool calling conversations
- ✅ Parallel tool execution when safe
- ✅ Automatic tool result formatting
- ✅ Cost tracking
- ✅ Timeout protection
- ✅ Loop detection (max turns)

## Installation

```bash
pnpm add @ai-company/tool-pipeline
```

## Usage

### Basic Example

```typescript
import { ToolCallingPipeline } from '@ai-company/tool-pipeline';
import { ToolRegistry } from '@ai-company/openapi-tools';
import { ToolExecutor } from '@ai-company/tool-executor';
import { OpenAIProvider } from '@ai-company/llm-providers';

// Initialize components
const registry = new ToolRegistry();
await registry.loadSpecs(['./tools/openapi/ai-dev-tools.yaml']);

const executor = new ToolExecutor();
// Register tool handlers...

const provider = new OpenAIProvider(process.env.OPENAI_API_KEY!);

// Create pipeline
const pipeline = new ToolCallingPipeline(registry, executor, provider);

// Execute with tools
const result = await pipeline.executeWithTools(
  'Create a GitHub issue titled "Fix bug" in the isaacbuz/SWE repo',
  ['createIssues'], // Available tools
  {
    maxTurns: 5,
    parallelExecution: true,
  }
);

console.log(result.content);
console.log(`Completed in ${result.turns} turns`);
console.log(`Cost: $${result.cost?.toFixed(4)}`);
```

### Advanced Example

```typescript
import { ToolCallingPipeline } from '@ai-company/tool-pipeline';

const pipeline = new ToolCallingPipeline(registry, executor, provider);

const result = await pipeline.executeWithTools(
  'Analyze the code in src/main.ts and create a PR with improvements',
  ['analyzeCode', 'createPR'],
  {
    maxTurns: 10,
    parallelExecution: true,
    timeoutMs: 60000,
    includeToolResults: true,
  }
);

// Access execution results
if (result.executionResults) {
  for (const execResult of result.executionResults) {
    console.log(`${execResult.toolName}: ${execResult.success ? 'success' : 'failed'}`);
  }
}
```

## API Reference

### ToolCallingPipeline

```typescript
class ToolCallingPipeline {
  constructor(
    toolRegistry: ToolRegistry,
    toolExecutor: ToolExecutor,
    provider: LLMProvider
  );

  executeWithTools(
    prompt: string,
    availableTools: string[],
    options?: PipelineOptions
  ): Promise<PipelineResult>;
}
```

### PipelineOptions

```typescript
interface PipelineOptions {
  maxTurns?: number;           // Default: 5
  parallelExecution?: boolean;  // Default: true
  timeoutMs?: number;          // Default: 30000
  includeToolResults?: boolean; // Default: true
}
```

### PipelineResult

```typescript
interface PipelineResult {
  content: string;
  turns: number;
  toolCalls?: ToolCall[];
  cost?: number;
  executionResults?: ToolResult[];
}
```

## How It Works

1. **Initial Request**: User provides prompt and available tools
2. **LLM Call**: Pipeline calls LLM with tools available
3. **Tool Execution**: If LLM requests tools, they're executed (possibly in parallel)
4. **Result Feeding**: Tool results are fed back to LLM as tool messages
5. **Repeat**: Process repeats until LLM provides final answer (no tool calls)
6. **Return**: Final answer and execution details are returned

## Safety Features

- **Max Turns**: Prevents infinite loops (default: 5 turns)
- **Timeout**: Each turn has a timeout (default: 30 seconds)
- **Error Handling**: Tool execution errors are passed to LLM for correction
- **Validation**: Tool inputs are validated before execution

## Related Packages

- `@ai-company/llm-providers` - LLM provider implementations
- `@ai-company/openapi-tools` - OpenAPI tool registry
- `@ai-company/tool-executor` - Tool execution engine

## License

MIT

