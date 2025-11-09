/**
 * Type definitions for OpenAPI Tool Registry
 */

export interface ToolSpec {
  /** Unique tool identifier (operationId from OpenAPI) */
  name: string;
  
  /** Human-readable description */
  description: string;
  
  /** JSON Schema for tool parameters */
  jsonSchema: Record<string, any>;
  
  /** OpenAPI operationId */
  operationId: string;
  
  /** HTTP endpoint path (if applicable) */
  endpoint?: string;
  
  /** HTTP method (if applicable) */
  method?: string;
  
  /** Tool category/tags */
  tags?: string[];
  
  /** Whether tool requires authentication */
  requiresAuth?: boolean;
  
  /** Rate limit per minute */
  rateLimit?: number;
}

export interface ToolRegistryOptions {
  /** Paths to OpenAPI spec files */
  specPaths?: string[];
  
  /** Whether to validate specs on load */
  validateOnLoad?: boolean;
  
  /** Custom tool handlers */
  handlers?: Map<string, ToolHandler>;
}

export type ToolHandler = (args: Record<string, any>) => Promise<any>;

export interface ToolExecutionResult {
  success: boolean;
  result?: any;
  error?: string;
  executionTimeMs: number;
}

