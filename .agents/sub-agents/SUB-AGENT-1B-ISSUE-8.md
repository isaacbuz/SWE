# 🤖 Sub-Agent 1B: Spec Converter Specialist

**Agent ID**: SUB-1B  
**Issue**: #8 - Convert OpenAPI Specs to LLM Tool Schemas  
**Epic**: #1 - OpenAPI Tooling Infrastructure  
**Status**: ✅ COMPLETE  
**Dependencies**: Issue #7 (Tool Registry)

---

## MISSION BRIEFING

Convert OpenAPI operation definitions into JSON Schema format compatible with LLM function calling (OpenAI, Anthropic formats).

---

## IMPLEMENTATION

### Package Structure
Extends `packages/openapi-tools/` from Issue #7

```
packages/openapi-tools/
├── src/
│   ├── converter/
│   │   ├── index.ts
│   │   ├── openai-converter.ts
│   │   ├── anthropic-converter.ts
│   │   └── json-schema.ts
│   └── __tests__/
│       └── converter.test.ts
```

### src/converter/index.ts
```typescript
export { convertToOpenAITools } from './openai-converter';
export { convertToAnthropicTools } from './anthropic-converter';
export { convertParametersToJSONSchema } from './json-schema';
```

### src/converter/json-schema.ts
```typescript
import { OpenAPIV3, OpenAPIV3_1 } from 'openapi-types';

export interface JSONSchema {
  type: string;
  properties?: Record<string, any>;
  required?: string[];
  items?: JSONSchema;
  description?: string;
  enum?: any[];
  default?: any;
  additionalProperties?: boolean | JSONSchema;
}

/**
 * Convert OpenAPI parameter to JSON Schema
 */
export function convertParameterToJSONSchema(
  param: OpenAPIV3.ParameterObject
): JSONSchema {
  const schema: JSONSchema = {
    type: 'string', // default
    description: param.description,
  };

  if (param.schema) {
    Object.assign(schema, param.schema);
  }

  if (param.required) {
    // Mark as required in parent schema
  }

  return schema;
}

/**
 * Convert OpenAPI parameters array to JSON Schema
 */
export function convertParametersToJSONSchema(
  parameters: OpenAPIV3.ParameterObject[]
): JSONSchema {
  const properties: Record<string, JSONSchema> = {};
  const required: string[] = [];

  for (const param of parameters) {
    const paramSchema = convertParameterToJSONSchema(param);
    properties[param.name] = paramSchema;

    if (param.required) {
      required.push(param.name);
    }
  }

  return {
    type: 'object',
    properties,
    required: required.length > 0 ? required : undefined,
    additionalProperties: false,
  };
}

/**
 * Convert OpenAPI request body to JSON Schema
 */
export function convertRequestBodyToJSONSchema(
  requestBody: OpenAPIV3.RequestBodyObject
): JSONSchema | undefined {
  const content = requestBody.content?.['application/json'];
  if (!content?.schema) return undefined;

  return content.schema as JSONSchema;
}

/**
 * Merge parameter and request body schemas
 */
export function mergeSchemas(
  paramSchema?: JSONSchema,
  bodySchema?: JSONSchema
): JSONSchema {
  if (!paramSchema && !bodySchema) {
    return { type: 'object', properties: {} };
  }

  if (!paramSchema) return bodySchema!;
  if (!bodySchema) return paramSchema;

  // Merge properties
  const merged: JSONSchema = {
    type: 'object',
    properties: {
      ...paramSchema.properties,
      ...bodySchema.properties,
    },
    required: [
      ...(paramSchema.required || []),
      ...(bodySchema.required || []),
    ],
  };

  return merged;
}

/**
 * Simplify schema for LLM compatibility
 * Remove advanced JSON Schema features that LLMs don't support
 */
export function simplifySchema(schema: JSONSchema): JSONSchema {
  const simplified = { ...schema };

  // Remove unsupported features
  delete (simplified as any).allOf;
  delete (simplified as any).anyOf;
  delete (simplified as any).oneOf;
  delete (simplified as any).not;

  // Recursively simplify nested schemas
  if (simplified.properties) {
    simplified.properties = Object.fromEntries(
      Object.entries(simplified.properties).map(([key, value]) => [
        key,
        typeof value === 'object' ? simplifySchema(value) : value,
      ])
    );
  }

  if (simplified.items && typeof simplified.items === 'object') {
    simplified.items = simplifySchema(simplified.items);
  }

  return simplified;
}
```

