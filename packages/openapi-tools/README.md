# @ai-company/openapi-tools

OpenAPI tool registry and schema management for LLM tool calling.

## Overview

This package provides a unified registry for managing OpenAPI tool specifications that can be used by LLM providers (OpenAI, Anthropic, etc.) for function/tool calling.

## Features

- ✅ Load and parse OpenAPI 3.0 and 3.1 specifications
- ✅ Extract tool definitions from OpenAPI operations
- ✅ Merge multiple OpenAPI specs into unified registry
- ✅ Validate OpenAPI specs on load
- ✅ Query tools by name, tag, or endpoint
- ✅ Convert OpenAPI schemas to JSON Schema format

## Installation

```bash
pnpm add @ai-company/openapi-tools
```

## Usage

### Basic Example

```typescript
import { ToolRegistry } from '@ai-company/openapi-tools';

// Create registry
const registry = new ToolRegistry();

// Load OpenAPI specs
await registry.loadSpecs([
  './tools/openapi/ai-dev-tools.yaml',
  './tools/openapi/github-api.yaml',
]);

// Get all tools
const allTools = registry.getToolSpecs();

// Get specific tool
const createIssueTool = registry.getToolByName('createIssues');

// Get tools by tag
const githubTools = registry.getToolsByTag('github');
```

### Advanced Configuration

```typescript
import { ToolRegistry } from '@ai-company/openapi-tools';

const registry = new ToolRegistry({
  validateOnLoad: true,        // Validate OpenAPI specs
  allowDuplicates: false,      // Throw error on duplicate operationIds
  operationIdResolver: (method, path) => {
    // Custom operationId generation
    return `${method.toLowerCase()}_${path.replace(/\//g, '_')}`;
  },
});
```

## API Reference

### ToolRegistry

Main class for managing tool specifications.

#### Methods

- `loadSpecs(paths: string[]): Promise<void>` - Load one or more OpenAPI specs
- `getToolSpecs(): ToolSpec[]` - Get all registered tools
- `getToolByName(name: string): ToolSpec | undefined` - Get tool by operationId
- `getToolsByTag(tag: string): ToolSpec[]` - Get tools by tag
- `getToolsByEndpointPrefix(prefix: string): ToolSpec[]` - Get tools by endpoint prefix
- `hasTool(name: string): boolean` - Check if tool exists
- `getToolCount(): number` - Get total tool count
- `getLoadedSpecs(): LoadedSpec[]` - Get metadata about loaded specs
- `clear(): void` - Clear all tools
- `removeTool(name: string): boolean` - Remove specific tool

### ToolSpec

Interface representing a tool specification.

```typescript
interface ToolSpec {
  name: string;              // operationId
  description: string;       // Tool description
  jsonSchema: object;        // JSON Schema for parameters
  operationId: string;       // Original operationId
  endpoint?: string;          // HTTP endpoint path
  method?: string;           // HTTP method
  tags?: string[];           // Tags/categories
  metadata?: object;         // Additional metadata
}
```

## OpenAPI Requirements

For an operation to be converted to a ToolSpec:

1. **operationId is required** (or provide `operationIdResolver`)
2. **description or summary** recommended for LLM context
3. **requestBody or parameters** for parameter schema

### Example OpenAPI Operation

```yaml
paths:
  /github/create-issues:
    post:
      operationId: createIssues
      summary: Create multiple GitHub issues
      description: Creates one or more GitHub issues from a specification
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [owner, repo, tasks]
              properties:
                owner:
                  type: string
                  description: GitHub repository owner
                repo:
                  type: string
                  description: Repository name
                tasks:
                  type: array
                  items:
                    type: object
                    required: [title, body]
                    properties:
                      title: { type: string }
                      body: { type: string }
      tags: [github]
```

## Error Handling

The registry will throw errors for:

- Invalid OpenAPI specifications (if `validateOnLoad: true`)
- Duplicate operationIds (if `allowDuplicates: false`)
- Missing operationId (if no `operationIdResolver` provided)

## Testing

```bash
# Run tests
pnpm test

# Run with coverage
pnpm test:coverage
```

## Related Packages

- `@ai-company/llm-providers` - LLM provider implementations
- `@ai-company/tool-executor` - Tool execution engine
- `@ai-company/moe-router` - MoE routing intelligence

## License

MIT

