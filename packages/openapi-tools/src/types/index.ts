/**
 * Type definitions for OpenAPI Tool Registry
 */

/**
 * Tool specification extracted from OpenAPI operation
 */
export interface ToolSpec {
  /** Unique tool name (operationId) */
  name: string;
  
  /** Tool description (from operation summary/description) */
  description: string;
  
  /** JSON Schema for tool parameters */
  jsonSchema: Record<string, unknown>;
  
  /** OpenAPI operation ID */
  operationId: string;
  
  /** HTTP method (GET, POST, etc.) */
  method?: string;
  
  /** API endpoint path */
  endpoint?: string;
  
  /** Tool category/tag */
  category?: string;
  
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * OpenAPI specification structure
 */
export interface OpenAPISpec {
  openapi: string;
  info: {
    title: string;
    version: string;
    description?: string;
  };
  paths: Record<string, Record<string, OpenAPIOperation>>;
  components?: {
    schemas?: Record<string, unknown>;
    parameters?: Record<string, unknown>;
  };
}

/**
 * OpenAPI operation structure
 */
export interface OpenAPIOperation {
  operationId?: string;
  summary?: string;
  description?: string;
  tags?: string[];
  parameters?: OpenAPIParameter[];
  requestBody?: {
    content?: Record<string, { schema?: unknown }>;
  };
  responses?: Record<string, unknown>;
}

/**
 * OpenAPI parameter structure
 */
export interface OpenAPIParameter {
  name: string;
  in: "query" | "header" | "path" | "cookie";
  required?: boolean;
  schema?: unknown;
  description?: string;
}

/**
 * Tool registry options
 */
export interface ToolRegistryOptions {
  /** Whether to validate OpenAPI specs */
  validate?: boolean;
  
  /** Whether to merge multiple specs */
  merge?: boolean;
  
  /** Custom schema converter */
  schemaConverter?: (schema: unknown) => Record<string, unknown>;
}

