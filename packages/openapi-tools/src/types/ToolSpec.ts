/**
 * ToolSpec - Standard interface for LLM tool specifications
 * 
 * This interface represents a tool that can be called by LLM providers.
 * It's derived from OpenAPI operation definitions and converted to
 * provider-specific formats (OpenAI functions, Anthropic tools, etc.)
 */
export interface ToolSpec {
  /**
   * Tool name (operationId from OpenAPI)
   */
  name: string;

  /**
   * Human-readable description for LLM context
   */
  description: string;

  /**
   * JSON Schema for tool parameters
   * This is derived from the OpenAPI requestBody or parameters
   */
  jsonSchema: object;

  /**
   * Original OpenAPI operationId
   */
  operationId: string;

  /**
   * Optional HTTP endpoint path (for reference)
   */
  endpoint?: string;

  /**
   * HTTP method (GET, POST, etc.)
   */
  method?: string;

  /**
   * Tags/categories for grouping tools
   */
  tags?: string[];

  /**
   * Additional metadata from OpenAPI spec
   */
  metadata?: {
    summary?: string;
    deprecated?: boolean;
    [key: string]: unknown;
  };
}

/**
 * ToolRegistryOptions - Configuration for ToolRegistry
 */
export interface ToolRegistryOptions {
  /**
   * Whether to validate OpenAPI specs on load
   * @default true
   */
  validateOnLoad?: boolean;

  /**
   * Whether to allow duplicate operationIds
   * @default false
   */
  allowDuplicates?: boolean;

  /**
   * Custom operationId resolver when operationId is missing
   */
  operationIdResolver?: (method: string, path: string) => string;
}

/**
 * LoadedSpec - Metadata about a loaded OpenAPI specification
 */
export interface LoadedSpec {
  /**
   * Path to the spec file
   */
  path: string;

  /**
   * OpenAPI version (3.0.0, 3.1.0, etc.)
   */
  version: string;

  /**
   * Title from info section
   */
  title?: string;

  /**
   * Number of tools extracted from this spec
   */
  toolCount: number;

  /**
   * Timestamp when spec was loaded
   */
  loadedAt: Date;
}

