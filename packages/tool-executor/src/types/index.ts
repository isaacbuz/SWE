/**
 * Tool execution types and interfaces
 */

/**
 * ToolHandler - Function that executes a tool
 */
export type ToolHandler = (args: unknown) => Promise<unknown>;

/**
 * ToolResult - Result of tool execution
 */
export interface ToolResult {
  /**
   * Tool name that was executed
   */
  toolName: string;

  /**
   * Execution result (success or error)
   */
  result: unknown;

  /**
   * Execution duration in milliseconds
   */
  durationMs: number;

  /**
   * Whether execution was successful
   */
  success: boolean;

  /**
   * Error message if execution failed
   */
  error?: string;

  /**
   * Validation errors if input validation failed
   */
  validationErrors?: string[];

  /**
   * Metadata about execution
   */
  metadata?: {
    timestamp: Date;
    [key: string]: unknown;
  };
}

/**
 * ToolExecutionOptions - Options for tool execution
 */
export interface ToolExecutionOptions {
  /**
   * Whether to validate inputs before execution
   * @default true
   */
  validateInputs?: boolean;

  /**
   * Timeout in milliseconds
   * @default 30000 (30 seconds)
   */
  timeoutMs?: number;

  /**
   * Whether to retry on failure
   * @default false
   */
  retryOnFailure?: boolean;

  /**
   * Maximum retry attempts
   * @default 3
   */
  maxRetries?: number;

  /**
   * Additional metadata to include in result
   */
  metadata?: Record<string, unknown>;
}

/**
 * RateLimitConfig - Rate limiting configuration for a tool
 */
export interface RateLimitConfig {
  /**
   * Maximum requests per time window
   */
  maxRequests: number;

  /**
   * Time window in milliseconds
   */
  windowMs: number;

  /**
   * Identifier for rate limiting (user ID, IP, etc.)
   */
  identifier?: string;
}

/**
 * CircuitBreakerState - Circuit breaker state for a tool
 */
export interface CircuitBreakerState {
  /**
   * Current state: 'closed' | 'open' | 'half-open'
   */
  state: 'closed' | 'open' | 'half-open';

  /**
   * Number of consecutive failures
   */
  failureCount: number;

  /**
   * Timestamp when circuit was opened
   */
  openedAt?: Date;

  /**
   * Timestamp when circuit can be retried (half-open)
   */
  nextRetryAt?: Date;
}

