# Tutorial: Build Your First Tool

This tutorial walks you through creating your first OpenAPI tool from scratch.

## Prerequisites

- Node.js 18+
- Basic TypeScript knowledge
- Understanding of OpenAPI specifications

## Step 1: Define Your Tool

Create a new file `tools/openapi/my-tools.yaml`:

```yaml
openapi: 3.1.0
info:
  title: My Custom Tools
  version: 1.0.0

paths:
  /greet:
    post:
      operationId: greetUser
      summary: Greet a user
      description: |
        Generates a personalized greeting message for a user.
        This is a simple example tool to get started.
      tags: [greeting]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name]
              properties:
                name:
                  type: string
                  description: User's name
                  example: "Alice"
                language:
                  type: string
                  enum: [en, es, fr]
                  default: en
                  description: Greeting language
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  greeting:
                    type: string
                    example: "Hello, Alice!"
```

## Step 2: Load the Tool

```typescript
import { ToolRegistry } from '@ai-company/openapi-tools';

const registry = new ToolRegistry();
await registry.loadSpecs(['./tools/openapi/my-tools.yaml']);

const tool = registry.getToolByName('greetUser');
console.log(tool?.description);
```

## Step 3: Implement the Handler

```typescript
import { ToolExecutor } from '@ai-company/tool-executor';

const executor = new ToolExecutor();

if (tool) {
  executor.registerTool(tool, async (args) => {
    const { name, language = 'en' } = args as {
      name: string;
      language?: string;
    };

    const greetings = {
      en: 'Hello',
      es: 'Hola',
      fr: 'Bonjour',
    };

    return {
      greeting: `${greetings[language as keyof typeof greetings]}, ${name}!`,
    };
  });
}
```

## Step 4: Test the Tool

```typescript
const result = await executor.execute('greetUser', {
  name: 'Alice',
  language: 'en',
});

console.log(result.result);
// { greeting: "Hello, Alice!" }
```

## Step 5: Use with LLM

```typescript
import { ToolCallingPipeline } from '@ai-company/tool-pipeline';
import { OpenAIProvider } from '@ai-company/llm-providers';

const provider = new OpenAIProvider(process.env.OPENAI_API_KEY!);
const pipeline = new ToolCallingPipeline(registry, executor, provider);

const result = await pipeline.executeWithTools(
  'Greet the user named Bob in Spanish',
  ['greetUser']
);

console.log(result.content);
```

## Next Steps

- Add more complex tools
- Integrate with external APIs
- Add error handling
- Write tests
- Document your tools

## Resources

- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
- [JSON Schema](https://json-schema.org/)
- [Adding Tools Guide](./adding-tools.md)

