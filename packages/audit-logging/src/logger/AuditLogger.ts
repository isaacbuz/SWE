import { AuditLogEntry, AuditLogFilter, PIIDetectionResult } from '../types';
import { PIIDetector } from '../utils/piidetector';

/**
 * Audit Logger Configuration
 */
export interface AuditLoggerConfig {
  /**
   * Whether to detect and redact PII
   * @default true
   */
  detectPII?: boolean;

  /**
   * Whether to include arguments in logs
   * @default true
   */
  includeArguments?: boolean;

  /**
   * Whether to include results in logs
   * @default false
   */
  includeResults?: boolean;

  /**
   * Log retention period in days
   * @default 90
   */
  retentionDays?: number;

  /**
   * Custom storage backend
   */
  storage?: AuditLogStorage;
}

/**
 * Audit log storage interface
 */
export interface AuditLogStorage {
  save(entry: AuditLogEntry): Promise<void>;
  query(filter: AuditLogFilter): Promise<AuditLogEntry[]>;
  deleteOlderThan(date: Date): Promise<number>;
}

/**
 * In-memory storage implementation
 */
export class InMemoryAuditLogStorage implements AuditLogStorage {
  private logs: AuditLogEntry[] = [];

  async save(entry: AuditLogEntry): Promise<void> {
    this.logs.push(entry);
  }

  async query(filter: AuditLogFilter): Promise<AuditLogEntry[]> {
    let results = [...this.logs];

    if (filter.userId) {
      results = results.filter((log) => log.userId === filter.userId);
    }

    if (filter.toolName) {
      results = results.filter((log) => log.toolName === filter.toolName);
    }

    if (filter.startDate) {
      results = results.filter((log) => log.timestamp >= filter.startDate!);
    }

    if (filter.endDate) {
      results = results.filter((log) => log.timestamp <= filter.endDate!);
    }

    if (filter.success !== undefined) {
      results = results.filter((log) => log.success === filter.success);
    }

    // Sort by timestamp descending
    results.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    // Apply pagination
    const offset = filter.offset || 0;
    const limit = filter.limit || 100;

    return results.slice(offset, offset + limit);
  }

  async deleteOlderThan(date: Date): Promise<number> {
    const before = this.logs.length;
    this.logs = this.logs.filter((log) => log.timestamp >= date);
    return before - this.logs.length;
  }
}

/**
 * Audit Logger
 * 
 * Provides comprehensive audit logging for tool executions with
 * PII detection, redaction, and retention policies.
 */
export class AuditLogger {
  private config: Required<AuditLoggerConfig>;
  private storage: AuditLogStorage;
  private piiDetector: PIIDetector;

  constructor(config: AuditLoggerConfig = {}) {
    this.config = {
      detectPII: config.detectPII ?? true,
      includeArguments: config.includeArguments ?? true,
      includeResults: config.includeResults ?? false,
      retentionDays: config.retentionDays ?? 90,
      storage: config.storage || new InMemoryAuditLogStorage(),
    };

    this.storage = this.config.storage;
    this.piiDetector = new PIIDetector();
  }

  /**
   * Log tool execution
   */
  async logExecution(
    userId: string,
    toolName: string,
    args: unknown,
    result: unknown,
    success: boolean,
    durationMs: number,
    error?: string,
    metadata?: {
      ipAddress?: string;
      userAgent?: string;
      [key: string]: unknown;
    }
  ): Promise<string> {
    const entryId = this.generateId();

    // Prepare arguments (with PII redaction if enabled)
    let logArgs = args;
    let piiDetection: PIIDetectionResult | undefined;

    if (this.config.includeArguments) {
      if (this.config.detectPII) {
        piiDetection = this.piiDetector.detectAndRedact(args);
        logArgs = piiDetection.redactedContent;
      }
    } else {
      logArgs = { redacted: true };
    }

    // Prepare result (with PII redaction if enabled)
    let logResult: unknown = undefined;

    if (this.config.includeResults && result !== undefined) {
      if (this.config.detectPII) {
        const resultDetection = this.piiDetector.detectAndRedact(result);
        logResult = resultDetection.redactedContent;
        if (resultDetection.detected) {
          // Merge PII types
          piiDetection = {
            detected: true,
            types: Array.from(
              new Set([
                ...(piiDetection?.types || []),
                ...resultDetection.types,
              ])
            ),
            redactedContent: logResult,
          };
        }
      } else {
        logResult = result;
      }
    }

    // Build audit log entry
    const entry: AuditLogEntry = {
      id: entryId,
      timestamp: new Date(),
      userId,
      toolName,
      arguments: logArgs,
      result: logResult,
      success,
      error: error ? this.sanitizeError(error) : undefined,
      durationMs,
      ipAddress: metadata?.ipAddress,
      userAgent: metadata?.userAgent,
      metadata: {
        ...metadata,
        piiDetected: piiDetection?.detected || false,
        piiTypes: piiDetection?.types || [],
      },
    };

    // Save to storage
    await this.storage.save(entry);

    return entryId;
  }

  /**
   * Query audit logs
   */
  async queryLogs(filter: AuditLogFilter): Promise<AuditLogEntry[]> {
    return this.storage.query(filter);
  }

  /**
   * Clean up old logs based on retention policy
   */
  async cleanup(): Promise<number> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.config.retentionDays);

    return this.storage.deleteOlderThan(cutoffDate);
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
  }

  /**
   * Sanitize error messages (remove stack traces, etc.)
   */
  private sanitizeError(error: string): string {
    // Remove stack traces
    const lines = error.split('\n');
    const firstLine = lines[0];
    
    // Keep only first line (error message)
    return firstLine;
  }
}

