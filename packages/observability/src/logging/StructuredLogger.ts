/**
 * Structured Logging
 * 
 * Provides structured JSON logging with OpenTelemetry integration.
 */
import winston from 'winston';
import { trace, context, SpanStatusCode } from '@opentelemetry/api';

/**
 * Log Levels
 */
export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug',
}

/**
 * Structured Log Entry
 */
export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  service?: string;
  version?: string;
  environment?: string;
  traceId?: string;
  spanId?: string;
  [key: string]: any;
}

/**
 * Structured Logger Configuration
 */
export interface LoggerConfig {
  serviceName: string;
  serviceVersion?: string;
  environment?: string;
  logLevel?: LogLevel;
  enableConsole?: boolean;
  enableFile?: boolean;
  logFile?: string;
  enableOpenTelemetry?: boolean;
}

/**
 * Structured Logger
 * 
 * Provides structured JSON logging with OpenTelemetry trace context.
 */
export class StructuredLogger {
  private logger: winston.Logger;
  private config: LoggerConfig;
  private serviceName: string;

  constructor(config: LoggerConfig) {
    this.config = {
      serviceName: config.serviceName,
      serviceVersion: config.serviceVersion || '1.0.0',
      environment: config.environment || process.env.NODE_ENV || 'development',
      logLevel: config.logLevel || LogLevel.INFO,
      enableConsole: config.enableConsole ?? true,
      enableFile: config.enableFile ?? false,
      logFile: config.logFile || 'logs/app.log',
      enableOpenTelemetry: config.enableOpenTelemetry ?? true,
    };

    this.serviceName = this.config.serviceName;

    // Create Winston logger
    const transports: winston.transport[] = [];

    // Console transport with JSON format
    if (this.config.enableConsole) {
      transports.push(
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.json()
          ),
        })
      );
    }

    // File transport
    if (this.config.enableFile) {
      transports.push(
        new winston.transports.File({
          filename: this.config.logFile,
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.json()
          ),
        })
      );
    }

    this.logger = winston.createLogger({
      level: this.config.logLevel,
      defaultMeta: {
        service: this.config.serviceName,
        version: this.config.serviceVersion,
        environment: this.config.environment,
      },
      transports,
    });
  }

  /**
   * Get current trace context
   */
  private getTraceContext(): { traceId?: string; spanId?: string } {
    if (!this.config.enableOpenTelemetry) {
      return {};
    }

    try {
      const activeSpan = trace.getActiveSpan();
      if (!activeSpan) {
        return {};
      }

      const spanContext = activeSpan.spanContext();
      return {
        traceId: spanContext.traceId,
        spanId: spanContext.spanId,
      };
    } catch (error) {
      return {};
    }
  }

  /**
   * Create log entry with context
   */
  private createLogEntry(
    level: LogLevel,
    message: string,
    meta?: Record<string, any>
  ): LogEntry {
    const traceContext = this.getTraceContext();
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      service: this.serviceName,
      version: this.config.serviceVersion,
      environment: this.config.environment,
      ...traceContext,
      ...meta,
    };
  }

  /**
   * Log error
   */
  error(message: string, meta?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.ERROR, message, meta);
    this.logger.error(entry);

    // Record error in OpenTelemetry span if available
    if (this.config.enableOpenTelemetry) {
      try {
        const activeSpan = trace.getActiveSpan();
        if (activeSpan) {
          activeSpan.recordException(new Error(message));
          activeSpan.setStatus({
            code: SpanStatusCode.ERROR,
            message,
          });
        }
      } catch (error) {
        // Ignore OpenTelemetry errors
      }
    }
  }

  /**
   * Log warning
   */
  warn(message: string, meta?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.WARN, message, meta);
    this.logger.warn(entry);
  }

  /**
   * Log info
   */
  info(message: string, meta?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.INFO, message, meta);
    this.logger.info(entry);
  }

  /**
   * Log debug
   */
  debug(message: string, meta?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.DEBUG, message, meta);
    this.logger.debug(entry);
  }

  /**
   * Log with custom level
   */
  log(level: LogLevel, message: string, meta?: Record<string, any>): void {
    const entry = this.createLogEntry(level, message, meta);
    this.logger.log(level, entry);
  }

  /**
   * Create child logger with additional context
   */
  child(meta: Record<string, any>): StructuredLogger {
    const childLogger = new StructuredLogger(this.config);
    childLogger.logger = this.logger.child(meta);
    return childLogger;
  }
}

/**
 * Create default logger instance
 */
export function createLogger(config: LoggerConfig): StructuredLogger {
  return new StructuredLogger(config);
}

