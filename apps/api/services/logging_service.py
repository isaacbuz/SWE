"""
Structured Logging Service

Provides structured JSON logging with OpenTelemetry integration.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from opentelemetry import trace


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""

    def __init__(self, service_name: str, service_version: str, environment: str):
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Get trace context from OpenTelemetry
        trace_id = None
        span_id = None
        
        try:
            span = trace.get_current_span()
            if span:
                span_context = span.get_span_context()
                if span_context.is_valid:
                    trace_id = format(span_context.trace_id, '032x')
                    span_id = format(span_context.span_id, '016x')
        except Exception:
            pass

        # Build log entry
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname.lower(),
            'message': record.getMessage(),
            'service': self.service_name,
            'version': self.service_version,
            'environment': self.environment,
        }

        # Add trace context if available
        if trace_id:
            log_entry['traceId'] = trace_id
        if span_id:
            log_entry['spanId'] = span_id

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)

        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                'service', 'version', 'environment'
            ]:
                if not key.startswith('_'):
                    log_entry[key] = value

        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """Structured logger with OpenTelemetry integration"""

    def __init__(
        self,
        service_name: str,
        service_version: str = '1.0.0',
        environment: str = 'development',
        log_level: str = 'INFO',
        enable_console: bool = True,
        enable_file: bool = False,
        log_file: str = 'logs/app.log'
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

        # Create logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.handlers.clear()

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                StructuredFormatter(service_name, service_version, environment)
            )
            self.logger.addHandler(console_handler)

        # File handler
        if enable_file:
            import os
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                StructuredFormatter(service_name, service_version, environment)
            )
            self.logger.addHandler(file_handler)

    def error(self, message: str, **kwargs):
        """Log error"""
        self._log(logging.ERROR, message, **kwargs)
        # Record error in OpenTelemetry span
        try:
            span = trace.get_current_span()
            if span:
                span.record_exception(Exception(message))
                span.set_status(trace.Status(trace.StatusCode.ERROR, message))
        except Exception:
            pass

    def warn(self, message: str, **kwargs):
        """Log warning"""
        self._log(logging.WARNING, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info"""
        self._log(logging.INFO, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug"""
        self._log(logging.DEBUG, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method"""
        extra = kwargs.copy()
        self.logger.log(level, message, extra=extra)

    def get_logger(self) -> logging.Logger:
        """Get underlying logger"""
        return self.logger


# Singleton instance
_logger_instance: Optional[StructuredLogger] = None


def get_logger(
    service_name: str = 'swe-platform-api',
    service_version: str = '1.0.0',
    environment: Optional[str] = None,
    log_level: str = 'INFO'
) -> StructuredLogger:
    """Get or create logger instance"""
    global _logger_instance
    
    if _logger_instance is None:
        env = environment or 'development'
        _logger_instance = StructuredLogger(
            service_name=service_name,
            service_version=service_version,
            environment=env,
            log_level=log_level,
            enable_console=True,
            enable_file=env == 'production',
            log_file='logs/app.log'
        )
    
    return _logger_instance

