/**
 * Tool Executor with Schema Validation
 * 
 * Executes tools with runtime validation, rate limiting, and security features.
 */
import { z } from 'zod';
import { ToolSpec, ToolHandler, ToolExecutionResult } from './types';

export interface ExecutorOptions {
  /** Enable rate limiting */
  enableRateLimit?: boolean;
  
  /** Enable input sanitization */
  enableSanitization?: boolean;
  
  /** Enable audit logging */
  enableAuditLog?: boolean;
  
  /** Default rate limit (requests per minute) */
  defaultRateLimit?: number;
  
  /** Custom rate limiters by tool name */
  rateLimits?: Map<string, number>;
  
  /** Audit log handler */
  auditLogger?: (log: AuditLog) => void | Promise<void>;
}

export interface AuditLog {
  toolName: string;
  timestamp: Date;
  userId?: string;
  inputs: Record<string, any>;
  result: ToolExecutionResult;
  executionTimeMs: number;
}

export interface RateLimitState {
  count: number;
  resetAt: Date;
}

/**
 * Tool Executor with validation and security features
 */
export class ToolExecutor {
  private handlers: Map<string, ToolHandler> = new Map();
  private rateLimiters: Map<string, RateLimitState> = new Map();
  private options: Required<ExecutorOptions>;

  constructor(options: ExecutorOptions = {}) {
    this.options = {
      enableRateLimit: options.enableRateLimit ?? true,
      enableSanitization: options.enableSanitization ?? true,
      enableAuditLog: options.enableAuditLog ?? true,
      defaultRateLimit: options.defaultRateLimit ?? 60,
      rateLimits: options.rateLimits ?? new Map(),
      auditLogger: options.auditLogger ?? (() => {}),
    };
  }

  /**
   * Register a tool handler
   */
  register(toolName: string, handler: ToolHandler): void {
    if (this.handlers.has(toolName)) {
      throw new Error(`Tool handler for ${toolName} already registered`);
    }
    this.handlers.set(toolName, handler);
  }

  /**
   * Unregister a tool handler
   */
  unregister(toolName: string): void {
    this.handlers.delete(toolName);
    this.rateLimiters.delete(toolName);
  }

  /**
   * Check if a tool is registered
   */
  hasHandler(toolName: string): boolean {
    return this.handlers.has(toolName);
  }

  /**
   * Execute a tool with validation
   */
  async execute(
    toolSpec: ToolSpec,
    args: Record<string, any>,
    context?: {
      userId?: string;
      [key: string]: any;
    }
  ): Promise<ToolExecutionResult> {
    const startTime = Date.now();

    try {
      // 1. Check if handler exists
      if (!this.handlers.has(toolSpec.name)) {
        return {
          success: false,
          error: `Tool handler not found for ${toolSpec.name}`,
          executionTimeMs: Date.now() - startTime,
        };
      }

      // 2. Rate limiting check
      if (this.options.enableRateLimit) {
        const rateLimitCheck = this.checkRateLimit(toolSpec);
        if (!rateLimitCheck.allowed) {
          return {
            success: false,
            error: `Rate limit exceeded for ${toolSpec.name}. ${rateLimitCheck.message}`,
            executionTimeMs: Date.now() - startTime,
          };
        }
      }

      // 3. Validate inputs against schema
      const validationResult = this.validateInputs(toolSpec.jsonSchema, args);
      if (!validationResult.success) {
        return {
          success: false,
          error: `Input validation failed: ${validationResult.error}`,
          executionTimeMs: Date.now() - startTime,
        };
      }

      // 4. Sanitize inputs
      const sanitizedArgs = this.options.enableSanitization
        ? this.sanitizeInputs(args)
        : args;

      // 5. Execute handler
      const handler = this.handlers.get(toolSpec.name)!;
      const result = await handler(sanitizedArgs);

      const executionTime = Date.now() - startTime;

      // 6. Audit logging
      if (this.options.enableAuditLog) {
        await this.logAudit({
          toolName: toolSpec.name,
          timestamp: new Date(),
          userId: context?.userId,
          inputs: sanitizedArgs,
          result: {
            success: true,
            result,
            executionTimeMs: executionTime,
          },
          executionTimeMs: executionTime,
        });
      }

      return {
        success: true,
        result,
        executionTimeMs: executionTime,
      };
    } catch (error) {
      const executionTime = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : String(error);

      // Audit log error
      if (this.options.enableAuditLog) {
        await this.logAudit({
          toolName: toolSpec.name,
          timestamp: new Date(),
          userId: context?.userId,
          inputs: args,
          result: {
            success: false,
            error: errorMessage,
            executionTimeMs: executionTime,
          },
          executionTimeMs: executionTime,
        });
      }

      return {
        success: false,
        error: errorMessage,
        executionTimeMs: executionTime,
      };
    }
  }

