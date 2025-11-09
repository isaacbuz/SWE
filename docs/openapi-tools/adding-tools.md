# Adding Tools Guide

## Overview

This guide explains how to add new tools to the OpenAPI Tools system.

## Steps

### 1. Define Tool in OpenAPI Spec

Add your tool to `tools/openapi/ai-dev-tools.yaml`:

```yaml
paths:
  /my-tool/execute:
    post:
      operationId: myTool
      summary: My custom tool
      description: Does something useful
      tags: [custom]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [param1]
              properties:
                param1:
                  type: string
                  description: First parameter
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  result:
                    type: string
```

### 2. Implement Tool Handler

Create a handler function:

```typescript
import { ToolExecutor } from '@ai-company/tool-executor';
import { ToolRegistry } from '@ai-company/openapi-tools';

const registry = new ToolRegistry();
await registry.loadSpecs(['./tools/openapi/ai-dev-tools.yaml']);

const executor = new ToolExecutor();
const toolSpec = registry.getToolByName('myTool');

if (toolSpec) {
  executor.registerTool(toolSpec, async (args) => {
    const { param1 } = args as { param1: string };
    // Implement tool logic
    return { result: `Processed: ${param1}` };
  });
}
```

### 3. Use in Pipeline

```typescript
import { ToolCallingPipeline } from '@ai-company/tool-pipeline';

const pipeline = new ToolCallingPipeline(registry, executor, provider);

const result = await pipeline.executeWithTools(
  'Use myTool with param1="test"',
  ['myTool']
);
```

## Best Practices

1. **Clear Descriptions**: Provide detailed descriptions for LLM context
2. **Schema Validation**: Use strict JSON Schema validation
3. **Error Handling**: Return clear error messages
4. **Security**: Never expose credentials in tool results
5. **Documentation**: Document all parameters and return values

## Testing

```typescript
import { ToolExecutor } from '@ai-company/tool-executor';

const executor = new ToolExecutor();
executor.registerTool(toolSpec, handler);

const result = await executor.execute('myTool', {
  param1: 'test',
});

expect(result.success).toBe(true);
expect(result.result).toBeDefined();
```

