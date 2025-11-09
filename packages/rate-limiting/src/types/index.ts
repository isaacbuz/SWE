/**
 * Rate limiting and quota types
 */

/**
 * Rate limit configuration
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
   * Identifier (user ID, IP, etc.)
   */
  identifier: string;
}

/**
 * Quota configuration
 */
export interface QuotaConfig {
  /**
   * Maximum cost per period
   */
  maxCost: number;

  /**
   * Period in milliseconds
   */
  periodMs: number;

  /**
   * Identifier (user ID, team ID, etc.)
   */
  identifier: string;
}

/**
 * Rate limit status
 */
export interface RateLimitStatus {
  /**
   * Whether limit is exceeded
   */
  exceeded: boolean;

  /**
   * Remaining requests in current window
   */
  remaining: number;

  /**
   * When the window resets
   */
  resetAt: Date;

  /**
   * Total requests in current window
   */
  current: number;
}

/**
 * Quota status
 */
export interface QuotaStatus {
  /**
   * Whether quota is exceeded
   */
  exceeded: boolean;

  /**
   * Remaining cost in current period
   */
  remaining: number;

  /**
   * When the period resets
   */
  resetAt: Date;

  /**
   * Current cost in period
   */
  current: number;
}

