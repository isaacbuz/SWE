/**
 * OpenAPI Tools Package
 * 
 * Provides OpenAPI specification loading, tool registry, and conversion
 * utilities for LLM function calling.
 */

export { ToolRegistry } from "./registry/ToolRegistry.js";
export { openApiToToolSpecs } from "./converter/index.js";
export { ToolExecutor } from "./executor/ToolExecutor.js";
export { SchemaValidator } from "./executor/SchemaValidator.js";
export { RateLimiter } from "./executor/RateLimiter.js";
export { EnhancedRateLimiter, InMemoryRateLimitStorage } from "./ratelimit/EnhancedRateLimiter.js";
export { CircuitBreaker } from "./executor/CircuitBreaker.js";
export { PermissionChecker } from "./permissions/PermissionChecker.js";
export type {
  ToolSpec,
  OpenAPISpec,
  OpenAPIOperation,
  OpenAPIParameter,
  ToolRegistryOptions,
} from "./types/index.js";
export type {
  ToolHandler,
  ToolResult,
  ToolExecutorOptions,
} from "./executor/ToolExecutor.js";
export type {
  ValidationResult,
} from "./executor/SchemaValidator.js";
export type {
  RateLimitResult,
  RateLimitConfig,
} from "./executor/RateLimiter.js";
export type {
  RateLimit,
  CostQuota,
  QuotaResult,
  UsageStats,
  RateLimitStorage,
} from "./ratelimit/EnhancedRateLimiter.js";
export type {
  Role,
  Permission,
  PermissionCondition,
  RoleDefinition,
  UserPermissions,
} from "./permissions/PermissionModel.js";
export {
  PermissionDeniedError,
} from "./permissions/PermissionModel.js";

