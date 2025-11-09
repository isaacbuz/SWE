/**
 * Audit Logging Service
 * 
 * Provides comprehensive audit logging for user actions, system events, and compliance.
 */
import { StructuredLogger } from '@ai-company/observability';

/**
 * Audit Event Types
 */
export enum AuditEventType {
  USER_LOGIN = 'user.login',
  USER_LOGOUT = 'user.logout',
  USER_CREATE = 'user.create',
  USER_UPDATE = 'user.update',
  USER_DELETE = 'user.delete',
  
  PROJECT_CREATE = 'project.create',
  PROJECT_UPDATE = 'project.update',
  PROJECT_DELETE = 'project.delete',
  
  AGENT_CREATE = 'agent.create',
  AGENT_UPDATE = 'agent.update',
  AGENT_DELETE = 'agent.delete',
  AGENT_EXECUTE = 'agent.execute',
  
  TOOL_EXECUTE = 'tool.execute',
  TOOL_CREATE = 'tool.create',
  TOOL_UPDATE = 'tool.update',
  TOOL_DELETE = 'tool.delete',
  
  API_ACCESS = 'api.access',
  API_ERROR = 'api.error',
  
  PERMISSION_GRANT = 'permission.grant',
  PERMISSION_REVOKE = 'permission.revoke',
  
  CONFIG_CHANGE = 'config.change',
  SECURITY_EVENT = 'security.event',
}

/**
 * Audit Log Entry
 */
export interface AuditLogEntry {
  id?: string;
  timestamp: Date;
  eventType: AuditEventType | string;
  userId?: string;
  userEmail?: string;
  resourceType?: string;
  resourceId?: string;
  action: string;
  result: 'success' | 'failure' | 'pending';
  ipAddress?: string;
  userAgent?: string;
  requestId?: string;
  metadata?: Record<string, any>;
  changes?: {
    before?: Record<string, any>;
    after?: Record<string, any>;
  };
}

/**
 * Audit Log Query Filters
 */
export interface AuditLogFilters {
  userId?: string;
  eventType?: string;
  resourceType?: string;
  resourceId?: string;
  startDate?: Date;
  endDate?: Date;
  result?: 'success' | 'failure' | 'pending';
  limit?: number;
  offset?: number;
}

/**
 * Audit Logger Configuration
 */
export interface AuditLoggerConfig {
  serviceName: string;
  enableDatabase?: boolean;
  enableFile?: boolean;
  enableStructuredLogging?: boolean;
  logFile?: string;
  structuredLogger?: StructuredLogger;
}

/**
 * Audit Logger
 * 
 * Provides comprehensive audit logging with database and file storage.
 */
export class AuditLogger {
  private config: AuditLoggerConfig;
  private logs: AuditLogEntry[] = [];
  private structuredLogger?: StructuredLogger;

  constructor(config: AuditLoggerConfig) {
    this.config = {
      serviceName: config.serviceName,
      enableDatabase: config.enableDatabase ?? true,
      enableFile: config.enableFile ?? false,
      enableStructuredLogging: config.enableStructuredLogging ?? true,
      logFile: config.logFile || 'logs/audit.log',
      structuredLogger: config.structuredLogger,
    };

    this.structuredLogger = this.config.structuredLogger;
  }

  /**
   * Log audit event
   */
  async log(entry: Omit<AuditLogEntry, 'id' | 'timestamp'>): Promise<AuditLogEntry> {
    const auditEntry: AuditLogEntry = {
      ...entry,
      id: this.generateId(),
      timestamp: new Date(),
    };

    // Store in memory (for now, will be replaced with database)
    this.logs.push(auditEntry);

    // Log to structured logger if enabled
    if (this.config.enableStructuredLogging && this.structuredLogger) {
      this.structuredLogger.info('Audit event', {
        audit: true,
        eventType: auditEntry.eventType,
        userId: auditEntry.userId,
        resourceType: auditEntry.resourceType,
        resourceId: auditEntry.resourceId,
        action: auditEntry.action,
        result: auditEntry.result,
        requestId: auditEntry.requestId,
      });
    }

    // TODO: Store in database if enabled
    // TODO: Write to file if enabled

    return auditEntry;
  }

