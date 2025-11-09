/**
 * OpenAPI Tool Registry
 * 
 * Provides infrastructure for managing OpenAPI tool specifications
 * and converting them to LLM-compatible tool formats.
 */

export { ToolRegistry } from './registry';
export type {
  ToolSpec,
  ToolRegistryOptions,
  ToolHandler,
  ToolExecutionResult,
} from './types';

export {
  toOpenAIFormat,
  toAnthropicFormat,
  toGoogleFormat,
  toGenericFormat,
  convertToolSpec,
  convertToolSpecs,
  validateConvertedTool,
  extractRequiredFields,
} from './converters';
export type { ProviderFormat, ConvertedTool } from './converters';

export { ToolExecutor } from './executor';
export type { ExecutorOptions, AuditLog, RateLimitState } from './executor';

