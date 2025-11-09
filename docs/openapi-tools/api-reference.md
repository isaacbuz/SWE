# API Reference

## ToolRegistry

### Methods

#### `loadSpecs(paths: string[]): Promise<void>`

Load one or more OpenAPI specification files.

```typescript
await registry.loadSpecs([
  './tools/openapi/ai-dev-tools.yaml',
  './tools/openapi/custom-tools.yaml',
]);
```

#### `getToolSpecs(): ToolSpec[]`

Get all registered tools.

```typescript
const tools = registry.getToolSpecs();
```

#### `getToolByName(name: string): ToolSpec | undefined`

Get a tool by operationId.

```typescript
const tool = registry.getToolByName('createIssue');
```

#### `getToolsByTag(tag: string): ToolSpec[]`

Get tools by tag.

```typescript
const githubTools = registry.getToolsByTag('github');
```

## ToolExecutor

### Methods

#### `registerTool(toolSpec: ToolSpec, handler: ToolHandler): void`

Register a tool handler.

```typescript
executor.registerTool(toolSpec, async (args) => {
  // Tool logic
  return { result: 'success' };
});
```

#### `execute(toolName: string, args: unknown, options?: ToolExecutionOptions): Promise<ToolResult>`

Execute a tool.

```typescript
const result = await executor.execute('createIssue', {
  title: 'Bug',
  body: 'Description',
});
```

## ToolCallingPipeline

### Methods

#### `executeWithTools(prompt: string, availableTools: string[], options?: PipelineOptions): Promise<PipelineResult>`

Execute pipeline with tools.

```typescript
const result = await pipeline.executeWithTools(
  'Create a GitHub issue',
  ['createIssues'],
  { maxTurns: 5 }
);
```

## MoERouter

### Methods

#### `registerProvider(provider: LLMProvider): void`

Register an LLM provider.

```typescript
router.registerProvider(new OpenAIProvider(apiKey));
```

#### `selectProvider(request: RoutingRequest): RoutingDecision`

Select provider for a request.

```typescript
const decision = router.selectProvider({
  taskType: TaskType.CODE_GENERATION,
  qualityRequirement: 0.8,
});
```

## Types

### ToolSpec

```typescript
interface ToolSpec {
  name: string;
  description: string;
  jsonSchema: object;
  operationId: string;
  endpoint?: string;
  method?: string;
  tags?: string[];
}
```

### ToolResult

```typescript
interface ToolResult {
  toolName: string;
  result: unknown;
  durationMs: number;
  success: boolean;
  error?: string;
  validationErrors?: string[];
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

