# Adding New Tools

This guide explains how to add new tools to the OpenAPI Tools system.

## Step 1: Define OpenAPI Specification

Create or extend an OpenAPI spec in `tools/openapi/`:

```yaml
openapi: 3.1.0
info:
  title: My Service Tools
  version: 1.0.0
paths:
  /my-service/my-tool:
    post:
      operationId: myTool
      summary: Does something useful
      description: Detailed description of what this tool does
      tags:
        - my-service
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
                  minLength: 1
                  maxLength: 100
                param2:
                  type: integer
                  description: Second parameter
                  minimum: 0
                  maximum: 100
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  result:
                    type: string
```

## Step 2: Implement Tool Handler

Create a handler function:

```typescript
import type { ToolHandler } from "@ai-company/openapi-tools";

export const myToolHandler: ToolHandler = async (args) => {
  // Args are already validated against schema
  const { param1, param2 } = args as {
    param1: string;
    param2?: number;
  };

  // Your implementation
  const result = await doSomething(param1, param2);

  // Return result (will be validated against output schema if defined)
  return {
    success: true,
    result: result,
  };
};
```

## Step 3: Register Tool

```typescript
import { ToolExecutor } from "@ai-company/openapi-tools";
import { myToolHandler } from "./handlers/myTool";

const executor = new ToolExecutor();

// Get tool spec from registry
const toolSpec = registry.getToolByName("myTool");

// Register handler
executor.registerTool("myTool", myToolHandler, toolSpec);
```

## Step 4: Test Tool

```typescript
// Test execution
const result = await executor.execute(
  "myTool",
  { param1: "test", param2: 42 },
  toolSpec
);

console.log(result.success); // true
console.log(result.result); // { success: true, result: "..." }
```

## Best Practices

### 1. Input Validation
- Define strict schemas in OpenAPI spec
- ToolExecutor validates automatically
- Don't trust inputs - validate again if needed

### 2. Error Handling
- Return structured errors
- Include error codes and messages
- Log errors for debugging

### 3. Security
- Never expose credentials
- Sanitize all inputs
- Check permissions before execution

### 4. Performance
- Use caching where appropriate
- Implement timeouts
- Handle rate limits gracefully

## Example: Complete Tool

See [examples/custom-tool.ts](../examples/custom-tool.ts) for a complete example.

