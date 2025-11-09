/**
 * OpenAPI to Tool Spec Converter
 *
 * Converts OpenAPI 3.0/3.1 operations to tool specifications
 * compatible with LLM function calling formats.
 */

import {
  ToolSpec,
  OpenAPISpec,
  OpenAPIOperation,
  OpenAPIParameter,
} from "../types/index.js";

/**
 * Convert OpenAPI specification to tool specifications
 *
 * @param spec - OpenAPI specification
 * @param schemaConverter - Optional custom schema converter
 * @returns Array of tool specifications
 */
export function openApiToToolSpecs(
  spec: OpenAPISpec,
  schemaConverter?: (schema: unknown) => Record<string, unknown>,
): ToolSpec[] {
  const tools: ToolSpec[] = [];
  const converter = schemaConverter || defaultSchemaConverter;

  if (!spec.paths) {
    return tools;
  }

  // Iterate through all paths
  for (const [path, pathItem] of Object.entries(spec.paths)) {
    // Iterate through HTTP methods
    for (const [method, operation] of Object.entries(pathItem)) {
      if (!isHttpMethod(method)) {
        continue;
      }

      const toolSpec = convertOperationToToolSpec(
        operation,
        method.toUpperCase(),
        path,
        converter,
      );

      if (toolSpec) {
        tools.push(toolSpec);
      }
    }
  }

  return tools;
}

/**
 * Convert OpenAPI operation to tool specification
 */
function convertOperationToToolSpec(
  operation: OpenAPIOperation,
  method: string,
  path: string,
  schemaConverter: (schema: unknown) => Record<string, unknown>,
): ToolSpec | null {
  // Require operationId for tool name
  if (!operation.operationId) {
    console.warn(`Skipping operation ${method} ${path}: missing operationId`);
    return null;
  }

  // Extract description
  const description =
    operation.description ||
    operation.summary ||
    `Execute ${operation.operationId}`;

  // Extract category from first tag
  const category = operation.tags?.[0];

  // Build JSON Schema for parameters
  const jsonSchema = buildParameterSchema(operation, schemaConverter);

  return {
    name: operation.operationId,
    description,
    jsonSchema,
    operationId: operation.operationId,
    method,
    endpoint: path,
    category,
    metadata: {
      tags: operation.tags || [],
      method,
      path,
    },
  };
}

/**
 * Build JSON Schema from OpenAPI operation parameters and request body
 */
function buildParameterSchema(
  operation: OpenAPIOperation,
  schemaConverter: (schema: unknown) => Record<string, unknown>,
): Record<string, unknown> {
  const properties: Record<string, unknown> = {};
  const required: string[] = [];

  // Process path/query/header parameters
  if (operation.parameters) {
    for (const param of operation.parameters) {
      const paramSchema = convertParameterToSchema(param, schemaConverter);
      if (paramSchema) {
        properties[param.name] = paramSchema;
        if (param.required) {
          required.push(param.name);
        }
      }
    }
  }

  // Process request body
  if (operation.requestBody) {
    const bodySchema = convertRequestBodyToSchema(
      operation.requestBody,
      schemaConverter,
    );
    if (bodySchema) {
      // Merge body schema properties
      if (bodySchema.properties) {
        Object.assign(properties, bodySchema.properties);
      }
      if (bodySchema.required) {
        required.push(...(bodySchema.required as string[]));
      }
    }
  }

  return {
    type: "object",
    properties,
    required: required.length > 0 ? required : undefined,
  };
}

/**
 * Convert OpenAPI parameter to JSON Schema property
 */
function convertParameterToSchema(
  param: OpenAPIParameter,
  schemaConverter: (schema: unknown) => Record<string, unknown>,
): Record<string, unknown> | null {
  if (!param.schema) {
    // Default to string if no schema
    return {
      type: "string",
      description: param.description,
    };
  }

  const converted = schemaConverter(param.schema);
  return {
    ...converted,
    description: param.description || converted.description,
  };
}

/**
 * Convert request body to JSON Schema
 */
function convertRequestBodyToSchema(
  requestBody: { content?: Record<string, { schema?: unknown }> },
  schemaConverter: (schema: unknown) => Record<string, unknown>,
): Record<string, unknown> | null {
  if (!requestBody.content) {
    return null;
  }

  // Prefer application/json
  const jsonContent = requestBody.content["application/json"];
  if (jsonContent?.schema) {
    return schemaConverter(jsonContent.schema);
  }

  // Fallback to first content type
  const firstContent = Object.values(requestBody.content)[0];
  if (firstContent?.schema) {
    return schemaConverter(firstContent.schema);
  }

  return null;
}

/**
 * Default schema converter - converts OpenAPI schema to JSON Schema
 */
function defaultSchemaConverter(schema: unknown): Record<string, unknown> {
  if (typeof schema !== "object" || schema === null) {
    return { type: "string" };
  }

  const s = schema as Record<string, unknown>;

  // Basic type mapping
  const typeMap: Record<string, string> = {
    integer: "integer",
    number: "number",
    string: "string",
    boolean: "boolean",
    array: "array",
    object: "object",
  };

  const result: Record<string, unknown> = {};

  // Map OpenAPI types to JSON Schema types
  if (s.type && typeof s.type === "string") {
    result.type = typeMap[s.type] || s.type;
  }

  // Copy common fields
  if (s.description) result.description = s.description;
  if (s.format) result.format = s.format;
  if (s.enum) result.enum = s.enum;
  if (s.default !== undefined) result.default = s.default;
  if (s.example !== undefined) result.example = s.example;

  // Handle array items
  if (s.type === "array" && s.items) {
    result.items = defaultSchemaConverter(s.items);
  }

  // Handle object properties
  if (s.type === "object" && s.properties) {
    result.properties = {};
    const props = s.properties as Record<string, unknown>;
    for (const [key, value] of Object.entries(props)) {
      result.properties[key] = defaultSchemaConverter(value);
    }

    if (s.required) {
      result.required = s.required;
    }
  }

  return result;
}

/**
 * Check if string is HTTP method
 */
function isHttpMethod(method: string): boolean {
  const methods = ["get", "post", "put", "patch", "delete", "options", "head"];
  return methods.includes(method.toLowerCase());
}