  /**
   * Log user action
   */
  async logUserAction(
    userId: string,
    userEmail: string,
    action: string,
    resourceType: string,
    resourceId: string,
    result: 'success' | 'failure' = 'success',
    metadata?: Record<string, any>
  ): Promise<AuditLogEntry> {
    return this.log({
      eventType: AuditEventType.API_ACCESS,
      userId,
      userEmail,
      resourceType,
      resourceId,
      action,
      result,
      metadata,
    });
  }

  /**
   * Log tool execution
   */
  async logToolExecution(
    userId: string,
    toolName: string,
    result: 'success' | 'failure',
    metadata?: Record<string, any>
  ): Promise<AuditLogEntry> {
    return this.log({
      eventType: AuditEventType.TOOL_EXECUTE,
      userId,
      resourceType: 'tool',
      resourceId: toolName,
      action: 'execute',
      result,
      metadata,
    });
  }

  /**
   * Log permission change
   */
  async logPermissionChange(
    userId: string,
    targetUserId: string,
    permission: string,
    action: 'grant' | 'revoke',
    result: 'success' | 'failure' = 'success'
  ): Promise<AuditLogEntry> {
    return this.log({
      eventType: action === 'grant' ? AuditEventType.PERMISSION_GRANT : AuditEventType.PERMISSION_REVOKE,
      userId,
      resourceType: 'permission',
      resourceId: targetUserId,
      action: `${action}_${permission}`,
      result,
      metadata: { permission, targetUserId },
    });
  }

  /**
   * Log security event
   */
  async logSecurityEvent(
    eventType: string,
    severity: 'low' | 'medium' | 'high' | 'critical',
    description: string,
    metadata?: Record<string, any>
  ): Promise<AuditLogEntry> {
    return this.log({
      eventType: AuditEventType.SECURITY_EVENT,
      action: eventType,
      result: severity === 'critical' || severity === 'high' ? 'failure' : 'success',
      metadata: {
        severity,
        description,
        ...metadata,
      },
    });
  }

  /**
   * Query audit logs
   */
  async query(filters: AuditLogFilters): Promise<AuditLogEntry[]> {
    let results = [...this.logs];

    // Filter by userId
    if (filters.userId) {
      results = results.filter(entry => entry.userId === filters.userId);
    }

    // Filter by eventType
    if (filters.eventType) {
      results = results.filter(entry => entry.eventType === filters.eventType);
    }

    // Filter by resourceType
    if (filters.resourceType) {
      results = results.filter(entry => entry.resourceType === filters.resourceType);
    }

    // Filter by resourceId
    if (filters.resourceId) {
      results = results.filter(entry => entry.resourceId === filters.resourceId);
    }

    // Filter by result
    if (filters.result) {
      results = results.filter(entry => entry.result === filters.result);
    }

    // Filter by date range
    if (filters.startDate) {
      results = results.filter(entry => entry.timestamp >= filters.startDate!);
    }
    if (filters.endDate) {
      results = results.filter(entry => entry.timestamp <= filters.endDate!);
    }

    // Sort by timestamp (newest first)
    results.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    // Apply pagination
    const offset = filters.offset || 0;
    const limit = filters.limit || 100;
    results = results.slice(offset, offset + limit);

    // TODO: Query from database if enabled

    return results;
  }

  /**
   * Get audit log by ID
   */
  async getById(id: string): Promise<AuditLogEntry | null> {
    const entry = this.logs.find(log => log.id === id);
    return entry || null;
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get all logs (for testing/debugging)
   */
  getAllLogs(): AuditLogEntry[] {
    return [...this.logs];
  }

  /**
   * Clear logs (for testing)
   */
  clear(): void {
    this.logs = [];
  }
}

/**
 * Create audit logger instance
 */
export function createAuditLogger(config: AuditLoggerConfig): AuditLogger {
  return new AuditLogger(config);
}