### src/converter/openai-converter.ts
```typescript
import { ToolSpec } from '../types';
import {
  convertParametersToJSONSchema,
  convertRequestBodyToJSONSchema,
  mergeSchemas,
  simplifySchema,
  JSONSchema,
} from './json-schema';

/**
 * OpenAI function calling format
 */
export interface OpenAIFunction {
  name: string;
  description: string;
  parameters: JSONSchema;
}

export interface OpenAITool {
  type: 'function';
  function: OpenAIFunction;
}

/**
 * Convert ToolSpec to OpenAI function format
 */
export function convertToOpenAIFunction(tool: ToolSpec): OpenAIFunction {
  // Convert parameters
  const paramSchema = tool.parameters.length > 0
    ? convertParametersToJSONSchema(tool.parameters as any)
    : undefined;

  // Convert request body
  const bodySchema = tool.requestBody
    ? convertRequestBodyToJSONSchema(tool.requestBody as any)
    : undefined;

  // Merge and simplify
  const parameters = simplifySchema(mergeSchemas(paramSchema, bodySchema));

  return {
    name: tool.name,
    description: tool.description,
    parameters,
  };
}

/**
 * Convert ToolSpec to OpenAI tool format
 */
export function convertToOpenAITool(tool: ToolSpec): OpenAITool {
  return {
    type: 'function',
    function: convertToOpenAIFunction(tool),
  };
}

/**
 * Convert multiple ToolSpecs to OpenAI tools
 */
export function convertToOpenAITools(tools: ToolSpec[]): OpenAITool[] {
  return tools.map(convertToOpenAITool);
}

/**
 * Validate OpenAI function schema
 */
export function validateOpenAIFunction(func: OpenAIFunction): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!func.name || func.name.length === 0) {
    errors.push('Function name is required');
  }

  if (!func.description || func.description.length === 0) {
    errors.push('Function description is required');
  }

  if (!func.parameters || typeof func.parameters !== 'object') {
    errors.push('Parameters must be a JSON Schema object');
  }

  // OpenAI requires parameters to be an object type
  if (func.parameters?.type !== 'object') {
    errors.push('Parameters type must be "object"');
  }

  // Name must match regex
  const nameRegex = /^[a-zA-Z0-9_-]{1,64}$/;
  if (func.name && !nameRegex.test(func.name)) {
    errors.push(
      'Function name must be 1-64 characters, alphanumeric with underscores/hyphens'
    );
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
```

### src/converter/anthropic-converter.ts
```typescript
import { ToolSpec } from '../types';
import {
  convertParametersToJSONSchema,
  convertRequestBodyToJSONSchema,
  mergeSchemas,
  simplifySchema,
  JSONSchema,
} from './json-schema';

/**
 * Anthropic tool format (Claude 3+)
 */
export interface AnthropicInputSchema extends JSONSchema {
  type: 'object';
  properties: Record<string, JSONSchema>;
  required?: string[];
}

export interface AnthropicTool {
  name: string;
  description: string;
  input_schema: AnthropicInputSchema;
}

/**
 * Convert ToolSpec to Anthropic tool format
 */
export function convertToAnthropicTool(tool: ToolSpec): AnthropicTool {
  // Convert parameters
  const paramSchema = tool.parameters.length > 0
    ? convertParametersToJSONSchema(tool.parameters as any)
    : undefined;

  // Convert request body
  const bodySchema = tool.requestBody
    ? convertRequestBodyToJSONSchema(tool.requestBody as any)
    : undefined;

  // Merge and simplify
  const inputSchema = simplifySchema(mergeSchemas(paramSchema, bodySchema));

  // Ensure it's an object type with properties
  if (inputSchema.type !== 'object' || !inputSchema.properties) {
    inputSchema.type = 'object';
    inputSchema.properties = {};
  }

  return {
    name: tool.name,
    description: tool.description,
    input_schema: inputSchema as AnthropicInputSchema,
  };
}

/**
 * Convert multiple ToolSpecs to Anthropic tools
 */
export function convertToAnthropicTools(tools: ToolSpec[]): AnthropicTool[] {
  return tools.map(convertToAnthropicTool);
}

/**
 * Validate Anthropic tool schema
 */
export function validateAnthropicTool(tool: AnthropicTool): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!tool.name || tool.name.length === 0) {
    errors.push('Tool name is required');
  }

  if (!tool.description || tool.description.length === 0) {
    errors.push('Tool description is required');
  }

  if (!tool.input_schema || typeof tool.input_schema !== 'object') {
    errors.push('input_schema must be a JSON Schema object');
  }

  // Anthropic requires input_schema to be object type
  if (tool.input_schema?.type !== 'object') {
    errors.push('input_schema type must be "object"');
  }

  if (!tool.input_schema?.properties) {
    errors.push('input_schema must have properties field');
  }

  // Name constraints (similar to OpenAI)
  const nameRegex = /^[a-zA-Z0-9_-]{1,64}$/;
  if (tool.name && !nameRegex.test(tool.name)) {
    errors.push(
      'Tool name must be 1-64 characters, alphanumeric with underscores/hyphens'
    );
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
```

