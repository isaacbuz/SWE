# OpenAPI Tools

OpenAPI Tool Registry and Converter for LLM Function Calling

## Overview

This package provides utilities for loading OpenAPI specifications and converting them to tool specifications compatible with LLM function calling (OpenAI, Anthropic, etc.).

## Features

- ✅ Load OpenAPI 3.0 and 3.1 specifications
- ✅ Convert operations to tool specifications
- ✅ Tool registry with discovery and lookup
- ✅ Support for multiple spec merging
- ✅ TypeScript types for all interfaces
- ✅ Schema conversion from OpenAPI to JSON Schema

## Installation

```bash
pnpm add @ai-company/openapi-tools
```

## Usage

### Basic Usage

```typescript
import { ToolRegistry } from "@ai-company/openapi-tools";

const registry = new ToolRegistry();

// Load OpenAPI spec
await registry.loadSpecs([
  {
    openapi: "3.1.0",
    info: { title: "My API", version: "1.0.0" },
    paths: {
      "/users": {
        get: {
          operationId: "listUsers",
          summary: "List all users",
          parameters: [
            {
              name: "limit",
              in: "query",
              schema: { type: "integer" },
            },
          ],
        },
      },
    },
  },
]);

// Get all tools
const tools = registry.getToolSpecs();

// Get specific tool
const tool = registry.getToolByName("listUsers");
```

### Loading from Files

```typescript
await registry.loadSpecs([
  "./api/openapi.yaml",
  "./external/github-api.yaml",
]);
```

### Converting to LLM Format

```typescript
import { openApiToToolSpecs } from "@ai-company/openapi-tools";

const tools = openApiToToolSpecs(openApiSpec);

// Convert to OpenAI format
const openAITools = tools.map((tool) => ({
  type: "function",
  function: {
    name: tool.name,
    description: tool.description,
    parameters: tool.jsonSchema,
  },
}));
```

## API Reference

### `ToolRegistry`

Main registry class for managing tools.

#### Methods

- `loadSpecs(specs)` - Load OpenAPI specifications
- `getToolSpecs()` - Get all registered tools
- `getToolByName(name)` - Get tool by name
- `getToolsByCategory(category)` - Get tools by category
- `hasTool(name)` - Check if tool exists
- `clear()` - Clear all tools

### `openApiToToolSpecs(spec, converter?)`

Convert OpenAPI spec to tool specifications.

## License

MIT

