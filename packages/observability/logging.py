"""
Structured Logging System
JSON log format with correlation IDs and context injection
"""

import logging
import json
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import traceback
from contextvars import ContextVar
from uuid import uuid4

from opentelemetry import trace


# Context variables for correlation
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
project_id_var: ContextVar[Optional[str]] = ContextVar("project_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging

    Features:
    - JSON output format
    - Correlation ID injection
    - Trace context injection
    - Custom field support
    - Exception formatting
    """

    def __init__(
        self,
        service_name: str = "swe-platform",
        environment: str = "production",
        include_trace: bool = True,
    ):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }

        # Add correlation IDs
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        project_id = project_id_var.get()
        if project_id:
            log_data["project_id"] = project_id

        # Add trace context
        if self.include_trace:
            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                log_data["trace_id"] = format(ctx.trace_id, "032x")
                log_data["span_id"] = format(ctx.span_id, "016x")
                log_data["trace_flags"] = ctx.trace_flags

        # Add file and line information
        log_data["file"] = record.pathname
        log_data["line"] = record.lineno
        log_data["function"] = record.funcName

        # Add extra fields from record
        if hasattr(record, "extra_fields") and record.extra_fields:
            log_data.update(record.extra_fields)

        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logging manager

    Features:
    - JSON log format
    - Multiple handlers (console, file, cloud)
    - Correlation ID management
    - Context injection
    - Log aggregation support
    """

    def __init__(
        self,
        name: str = "swe-platform",
        level: str = "INFO",
        service_name: str = "swe-platform",
        environment: str = "production",
        log_file: Optional[str] = None,
    ):
        self.name = name
        self.level = getattr(logging, level.upper())
        self.service_name = service_name
        self.environment = environment
        self.log_file = log_file

        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        self.logger.propagate = False

        # Remove existing handlers
        self.logger.handlers.clear()

    def setup(self) -> None:
        """Initialize structured logging"""
        # JSON formatter
        json_formatter = JSONFormatter(
            service_name=self.service_name,
            environment=self.environment,
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(self.level)
        self.logger.addHandler(console_handler)

        # File handler
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(json_formatter)
            file_handler.setLevel(self.level)
            self.logger.addHandler(file_handler)

        print(f"✓ Structured logging initialized for {self.service_name}")

    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """Set correlation ID for request tracking"""
        cid = correlation_id or str(uuid4())
        correlation_id_var.set(cid)
        return cid

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        return correlation_id_var.get()

    def set_user_id(self, user_id: str) -> None:
        """Set user ID for request tracking"""
        user_id_var.set(user_id)

    def set_project_id(self, project_id: str) -> None:
        """Set project ID for request tracking"""
        project_id_var.set(project_id)

    def clear_context(self) -> None:
        """Clear all context variables"""
        correlation_id_var.set(None)
        user_id_var.set(None)
        project_id_var.set(None)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)

    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs) -> None:
        """Internal logging method"""
        # Create log record with extra fields
        extra = {"extra_fields": kwargs}
        self.logger.log(level, message, exc_info=exc_info, extra=extra)

    def log_agent_activity(
        self,
        agent_name: str,
        action: str,
        status: str,
        **kwargs
    ) -> None:
        """Log agent activity"""
        self.info(
            f"Agent {agent_name}: {action}",
            agent_name=agent_name,
            action=action,
            status=status,
            **kwargs
        )

    def log_llm_call(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        duration_ms: float,
        **kwargs
    ) -> None:
        """Log LLM API call"""
        self.info(
            f"LLM call to {provider}/{model}",
            llm_provider=provider,
            llm_model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            duration_ms=duration_ms,
            **kwargs
        )

    def log_quality_gate(
        self,
        gate_type: str,
        passed: bool,
        project_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log quality gate execution"""
        level = logging.INFO if passed else logging.WARNING
        self._log(
            level,
            f"Quality gate '{gate_type}': {'PASSED' if passed else 'FAILED'}",
            gate_type=gate_type,
            passed=passed,
            project_id=project_id,
            details=details or {},
        )

    def log_database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        rows_affected: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log database operation"""
        self.debug(
            f"Database {operation} on {table}",
            db_operation=operation,
            db_table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            **kwargs
        )

    def log_cache_operation(
        self,
        operation: str,
        key: str,
        hit: bool,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Log cache operation"""
        self.debug(
            f"Cache {operation}: {'HIT' if hit else 'MISS'}",
            cache_operation=operation,
            cache_key=key,
            cache_hit=hit,
            duration_ms=duration_ms,
        )

    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        severity: str = "info",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log security-related event"""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        level = level_map.get(severity.lower(), logging.INFO)

        self._log(
            level,
            f"Security event: {event_type}",
            security_event_type=event_type,
            security_severity=severity,
            user_id=user_id,
            details=details or {},
        )

    def log_cost_tracking(
        self,
        cost_type: str,
        amount: float,
        currency: str = "USD",
        project_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log cost tracking information"""
        self.info(
            f"Cost tracked: {cost_type}",
            cost_type=cost_type,
            amount=amount,
            currency=currency,
            project_id=project_id,
            **kwargs
        )


# Global logger instance
structured_logger = StructuredLogger(
    name=os.getenv("SERVICE_NAME", "swe-platform"),
    level=os.getenv("LOG_LEVEL", "INFO"),
    service_name=os.getenv("SERVICE_NAME", "swe-platform"),
    environment=os.getenv("ENVIRONMENT", "production"),
    log_file=os.getenv("LOG_FILE"),
)


# Convenience functions
def get_logger(name: Optional[str] = None) -> StructuredLogger:
    """Get logger instance"""
    if name:
        return StructuredLogger(name=name)
    return structured_logger


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID"""
    return structured_logger.set_correlation_id(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID"""
    return structured_logger.get_correlation_id()


def set_user_context(user_id: str, project_id: Optional[str] = None) -> None:
    """Set user context"""
    structured_logger.set_user_id(user_id)
    if project_id:
        structured_logger.set_project_id(project_id)


def clear_context() -> None:
    """Clear logging context"""
    structured_logger.clear_context()