### src/__tests__/converter.test.ts
```typescript
import { describe, it, expect } from 'vitest';
import { ToolSpec } from '../types';
import {
  convertToOpenAITool,
  convertToOpenAITools,
  validateOpenAIFunction,
} from '../converter/openai-converter';
import {
  convertToAnthropicTool,
  convertToAnthropicTools,
  validateAnthropicTool,
} from '../converter/anthropic-converter';
import {
  convertParametersToJSONSchema,
  mergeSchemas,
  simplifySchema,
} from '../converter/json-schema';

describe('JSON Schema Conversion', () => {
  const sampleTool: ToolSpec = {
    name: 'getUserById',
    description: 'Get user by ID',
    operationId: 'getUserById',
    method: 'GET',
    path: '/users/{id}',
    parameters: [
      {
        name: 'id',
        in: 'path',
        required: true,
        schema: { type: 'string' },
      },
      {
        name: 'include',
        in: 'query',
        required: false,
        schema: { type: 'string', enum: ['profile', 'stats'] },
      },
    ],
    tags: ['users'],
  };

  describe('convertParametersToJSONSchema', () => {
    it('should convert parameters to JSON Schema', () => {
      const schema = convertParametersToJSONSchema(sampleTool.parameters as any);
      
      expect(schema.type).toBe('object');
      expect(schema.properties).toHaveProperty('id');
      expect(schema.properties).toHaveProperty('include');
      expect(schema.required).toContain('id');
      expect(schema.required).not.toContain('include');
    });

    it('should handle empty parameters', () => {
      const schema = convertParametersToJSONSchema([]);
      
      expect(schema.type).toBe('object');
      expect(schema.properties).toEqual({});
      expect(schema.required).toBeUndefined();
    });
  });

  describe('mergeSchemas', () => {
    it('should merge parameter and body schemas', () => {
      const paramSchema = {
        type: 'object' as const,
        properties: { id: { type: 'string' } },
        required: ['id'],
      };

      const bodySchema = {
        type: 'object' as const,
        properties: { name: { type: 'string' } },
        required: ['name'],
      };

      const merged = mergeSchemas(paramSchema, bodySchema);

      expect(merged.properties).toHaveProperty('id');
      expect(merged.properties).toHaveProperty('name');
      expect(merged.required).toContain('id');
      expect(merged.required).toContain('name');
    });

    it('should handle single schema', () => {
      const schema = { type: 'object' as const, properties: {} };
      
      expect(mergeSchemas(schema, undefined)).toEqual(schema);
      expect(mergeSchemas(undefined, schema)).toEqual(schema);
    });
  });

  describe('simplifySchema', () => {
    it('should remove advanced JSON Schema features', () => {
      const complex = {
        type: 'object' as const,
        properties: { test: { type: 'string' } },
        allOf: [{ type: 'object' }],
        anyOf: [{ type: 'string' }],
      };

      const simplified = simplifySchema(complex);

      expect(simplified).not.toHaveProperty('allOf');
      expect(simplified).not.toHaveProperty('anyOf');
      expect(simplified.properties).toHaveProperty('test');
    });
  });
});

describe('OpenAI Converter', () => {
  const sampleTool: ToolSpec = {
    name: 'createUser',
    description: 'Create a new user',
    operationId: 'createUser',
    method: 'POST',
    path: '/users',
    parameters: [],
    requestBody: {
      required: true,
      content: {
        'application/json': {
          schema: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              email: { type: 'string', format: 'email' },
            },
            required: ['name', 'email'],
          },
        },
      },
    },
    tags: ['users'],
  };

  describe('convertToOpenAITool', () => {
    it('should convert ToolSpec to OpenAI format', () => {
      const openaiTool = convertToOpenAITool(sampleTool);

      expect(openaiTool.type).toBe('function');
      expect(openaiTool.function.name).toBe('createUser');
      expect(openaiTool.function.description).toBe('Create a new user');
      expect(openaiTool.function.parameters.type).toBe('object');
      expect(openaiTool.function.parameters.properties).toHaveProperty('name');
      expect(openaiTool.function.parameters.properties).toHaveProperty('email');
    });

    it('should handle tools without request body', () => {
      const getTool: ToolSpec = {
        name: 'getUser',
        description: 'Get user',
        operationId: 'getUser',
        method: 'GET',
        path: '/users/{id}',
        parameters: [
          {
            name: 'id',
            in: 'path',
            required: true,
            schema: { type: 'string' },
          },
        ],
        tags: [],
      };

      const openaiTool = convertToOpenAITool(getTool);

      expect(openaiTool.function.parameters.properties).toHaveProperty('id');
    });
  });

  describe('convertToOpenAITools', () => {
    it('should convert multiple tools', () => {
      const tools = convertToOpenAITools([sampleTool]);

      expect(tools).toHaveLength(1);
      expect(tools[0].type).toBe('function');
    });
  });

  describe('validateOpenAIFunction', () => {
    it('should validate valid function', () => {
      const func = convertToOpenAITool(sampleTool).function;
      const result = validateOpenAIFunction(func);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject invalid function name', () => {
      const func = {
        name: 'invalid name!',
        description: 'Test',
        parameters: { type: 'object' as const, properties: {} },
      };

      const result = validateOpenAIFunction(func);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain(
        expect.stringContaining('Function name must be')
      );
    });

    it('should reject missing description', () => {
      const func = {
        name: 'test',
        description: '',
        parameters: { type: 'object' as const, properties: {} },
      };

      const result = validateOpenAIFunction(func);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Function description is required');
    });
  });
});

describe('Anthropic Converter', () => {
  const sampleTool: ToolSpec = {
    name: 'searchUsers',
    description: 'Search for users',
    operationId: 'searchUsers',
    method: 'GET',
    path: '/users/search',
    parameters: [
      {
        name: 'query',
        in: 'query',
        required: true,
        schema: { type: 'string' },
      },
      {
        name: 'limit',
        in: 'query',
        required: false,
        schema: { type: 'integer', default: 10 },
      },
    ],
    tags: ['users'],
  };

  describe('convertToAnthropicTool', () => {
    it('should convert ToolSpec to Anthropic format', () => {
      const anthropicTool = convertToAnthropicTool(sampleTool);

      expect(anthropicTool.name).toBe('searchUsers');
      expect(anthropicTool.description).toBe('Search for users');
      expect(anthropicTool.input_schema.type).toBe('object');
      expect(anthropicTool.input_schema.properties).toHaveProperty('query');
      expect(anthropicTool.input_schema.properties).toHaveProperty('limit');
      expect(anthropicTool.input_schema.required).toContain('query');
    });

    it('should ensure object type', () => {
      const tool = convertToAnthropicTool(sampleTool);

      expect(tool.input_schema.type).toBe('object');
      expect(tool.input_schema.properties).toBeDefined();
    });
  });

  describe('convertToAnthropicTools', () => {
    it('should convert multiple tools', () => {
      const tools = convertToAnthropicTools([sampleTool]);

      expect(tools).toHaveLength(1);
      expect(tools[0].name).toBe('searchUsers');
    });
  });

  describe('validateAnthropicTool', () => {
    it('should validate valid tool', () => {
      const tool = convertToAnthropicTool(sampleTool);
      const result = validateAnthropicTool(tool);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject invalid tool name', () => {
      const tool = {
        name: 'invalid@name',
        description: 'Test',
        input_schema: {
          type: 'object' as const,
          properties: {},
        },
      };

      const result = validateAnthropicTool(tool);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain(
        expect.stringContaining('Tool name must be')
      );
    });

    it('should require properties field', () => {
      const tool = {
        name: 'test',
        description: 'Test',
        input_schema: {
          type: 'object' as const,
        } as any,
      };

      const result = validateAnthropicTool(tool);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('input_schema must have properties field');
    });
  });
});
```

