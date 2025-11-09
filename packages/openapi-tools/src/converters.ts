/**
 * OpenAPI to Tool Spec Converter
 * 
 * Converts ToolSpec objects from the registry into LLM provider-specific formats
 * (OpenAI, Anthropic, Google Gemini, etc.)
 */
import { ToolSpec } from './types';

export type ProviderFormat = 'openai' | 'anthropic' | 'google' | 'generic';

export interface ConvertedTool {
  /** Provider-specific tool format */
  format: ProviderFormat;
  /** Converted tool object */
  tool: any;
}

/**
 * Convert ToolSpec to OpenAI function calling format
 */
export function toOpenAIFormat(toolSpec: ToolSpec): any {
  return {
    type: 'function',
    function: {
      name: toolSpec.name,
      description: toolSpec.description,
      parameters: normalizeJsonSchema(toolSpec.jsonSchema),
    },
  };
}

/**
 * Convert ToolSpec to Anthropic tool use format
 */
export function toAnthropicFormat(toolSpec: ToolSpec): any {
  const schema = normalizeJsonSchema(toolSpec.jsonSchema);
  
  return {
    name: toolSpec.name,
    description: toolSpec.description,
    input_schema: {
      type: 'object',
      properties: schema.properties || {},
      required: schema.required || [],
    },
  };
}

/**
 * Convert ToolSpec to Google Gemini function calling format
 */
export function toGoogleFormat(toolSpec: ToolSpec): any {
  const schema = normalizeJsonSchema(toolSpec.jsonSchema);
  
  return {
    name: toolSpec.name,
    description: toolSpec.description,
    parameters: {
      type: 'object',
      properties: schema.properties || {},
      required: schema.required || [],
    },
  };
}

/**
 * Convert ToolSpec to generic JSON Schema format
 */
export function toGenericFormat(toolSpec: ToolSpec): any {
  return {
    name: toolSpec.name,
    description: toolSpec.description,
    parameters: normalizeJsonSchema(toolSpec.jsonSchema),
  };
}

/**
 * Convert ToolSpec to provider-specific format
 */
export function convertToolSpec(
  toolSpec: ToolSpec,
  provider: ProviderFormat = 'openai'
): ConvertedTool {
  let tool: any;

  switch (provider) {
    case 'openai':
      tool = toOpenAIFormat(toolSpec);
      break;
    case 'anthropic':
      tool = toAnthropicFormat(toolSpec);
      break;
    case 'google':
      tool = toGoogleFormat(toolSpec);
      break;
    case 'generic':
      tool = toGenericFormat(toolSpec);
      break;
    default:
      throw new Error(`Unsupported provider format: ${provider}`);
  }

  return {
    format: provider,
    tool,
  };
}

/**
 * Convert multiple ToolSpecs to provider format
 */
export function convertToolSpecs(
  toolSpecs: ToolSpec[],
  provider: ProviderFormat = 'openai'
): ConvertedTool[] {
  return toolSpecs.map(spec => convertToolSpec(spec, provider));
}

/**
 * Normalize JSON Schema to ensure consistent structure
 */
function normalizeJsonSchema(schema: any): any {
  if (!schema || typeof schema !== 'object') {
    return {
      type: 'object',
      properties: {},
      required: [],
    };
  }

  // If it's already a proper JSON Schema, return as-is
  if (schema.type === 'object' && schema.properties) {
    return {
      type: 'object',
      properties: schema.properties,
      required: schema.required || [],
      ...(schema.additionalProperties !== undefined && {
        additionalProperties: schema.additionalProperties,
      }),
    };
  }

  // If it's a simple object, wrap it
  if (!schema.type && !schema.properties) {
    return {
      type: 'object',
      properties: schema,
      required: [],
    };
  }

  // Ensure required is an array
  return {
    ...schema,
    type: schema.type || 'object',
    properties: schema.properties || {},
    required: Array.isArray(schema.required) ? schema.required : [],
  };
}

/**
 * Extract required fields from JSON Schema
 */
export function extractRequiredFields(schema: any): string[] {
  if (!schema || typeof schema !== 'object') {
    return [];
  }

  if (Array.isArray(schema.required)) {
    return schema.required;
  }

  if (schema.properties && typeof schema.properties === 'object') {
    // Check for required markers in properties
    const required: string[] = [];
    for (const [key, prop] of Object.entries(schema.properties)) {
      if (typeof prop === 'object' && prop !== null && 'required' in prop) {
        if (prop.required === true) {
          required.push(key);
        }
      }
    }
    return required;
  }

  return [];
}

/**
 * Validate converted tool format
 */
export function validateConvertedTool(
  converted: ConvertedTool,
  provider: ProviderFormat
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (converted.format !== provider) {
    errors.push(`Format mismatch: expected ${provider}, got ${converted.format}`);
  }

  const tool = converted.tool;

  switch (provider) {
    case 'openai':
      if (!tool.type || tool.type !== 'function') {
        errors.push('OpenAI format must have type: "function"');
      }
      if (!tool.function) {
        errors.push('OpenAI format must have function property');
      } else {
        if (!tool.function.name) errors.push('Function must have name');
        if (!tool.function.description) errors.push('Function must have description');
        if (!tool.function.parameters) errors.push('Function must have parameters');
      }
      break;

    case 'anthropic':
      if (!tool.name) errors.push('Anthropic format must have name');
      if (!tool.description) errors.push('Anthropic format must have description');
      if (!tool.input_schema) {
        errors.push('Anthropic format must have input_schema');
      } else {
        if (tool.input_schema.type !== 'object') {
          errors.push('input_schema must have type: "object"');
        }
      }
      break;

    case 'google':
      if (!tool.name) errors.push('Google format must have name');
      if (!tool.description) errors.push('Google format must have description');
      if (!tool.parameters) {
        errors.push('Google format must have parameters');
      } else {
        if (tool.parameters.type !== 'object') {
          errors.push('parameters must have type: "object"');
        }
      }
      break;
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

