/**
 * Tool Executor
 * 
 * Executes tools with schema validation, rate limiting, and error handling.
 */

import { ToolSpec } from "../types/index.js";
import { SchemaValidator } from "./SchemaValidator.js";
import { RateLimiter } from "./RateLimiter.js";
import { CircuitBreaker } from "./CircuitBreaker.js";

export interface ToolHandler {
  (args: Record<string, unknown>): Promise<unknown> | unknown;
}

export interface ToolResult {
  success: boolean;
  result?: unknown;
  error?: string;
  executionTimeMs: number;
  validated: boolean;
}

export interface ToolExecutorOptions {
  /** Enable schema validation */
  validate?: boolean;
  
  /** Enable rate limiting */
  rateLimit?: boolean;
  
  /** Enable circuit breaker */
  circuitBreaker?: boolean;
  
  /** Custom validator */
  validator?: SchemaValidator;
  
  /** Custom rate limiter */
  rateLimiter?: RateLimiter;
  
  /** Custom circuit breaker */
  circuitBreakerInstance?: CircuitBreaker;
  
  /** Maximum execution time in milliseconds */
  timeout?: number;
}

export class ToolExecutor {
  private handlers: Map<string, ToolHandler> = new Map();
  private validator: SchemaValidator;
  private rateLimiter: RateLimiter;
  private circuitBreaker: CircuitBreaker;
  private options: Required<Omit<ToolExecutorOptions, "validator" | "rateLimiter" | "circuitBreakerInstance">> & {
    validator?: SchemaValidator;
    rateLimiter?: RateLimiter;
    circuitBreakerInstance?: CircuitBreaker;
  };

  constructor(options: ToolExecutorOptions = {}) {
    this.options = {
      validate: options.validate ?? true,
      rateLimit: options.rateLimit ?? true,
      circuitBreaker: options.circuitBreaker ?? true,
      timeout: options.timeout ?? 30000,
      validator: options.validator,
      rateLimiter: options.rateLimiter,
      circuitBreakerInstance: options.circuitBreakerInstance,
    };

    this.validator = this.options.validator || new SchemaValidator();
    this.rateLimiter = this.options.rateLimiter || new RateLimiter();
    this.circuitBreaker = this.options.circuitBreakerInstance || new CircuitBreaker();
  }

  /**
   * Register a tool handler
   */
  registerTool(
    name: string,
    handler: ToolHandler,
    spec?: ToolSpec
  ): void {
    if (this.handlers.has(name)) {
      throw new Error(`Tool '${name}' is already registered`);
    }

    this.handlers.set(name, handler);

    // Register schema if provided
    if (spec && this.options.validate) {
      this.validator.registerSchema(name, spec.jsonSchema);
    }
  }

  /**
   * Unregister a tool
   */
  unregisterTool(name: string): boolean {
    this.handlers.delete(name);
    this.validator.unregisterSchema(name);
    return true;
  }

  /**
   * Execute a tool
   */
  async execute(
    toolName: string,
    args: unknown,
    spec?: ToolSpec
  ): Promise<ToolResult> {
    const startTime = Date.now();

    try {
      // 1. Check if tool exists
      const handler = this.handlers.get(toolName);
      if (!handler) {
        return {
          success: false,
          error: `Tool '${toolName}' not found`,
          executionTimeMs: Date.now() - startTime,
          validated: false,
        };
      }

      // 2. Validate arguments if enabled
      if (this.options.validate && spec) {
        const validationResult = this.validator.validate(
          toolName,
          args,
          spec.jsonSchema
        );

        if (!validationResult.valid) {
          return {
            success: false,
            error: `Validation failed: ${validationResult.errors.join(", ")}`,
            executionTimeMs: Date.now() - startTime,
            validated: false,
          };
        }
      }

      // 3. Rate limiting check
      if (this.options.rateLimit) {
        const rateLimitResult = await this.rateLimiter.checkLimit(toolName);
        if (!rateLimitResult.allowed) {
          return {
            success: false,
            error: `Rate limit exceeded: ${rateLimitResult.message}`,
            executionTimeMs: Date.now() - startTime,
            validated: true,
          };
        }
      }

      // 4. Circuit breaker check
      if (this.options.circuitBreaker) {
        if (this.circuitBreaker.isOpen(toolName)) {
          return {
            success: false,
            error: `Circuit breaker is open for tool '${toolName}'`,
            executionTimeMs: Date.now() - startTime,
            validated: true,
          };
        }
      }

      // 5. Sanitize inputs
      const sanitizedArgs = this.sanitizeInputs(args);

      // 6. Execute with timeout
      const result = await Promise.race([
        this.executeHandler(handler, sanitizedArgs),
        this.createTimeout(this.options.timeout),
      ]);

      if (result === "timeout") {
        this.circuitBreaker.recordFailure(toolName);
        return {
          success: false,
          error: `Tool execution timed out after ${this.options.timeout}ms`,
          executionTimeMs: Date.now() - startTime,
          validated: true,
        };
      }

      // 7. Record success
      if (this.options.circuitBreaker) {
        this.circuitBreaker.recordSuccess(toolName);
      }

      return {
        success: true,
        result,
        executionTimeMs: Date.now() - startTime,
        validated: true,
      };
    } catch (error) {
      // Record failure
      if (this.options.circuitBreaker) {
        this.circuitBreaker.recordFailure(toolName);
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        executionTimeMs: Date.now() - startTime,
        validated: this.options.validate,
      };
    }
  }

  /**
   * Execute handler with error handling
   */
  private async executeHandler(
    handler: ToolHandler,
    args: Record<string, unknown>
  ): Promise<unknown> {
    const result = handler(args);
    
    // Handle both sync and async handlers
    if (result instanceof Promise) {
      return await result;
    }
    
    return result;
  }

  /**
   * Create timeout promise
   */
  private createTimeout(ms: number): Promise<"timeout"> {
    return new Promise((resolve) => {
      setTimeout(() => resolve("timeout"), ms);
    });
  }

  /**
   * Sanitize inputs to prevent injection attacks
   */
  private sanitizeInputs(args: unknown): Record<string, unknown> {
    if (typeof args !== "object" || args === null) {
      return {};
    }

    const sanitized: Record<string, unknown> = {};
    const input = args as Record<string, unknown>;

    for (const [key, value] of Object.entries(input)) {
      // Remove potentially dangerous keys
      if (key.startsWith("__") || key.startsWith("$")) {
        continue;
      }

      // Sanitize string values
      if (typeof value === "string") {
        sanitized[key] = this.sanitizeString(value);
      } else if (Array.isArray(value)) {
        sanitized[key] = value.map((v) =>
          typeof v === "string" ? this.sanitizeString(v) : v
        );
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Sanitize string to prevent injection
   */
  private sanitizeString(str: string): string {
    // Remove null bytes and control characters
    return str
      .replace(/\0/g, "")
      .replace(/[\x00-\x1F\x7F]/g, "")
      .trim();
  }

  /**
   * Get registered tool names
   */
  getRegisteredTools(): string[] {
    return Array.from(this.handlers.keys());
  }

  /**
   * Check if tool is registered
   */
  hasTool(name: string): boolean {
    return this.handlers.has(name);
  }
}
