/**
 * Audit logging types
 */

/**
 * Audit log entry
 */
export interface AuditLogEntry {
  /**
   * Unique log entry ID
   */
  id: string;

  /**
   * Timestamp
   */
  timestamp: Date;

  /**
   * User ID who executed the tool
   */
  userId: string;

  /**
   * Tool name that was executed
   */
  toolName: string;

  /**
   * Tool arguments (may be redacted)
   */
  arguments: unknown;

  /**
   * Execution result (may be redacted)
   */
  result?: unknown;

  /**
   * Whether execution was successful
   */
  success: boolean;

  /**
   * Error message if failed
   */
  error?: string;

  /**
   * Execution duration in milliseconds
   */
  durationMs: number;

  /**
   * IP address of requester
   */
  ipAddress?: string;

  /**
   * User agent
   */
  userAgent?: string;

  /**
   * Additional metadata
   */
  metadata?: Record<string, unknown>;
}

/**
 * PII detection result
 */
export interface PIIDetectionResult {
  /**
   * Whether PII was detected
   */
  detected: boolean;

  /**
   * Types of PII detected
   */
  types: string[];

  /**
   * Redacted content
   */
  redactedContent: unknown;
}

/**
 * Audit log filter
 */
export interface AuditLogFilter {
  userId?: string;
  toolName?: string;
  startDate?: Date;
  endDate?: Date;
  success?: boolean;
  limit?: number;
  offset?: number;
}

