/**
 * Circuit Breaker
 * 
 * Implements circuit breaker pattern for fault tolerance.
 */

export interface CircuitBreakerConfig {
  /** Number of failures before opening circuit */
  failureThreshold: number;
  
  /** Time window in milliseconds for failure counting */
  windowMs: number;
  
  /** Time in milliseconds before attempting to close circuit */
  resetTimeoutMs: number;
}

export class CircuitBreaker {
  private config: CircuitBreakerConfig;
  private states: Map<string, {
    state: "closed" | "open" | "half-open";
    failures: number;
    lastFailureTime: number;
    openedAt: number;
  }> = new Map();

  constructor(config: Partial<CircuitBreakerConfig> = {}) {
    this.config = {
      failureThreshold: config.failureThreshold ?? 5,
      windowMs: config.windowMs ?? 60000, // 1 minute
      resetTimeoutMs: config.resetTimeoutMs ?? 30000, // 30 seconds
    };
  }

  /**
   * Check if circuit is open
   */
  isOpen(toolName: string): boolean {
    const state = this.getState(toolName);
    
    if (state.state === "open") {
      // Check if reset timeout has passed
      const now = Date.now();
      if (now - state.openedAt >= this.config.resetTimeoutMs) {
        // Move to half-open
        state.state = "half-open";
        state.failures = 0;
        return false;
      }
      return true;
    }

    return false;
  }

  /**
   * Record successful execution
   */
  recordSuccess(toolName: string): void {
    const state = this.getState(toolName);
    
    if (state.state === "half-open") {
      // Close circuit on success
      state.state = "closed";
      state.failures = 0;
    } else if (state.state === "closed") {
      // Reset failure count on success
      const now = Date.now();
      if (now - state.lastFailureTime > this.config.windowMs) {
        state.failures = 0;
      }
    }
  }

  /**
   * Record failed execution
   */
  recordFailure(toolName: string): void {
    const state = this.getState(toolName);
    const now = Date.now();

    // Reset failures if window has passed
    if (now - state.lastFailureTime > this.config.windowMs) {
      state.failures = 0;
    }

    state.failures += 1;
    state.lastFailureTime = now;

    // Open circuit if threshold exceeded
    if (state.failures >= this.config.failureThreshold) {
      state.state = "open";
      state.openedAt = now;
    }
  }

  /**
   * Get or create state for tool
   */
  private getState(toolName: string) {
    if (!this.states.has(toolName)) {
      this.states.set(toolName, {
        state: "closed",
        failures: 0,
        lastFailureTime: 0,
        openedAt: 0,
      });
    }
    return this.states.get(toolName)!;
  }

  /**
   * Reset circuit breaker for a tool
   */
  reset(toolName: string): void {
    this.states.delete(toolName);
  }

  /**
   * Get circuit breaker state
   */
  getStateInfo(toolName: string) {
    return this.getState(toolName);
  }
}

