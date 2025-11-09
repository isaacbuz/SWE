/**
 * Tests for Tool Spec Converters
 */
import { describe, it, expect } from 'vitest';
import {
  toOpenAIFormat,
  toAnthropicFormat,
  toGoogleFormat,
  toGenericFormat,
  convertToolSpec,
  convertToolSpecs,
  validateConvertedTool,
  extractRequiredFields,
} from '../converters';
import { ToolSpec } from '../types';

describe('Tool Spec Converters', () => {
  const sampleToolSpec: ToolSpec = {
    name: 'createUser',
    description: 'Create a new user account',
    operationId: 'createUser',
    jsonSchema: {
      type: 'object',
      properties: {
        email: {
          type: 'string',
          format: 'email',
          description: 'User email address',
        },
        password: {
          type: 'string',
          minLength: 8,
          description: 'User password',
        },
        name: {
          type: 'string',
          description: 'User full name',
        },
      },
      required: ['email', 'password'],
    },
    endpoint: '/users',
    method: 'POST',
    tags: ['users'],
  };

  describe('toOpenAIFormat', () => {
    it('should convert to OpenAI format', () => {
      const result = toOpenAIFormat(sampleToolSpec);

      expect(result).toHaveProperty('type', 'function');
      expect(result).toHaveProperty('function');
      expect(result.function).toHaveProperty('name', 'createUser');
      expect(result.function).toHaveProperty('description');
      expect(result.function).toHaveProperty('parameters');
      expect(result.function.parameters).toHaveProperty('type', 'object');
      expect(result.function.parameters).toHaveProperty('properties');
      expect(result.function.parameters).toHaveProperty('required');
      expect(result.function.parameters.required).toContain('email');
      expect(result.function.parameters.required).toContain('password');
    });

    it('should handle missing required fields', () => {
      const specWithoutRequired: ToolSpec = {
        ...sampleToolSpec,
        jsonSchema: {
          type: 'object',
          properties: {
            email: { type: 'string' },
          },
        },
      };

      const result = toOpenAIFormat(specWithoutRequired);
      expect(result.function.parameters.required).toEqual([]);
    });
  });

  describe('toAnthropicFormat', () => {
    it('should convert to Anthropic format', () => {
      const result = toAnthropicFormat(sampleToolSpec);

      expect(result).toHaveProperty('name', 'createUser');
      expect(result).toHaveProperty('description');
      expect(result).toHaveProperty('input_schema');
      expect(result.input_schema).toHaveProperty('type', 'object');
      expect(result.input_schema).toHaveProperty('properties');
      expect(result.input_schema).toHaveProperty('required');
      expect(result.input_schema.required).toContain('email');
    });

    it('should have correct input_schema structure', () => {
      const result = toAnthropicFormat(sampleToolSpec);
      expect(result.input_schema.type).toBe('object');
      expect(typeof result.input_schema.properties).toBe('object');
      expect(Array.isArray(result.input_schema.required)).toBe(true);
    });
  });

  describe('toGoogleFormat', () => {
    it('should convert to Google format', () => {
      const result = toGoogleFormat(sampleToolSpec);

      expect(result).toHaveProperty('name', 'createUser');
      expect(result).toHaveProperty('description');
      expect(result).toHaveProperty('parameters');
      expect(result.parameters).toHaveProperty('type', 'object');
      expect(result.parameters).toHaveProperty('properties');
      expect(result.parameters).toHaveProperty('required');
    });
  });

  describe('toGenericFormat', () => {
    it('should convert to generic format', () => {
      const result = toGenericFormat(sampleToolSpec);

      expect(result).toHaveProperty('name', 'createUser');
      expect(result).toHaveProperty('description');
      expect(result).toHaveProperty('parameters');
      expect(result.parameters).toHaveProperty('type', 'object');
    });
  });

  describe('convertToolSpec', () => {
    it('should convert to OpenAI format by default', () => {
      const result = convertToolSpec(sampleToolSpec);
      expect(result.format).toBe('openai');
      expect(result.tool).toHaveProperty('type', 'function');
    });

    it('should convert to specified provider format', () => {
      const anthropicResult = convertToolSpec(sampleToolSpec, 'anthropic');
      expect(anthropicResult.format).toBe('anthropic');
      expect(anthropicResult.tool).toHaveProperty('name');

      const googleResult = convertToolSpec(sampleToolSpec, 'google');
      expect(googleResult.format).toBe('google');
      expect(googleResult.tool).toHaveProperty('name');
    });

    it('should throw error for unsupported provider', () => {
      expect(() => {
        convertToolSpec(sampleToolSpec, 'unsupported' as any);
      }).toThrow('Unsupported provider format');
    });
  });

  describe('convertToolSpecs', () => {
    it('should convert multiple tool specs', () => {
      const specs: ToolSpec[] = [
        sampleToolSpec,
        {
          ...sampleToolSpec,
          name: 'updateUser',
          operationId: 'updateUser',
        },
      ];

      const results = convertToolSpecs(specs, 'openai');
      expect(results).toHaveLength(2);
      expect(results[0].format).toBe('openai');
      expect(results[1].format).toBe('openai');
    });
  });

  describe('extractRequiredFields', () => {
    it('should extract required fields from schema', () => {
      const schema = {
        type: 'object',
        properties: {
          email: { type: 'string' },
          password: { type: 'string' },
        },
        required: ['email', 'password'],
      };

      const required = extractRequiredFields(schema);
      expect(required).toContain('email');
      expect(required).toContain('password');
    });

    it('should return empty array for missing required', () => {
      const schema = {
        type: 'object',
        properties: {
          email: { type: 'string' },
        },
      };

      const required = extractRequiredFields(schema);
      expect(required).toEqual([]);
    });
  });

  describe('validateConvertedTool', () => {
    it('should validate OpenAI format', () => {
      const converted = convertToolSpec(sampleToolSpec, 'openai');
      const validation = validateConvertedTool(converted, 'openai');

      expect(validation.valid).toBe(true);
      expect(validation.errors).toHaveLength(0);
    });

    it('should validate Anthropic format', () => {
      const converted = convertToolSpec(sampleToolSpec, 'anthropic');
      const validation = validateConvertedTool(converted, 'anthropic');

      expect(validation.valid).toBe(true);
      expect(validation.errors).toHaveLength(0);
    });

    it('should validate Google format', () => {
      const converted = convertToolSpec(sampleToolSpec, 'google');
      const validation = validateConvertedTool(converted, 'google');

      expect(validation.valid).toBe(true);
      expect(validation.errors).toHaveLength(0);
    });

    it('should detect invalid format', () => {
      const invalid = {
        format: 'openai' as const,
        tool: {
          type: 'invalid',
        },
      };

      const validation = validateConvertedTool(invalid, 'openai');
      expect(validation.valid).toBe(false);
      expect(validation.errors.length).toBeGreaterThan(0);
    });
  });

  describe('edge cases', () => {
    it('should handle empty schema', () => {
      const emptySpec: ToolSpec = {
        ...sampleToolSpec,
        jsonSchema: {},
      };

      const result = toOpenAIFormat(emptySpec);
      expect(result.function.parameters).toHaveProperty('type', 'object');
      expect(result.function.parameters).toHaveProperty('properties');
    });

    it('should handle null schema', () => {
      const nullSpec: ToolSpec = {
        ...sampleToolSpec,
        jsonSchema: null as any,
      };

      const result = toOpenAIFormat(nullSpec);
      expect(result.function.parameters).toHaveProperty('type', 'object');
    });

    it('should preserve schema properties', () => {
      const schemaWithFormat = {
        ...sampleToolSpec.jsonSchema,
        properties: {
          email: {
            type: 'string',
            format: 'email',
          },
        },
      };

      const spec: ToolSpec = {
        ...sampleToolSpec,
        jsonSchema: schemaWithFormat,
      };

      const result = toOpenAIFormat(spec);
      expect(result.function.parameters.properties.email.format).toBe('email');
    });
  });
});