  /**
   * Validate inputs against JSON Schema using Zod
   */
  private validateInputs(
    schema: Record<string, any>,
    inputs: Record<string, any>
  ): { success: boolean; error?: string } {
    try {
      // Convert JSON Schema to Zod schema
      const zodSchema = this.jsonSchemaToZod(schema);
      
      // Validate
      zodSchema.parse(inputs);
      
      return { success: true };
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors = error.errors.map(e => `${e.path.join('.')}: ${e.message}`);
        return {
          success: false,
          error: errors.join('; '),
        };
      }
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Convert JSON Schema to Zod schema (simplified)
   */
  private jsonSchemaToZod(schema: Record<string, any>): z.ZodObject<any> {
    if (schema.type !== 'object' || !schema.properties) {
      // Fallback to any object if schema is not an object type
      return z.object({}).passthrough();
    }

    const shape: Record<string, z.ZodTypeAny> = {};

    for (const [key, prop] of Object.entries(schema.properties)) {
      const propSchema = prop as Record<string, any>;
      let zodType: z.ZodTypeAny;

      switch (propSchema.type) {
        case 'string':
          zodType = z.string();
          if (propSchema.format === 'email') {
            zodType = z.string().email();
          }
          break;
        case 'number':
        case 'integer':
          zodType = z.number();
          if (propSchema.minimum !== undefined) {
            zodType = (zodType as z.ZodNumber).min(propSchema.minimum);
          }
          if (propSchema.maximum !== undefined) {
            zodType = (zodType as z.ZodNumber).max(propSchema.maximum);
          }
          break;
        case 'boolean':
          zodType = z.boolean();
          break;
        case 'array':
          zodType = z.array(z.any());
          break;
        default:
          zodType = z.any();
      }

      if (Array.isArray(schema.required) && schema.required.includes(key)) {
        shape[key] = zodType;
      } else {
        shape[key] = zodType.optional();
      }
    }

    return z.object(shape);
  }

  /**
   * Sanitize inputs to prevent injection attacks
   */
  private sanitizeInputs(inputs: Record<string, any>): Record<string, any> {
    const sanitized: Record<string, any> = {};

    for (const [key, value] of Object.entries(inputs)) {
      if (typeof value === 'string') {
        // Remove potentially dangerous characters
        sanitized[key] = value
          .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
          .replace(/javascript:/gi, '')
          .replace(/on\w+\s*=/gi, '');
      } else if (typeof value === 'object' && value !== null) {
        // Recursively sanitize nested objects
        sanitized[key] = this.sanitizeInputs(value as Record<string, any>);
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Check rate limit for a tool
   */
  private checkRateLimit(toolSpec: ToolSpec): {
    allowed: boolean;
    message?: string;
  } {
    const toolName = toolSpec.name;
    const limit = this.options.rateLimits.get(toolName) ?? 
                  toolSpec.rateLimit ?? 
                  this.options.defaultRateLimit;

    const now = new Date();
    const state = this.rateLimiters.get(toolName);

    if (!state || now > state.resetAt) {
      // Reset or initialize
      this.rateLimiters.set(toolName, {
        count: 1,
        resetAt: new Date(now.getTime() + 60 * 1000), // Reset in 1 minute
      });
      return { allowed: true };
    }

    if (state.count >= limit) {
      const secondsUntilReset = Math.ceil(
        (state.resetAt.getTime() - now.getTime()) / 1000
      );
      return {
        allowed: false,
        message: `Limit: ${limit}/min. Resets in ${secondsUntilReset}s`,
      };
    }

    state.count++;
    return { allowed: true };
  }

  /**
   * Log audit event
   */
  private async logAudit(log: AuditLog): Promise<void> {
    try {
      await this.options.auditLogger(log);
    } catch (error) {
      // Don't fail execution if audit logging fails
      console.error('Audit logging failed:', error);
    }
  }

  /**
   * Get executor statistics
   */
  getStats(): {
    registeredTools: number;
    rateLimiters: number;
  } {
    return {
      registeredTools: this.handlers.size,
      rateLimiters: this.rateLimiters.size,
    };
  }

  /**
   * Clear rate limiters (useful for testing)
   */
  clearRateLimiters(): void {
    this.rateLimiters.clear();
  }
}