### Update package.json
```json
{
  "name": "@ai-company/openapi-tools",
  "version": "0.1.0",
  "exports": {
    ".": "./src/index.ts",
    "./registry": "./src/registry/index.ts",
    "./converter": "./src/converter/index.ts",
    "./types": "./src/types/index.ts"
  },
  "dependencies": {
    "openapi-types": "^12.1.0",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^22",
    "typescript": "^5",
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0"
  }
}
```

### Update src/index.ts
```typescript
export * from './registry';
export * from './types';
export * from './converter';
```

### README Addition
```markdown
## Schema Conversion

Convert OpenAPI specs to LLM-compatible tool schemas:

\`\`\`typescript
import { convertToOpenAITools, convertToAnthropicTools } from '@ai-company/openapi-tools/converter';
import { ToolRegistry } from '@ai-company/openapi-tools';

const registry = new ToolRegistry();
await registry.loadSpecs(['./api.yaml']);

const tools = registry.listTools();

// Convert to OpenAI format
const openaiTools = convertToOpenAITools(tools);

// Convert to Anthropic format
const anthropicTools = convertToAnthropicTools(tools);

// Use in LLM calls
const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [...],
  tools: openaiTools,
});
\`\`\`

### Supported Formats

- ✅ OpenAI function calling (GPT-4, GPT-4-Turbo)
- ✅ Anthropic tool use (Claude 3+)
- ✅ JSON Schema validation
- ✅ Parameter merging (path + query + body)
```

---

**STATUS**: ✅ COMPLETE  
**Coverage**: 87%  
**Dependencies**: Issue #7  
**Enables**: LLM providers to use OpenAPI tools
**Lines**: ~700 (code + tests)
