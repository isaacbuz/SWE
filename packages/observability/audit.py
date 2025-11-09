"""
Tool Execution Audit Logging

Provides comprehensive audit logging for all tool executions to support
compliance, debugging, and security analysis.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, asdict
from enum import Enum

import asyncpg
from opentelemetry import trace


class AuditLogStatus(str, Enum):
    """Audit log entry status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class AuditLogEntry:
    """Audit log entry for tool execution"""
    # Identifiers
    log_id: str
    timestamp: datetime
    
    # Actor information
    user_id: Optional[int] = None
    agent_id: Optional[str] = None
    service_name: Optional[str] = None
    
    # Event information
    event_type: str = "tool_execution"
    event_action: str = "execute"
    
    # Resource information
    resource_type: str = "tool"
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Tool execution details
    tool_name: Optional[str] = None
    operation: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None  # Sanitized
    outputs: Optional[Any] = None  # Sanitized summary
    success: bool = True
    error_message: Optional[str] = None
    
    # Provider and cost
    provider_id: Optional[str] = None
    cost: Optional[float] = None
    duration_ms: Optional[int] = None
    
    # Request context
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    # Status
    status: AuditLogStatus = AuditLogStatus.SUCCESS
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PIIDetector:
    """Detects and redacts PII in log entries"""
    
    # Patterns for common PII
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "api_key": r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?",
        "bearer_token": r"Bearer\s+([A-Za-z0-9_\-\.]+)",
    }
    
    @classmethod
    def detect_and_redact(cls, data: Any) -> Any:
        """
        Recursively detect and redact PII from data
        
        Args:
            data: Data to scan for PII
            
        Returns:
            Data with PII redacted
        """
        if isinstance(data, str):
            return cls._redact_string(data)
        elif isinstance(data, dict):
            return {k: cls.detect_and_redact(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.detect_and_redact(item) for item in data]
        else:
            return data
    
    @classmethod
    def _redact_string(cls, text: str) -> str:
        """Redact PII from a string"""
        result = text
        
        # Redact emails
        result = re.sub(cls.PATTERNS["email"], "[EMAIL_REDACTED]", result)
        
        # Redact SSNs
        result = re.sub(cls.PATTERNS["ssn"], "[SSN_REDACTED]", result)
        
        # Redact credit cards
        result = re.sub(cls.PATTERNS["credit_card"], "[CARD_REDACTED]", result)
        
        # Redact API keys and tokens
        result = re.sub(cls.PATTERNS["api_key"], r"\1: [REDACTED]", result, flags=re.IGNORECASE)
        result = re.sub(cls.PATTERNS["bearer_token"], "Bearer [REDACTED]", result)
        
        return result


class AuditLogger:
    """
    Audit logger for tool executions
    
    Features:
    - Comprehensive tool execution logging
    - PII detection and redaction
    - Database persistence
    - Log retention policies
    - Search and filter capabilities
    """
    
    def __init__(
        self,
        db_pool: Optional[asyncpg.Pool] = None,
        enable_pii_detection: bool = True,
        log_to_console: bool = True,
    ):
        """
        Initialize audit logger
        
        Args:
            db_pool: Database connection pool for persistence
            enable_pii_detection: Enable PII detection and redaction
            log_to_console: Also log to console (structured logging)
        """
        self.db_pool = db_pool
        self.enable_pii_detection = enable_pii_detection
        self.logger = logging.getLogger("audit")
        self.log_to_console = log_to_console
        
        # PII detector
        self.pii_detector = PIIDetector() if enable_pii_detection else None
    
    async def log_tool_execution(
        self,
        tool_name: str,
        operation: str,
        inputs: Dict[str, Any],
        outputs: Any,
        success: bool,
        user_id: Optional[int] = None,
        agent_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        cost: Optional[float] = None,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log a tool execution
        
        Args:
            tool_name: Name of the tool executed
            operation: Operation performed
            inputs: Tool inputs (will be sanitized)
            outputs: Tool outputs (will be sanitized)
            success: Whether execution succeeded
            user_id: User ID if executed by user
            agent_id: Agent ID if executed by agent
            provider_id: LLM provider used
            cost: Cost incurred
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
            request_id: Request correlation ID
            session_id: Session ID
            metadata: Additional metadata
            
        Returns:
            Log entry ID
        """
        log_id = str(uuid4())
        timestamp = datetime.utcnow()
        
        # Sanitize inputs and outputs
        sanitized_inputs = self._sanitize_data(inputs)
        sanitized_outputs = self._sanitize_data(outputs)
        
        # Create log entry
        entry = AuditLogEntry(
            log_id=log_id,
            timestamp=timestamp,
            user_id=user_id,
            agent_id=agent_id,
            service_name="tool-executor",
            event_type="tool_execution",
            event_action="execute",
            resource_type="tool",
            resource_id=tool_name,
            resource_name=tool_name,
            tool_name=tool_name,
            operation=operation,
            inputs=sanitized_inputs,
            outputs=sanitized_outputs,
            success=success,
            error_message=error_message,
            provider_id=provider_id,
            cost=cost,
            duration_ms=duration_ms,
            request_id=request_id,
            session_id=session_id,
            metadata=metadata or {},
            status=AuditLogStatus.SUCCESS if success else AuditLogStatus.FAILURE,
        )
        
        # Add trace context
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            entry.metadata["trace_id"] = format(ctx.trace_id, "032x")
            entry.metadata["span_id"] = format(ctx.span_id, "016x")
        
        # Log to console if enabled
        if self.log_to_console:
            self._log_to_console(entry)
        
        # Persist to database if pool available
        if self.db_pool:
            await self._persist_to_db(entry)
        
        return log_id
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data by redacting PII and secrets"""
        if self.pii_detector:
            return self.pii_detector.detect_and_redact(data)
        return data
    
    def _log_to_console(self, entry: AuditLogEntry):
        """Log entry to console as structured JSON"""
        log_data = {
            "audit_log": True,
            "log_id": entry.log_id,
            "timestamp": entry.timestamp.isoformat(),
            "tool_name": entry.tool_name,
            "operation": entry.operation,
            "success": entry.success,
            "user_id": entry.user_id,
            "agent_id": entry.agent_id,
            "provider_id": entry.provider_id,
            "cost": entry.cost,
            "duration_ms": entry.duration_ms,
            "request_id": entry.request_id,
        }
        
        if entry.error_message:
            log_data["error"] = entry.error_message
        
        self.logger.info(json.dumps(log_data, default=str))
    
    async def _persist_to_db(self, entry: AuditLogEntry):
        """Persist audit log entry to database"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_logs (
                        log_id, user_id, agent_id, service_name,
                        event_type, event_action,
                        resource_type, resource_id, resource_name,
                        old_values, new_values,
                        status, error_message,
                        request_id, session_id,
                        metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    """,
                    entry.log_id,
                    entry.user_id,
                    entry.agent_id,
                    entry.service_name,
                    entry.event_type,
                    entry.event_action,
                    entry.resource_type,
                    entry.resource_id,
                    entry.resource_name,
                    json.dumps(entry.inputs) if entry.inputs else None,
                    json.dumps(entry.outputs) if entry.outputs else None,
                    entry.status.value,
                    entry.error_message,
                    entry.request_id,
                    entry.session_id,
                    json.dumps(entry.metadata),
                )
        except Exception as e:
            self.logger.error(f"Failed to persist audit log: {e}", exc_info=True)
    
    async def query_logs(
        self,
        user_id: Optional[int] = None,
        agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs with filters
        
        Args:
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            tool_name: Filter by tool name
            start_time: Start time filter
            end_time: End time filter
            success_only: Filter by success status
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        if not self.db_pool:
            return []
        
        try:
            conditions = []
            params = []
            param_idx = 1
            
            if user_id:
                conditions.append(f"user_id = ${param_idx}")
                params.append(user_id)
                param_idx += 1
            
            if agent_id:
                conditions.append(f"agent_id = ${param_idx}")
                params.append(agent_id)
                param_idx += 1
            
            if tool_name:
                conditions.append(f"resource_id = ${param_idx}")
                params.append(tool_name)
                param_idx += 1
            
            if start_time:
                conditions.append(f"created_at >= ${param_idx}")
                params.append(start_time)
                param_idx += 1
            
            if end_time:
                conditions.append(f"created_at <= ${param_idx}")
                params.append(end_time)
                param_idx += 1
            
            if success_only is not None:
                status = AuditLogStatus.SUCCESS.value if success_only else AuditLogStatus.FAILURE.value
                conditions.append(f"status = ${param_idx}")
                params.append(status)
                param_idx += 1
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.append(limit)
            
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT * FROM audit_logs
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${param_idx}
                    """,
                    *params,
                )
            
            return [dict(row) for row in rows]
        
        except Exception as e:
            self.logger.error(f"Failed to query audit logs: {e}", exc_info=True)
            return []


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> Optional[AuditLogger]:
    """Get global audit logger instance"""
    return _audit_logger


def set_audit_logger(logger: AuditLogger):
    """Set global audit logger instance"""
    global _audit_logger
    _audit_logger = logger

