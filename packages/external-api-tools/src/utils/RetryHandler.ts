/**
 * Retry Handler
 * 
 * Implements exponential backoff retry logic for API calls.
 */

export interface RetryConfig {
  /** Maximum number of retries */
  maxRetries?: number;
  
  /** Initial delay in milliseconds */
  initialDelay?: number;
  
  /** Maximum delay in milliseconds */
  maxDelay?: number;
  
  /** Backoff multiplier */
  backoffMultiplier?: number;
  
  /** Retry on these HTTP status codes */
  retryableStatusCodes?: number[];
}

export class RetryHandler {
  private config: Required<RetryConfig>;

  constructor(config: RetryConfig = {}) {
    this.config = {
      maxRetries: config.maxRetries ?? 3,
      initialDelay: config.initialDelay ?? 1000,
      maxDelay: config.maxDelay ?? 30000,
      backoffMultiplier: config.backoffMultiplier ?? 2,
      retryableStatusCodes: config.retryableStatusCodes ?? [
        429, // Too Many Requests
        500, // Internal Server Error
        502, // Bad Gateway
        503, // Service Unavailable
        504, // Gateway Timeout
      ],
    };
  }

  /**
   * Execute function with retry logic
   */
  async execute<T>(
    fn: () => Promise<T>,
    shouldRetry?: (error: unknown) => boolean
  ): Promise<T> {
    let lastError: unknown;
    let delay = this.config.initialDelay;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;

        // Check if we should retry
        if (attempt === this.config.maxRetries) {
          break; // Max retries reached
        }

        const shouldRetryError =
          shouldRetry ? shouldRetry(error) : this.isRetryableError(error);

        if (!shouldRetryError) {
          throw error; // Don't retry non-retryable errors
        }

        // Wait before retrying
        await this.sleep(delay);

        // Increase delay for next retry (exponential backoff)
        delay = Math.min(
          delay * this.config.backoffMultiplier,
          this.config.maxDelay
        );
      }
    }

    throw lastError;
  }

  /**
   * Check if error is retryable
   */
  private isRetryableError(error: unknown): boolean {
    if (error && typeof error === "object" && "status" in error) {
      const status = (error as { status: number }).status;
      return this.config.retryableStatusCodes.includes(status);
    }

    // Network errors are retryable
    if (error instanceof Error) {
      return (
        error.message.includes("ECONNRESET") ||
        error.message.includes("ETIMEDOUT") ||
        error.message.includes("ENOTFOUND")
      );
    }

    return false;
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

