# OpenAPI Tool Registry

Infrastructure for managing OpenAPI tool specifications and converting them to LLM-compatible tool formats.

## Overview

The OpenAPI Tool Registry provides a unified system for:
- Loading and managing OpenAPI 3.0/3.1 specifications
- Converting OpenAPI operations to LLM tool specifications
- Registering and discovering tools by name, tag, or category
- Type-safe tool definitions with JSON Schema validation

## Features

- ✅ OpenAPI 3.0 and 3.1 support
- ✅ Automatic tool extraction from OpenAPI specs
- ✅ JSON Schema validation
- ✅ Tag-based tool organization
- ✅ TypeScript type definitions
- ✅ Comprehensive test coverage

## Installation

```bash
pnpm add @ai-company/openapi-tools
```

## Quick Start

```typescript
import { ToolRegistry } from '@ai-company/openapi-tools';

// Create registry
const registry = new ToolRegistry();

// Load OpenAPI specs
await registry.loadSpecs([
  './tools/openapi/ai-dev-tools.yaml',
  './tools/openapi/github-api.yaml'
]);

// Get all tools
const tools = registry.getToolSpecs();
console.log(`Loaded ${tools.length} tools`);

// Get specific tool
const createUserTool = registry.getToolByName('createUser');
console.log(createUserTool?.description);

// Get tools by tag
const githubTools = registry.getToolsByTag('github');
```

## API Reference

### ToolRegistry

Main class for managing tool specifications.

#### Methods

- `loadSpecs(paths: string[], validate?: boolean): Promise<void>` - Load OpenAPI specs from file paths
- `getToolSpecs(): ToolSpec[]` - Get all registered tools
- `getToolByName(name: string): ToolSpec | undefined` - Get tool by operationId
- `hasTool(name: string): boolean` - Check if tool exists
- `getToolsByTag(tag: string): ToolSpec[]` - Get tools by tag
- `getAllTags(): string[]` - Get all unique tags
- `getStats()` - Get registry statistics

### ToolSpec

Tool specification interface:

```typescript
interface ToolSpec {
  name: string;              // operationId
  description: string;        // Operation description
  jsonSchema: object;         // JSON Schema for parameters
  operationId: string;        // OpenAPI operationId
  endpoint?: string;          // HTTP path
  method?: string;            // HTTP method
  tags?: string[];            // OpenAPI tags
  requiresAuth?: boolean;     // Security requirements
  rateLimit?: number;         // Rate limit per minute
}
```

## Tool Spec Conversion

The package includes converters to transform ToolSpec objects into provider-specific formats:

```typescript
import { ToolRegistry, convertToolSpec, toOpenAIFormat } from '@ai-company/openapi-tools';

const registry = new ToolRegistry();
await registry.loadSpecs(['./tools.yaml']);

const tool = registry.getToolByName('createUser');

// Convert to OpenAI format
const openAITool = toOpenAIFormat(tool!);
// Result: { type: 'function', function: { name, description, parameters } }

// Convert to Anthropic format
const anthropicTool = convertToolSpec(tool!, 'anthropic');
// Result: { name, description, input_schema: { type: 'object', properties, required } }

// Convert to Google format
const googleTool = convertToolSpec(tool!, 'google');
// Result: { name, description, parameters: { type: 'object', properties, required } }
```

### Supported Providers

- **OpenAI**: `{ type: 'function', function: { name, description, parameters } }`
- **Anthropic**: `{ name, description, input_schema: { type, properties, required } }`
- **Google**: `{ name, description, parameters: { type, properties, required } }`
- **Generic**: `{ name, description, parameters }`

## Usage Examples

### Loading Multiple Specs

```typescript
const registry = new ToolRegistry();

await registry.loadSpecs([
  './specs/internal-tools.yaml',
  './specs/external-apis.yaml'
]);

const stats = registry.getStats();
console.log(`Loaded ${stats.totalTools} tools from ${stats.specPaths} specs`);
```

### Finding Tools

```typescript
// By name
const tool = registry.getToolByName('createIssue');

// By tag
const githubTools = registry.getToolsByTag('github');

// All tags
const allTags = registry.getAllTags();
```

### Converting to LLM Format

```typescript
const tool = registry.getToolByName('createUser');

// Convert to OpenAI function format
const openAITool = {
  type: 'function',
  function: {
    name: tool.name,
    description: tool.description,
    parameters: tool.jsonSchema
  }
};

// Convert to Anthropic tool format
const anthropicTool = {
  name: tool.name,
  description: tool.description,
  input_schema: tool.jsonSchema
};
```

## OpenAPI Spec Requirements

Your OpenAPI specs must:

1. Be version 3.0 or 3.1
2. Include `operationId` for each operation
3. Define request schemas (parameters or requestBody)
4. Include descriptions for better LLM understanding

Example:

```yaml
openapi: 3.1.0
paths:
  /users:
    post:
      operationId: createUser
      summary: Create a new user
      description: Creates a new user account with email and password
      tags:
        - users
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  minLength: 8
              required:
                - email
                - password
```

## Testing

```bash
pnpm test
```

## Related Issues

- Issue #7: OpenAPI Tool Registry Foundation ✅
- Issue #8: OpenAPI to Tool Spec Converter (in progress)
- Issue #9: Tool Executor with Schema Validation (pending)

## License

MIT

