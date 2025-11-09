"""
Observability Package

Provides logging, metrics, tracing, and audit logging capabilities.
"""

from .logging import StructuredLogger, get_logger, set_correlation_id
from .metrics import MetricsCollector, get_metrics_collector
from .tracing import TracingService, get_tracing_service
from .audit import AuditLogger, AuditLogEntry, AuditLogStatus, get_audit_logger, set_audit_logger

__all__ = [
    "StructuredLogger",
    "get_logger",
    "set_correlation_id",
    "MetricsCollector",
    "get_metrics_collector",
    "TracingService",
    "get_tracing_service",
    "AuditLogger",
    "AuditLogEntry",
    "AuditLogStatus",
    "get_audit_logger",
    "set_audit_logger",
]

