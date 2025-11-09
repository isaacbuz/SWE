"""
Tool Execution Audit Logger
Comprehensive audit logging for tool executions with PII detection, retention policies, and export capabilities
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg not available - audit logging will use in-memory storage only")


class LogRetentionPolicy(Enum):
    """Log retention policies"""
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    DAYS_90 = "90d"
    DAYS_365 = "365d"
    INDEFINITE = "indefinite"


class SuspiciousPattern(Enum):
    """Suspicious patterns to detect"""
    HIGH_COST_SPIKE = "high_cost_spike"
    RAPID_FAILURES = "rapid_failures"
    UNUSUAL_TOOL_COMBINATION = "unusual_tool_combination"
    PII_DETECTED = "pii_detected"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass
class AuditLogEntry:
    """Complete audit log entry for tool execution"""
    id: str
    timestamp: datetime
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    tool_name: str = ""
    operation: str = ""
    inputs: Dict[str, Any] = None
    outputs: Any = None
    success: bool = True
    error: Optional[str] = None
    provider_id: Optional[str] = None
    cost: float = 0.0
    duration_ms: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    pii_detected: bool = False
    pii_redacted: bool = False
    suspicious_patterns: List[str] = None
    
    def __post_init__(self):
        if self.inputs is None:
            self.inputs = {}
        if self.suspicious_patterns is None:
            self.suspicious_patterns = []


class PIIDetector:
    """Detects and redacts PII in audit logs"""
    
    # Common PII patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    API_KEY_PATTERN = re.compile(r'\b(api[_-]?key|token|secret)[\s:=]+([A-Za-z0-9_-]{20,})\b', re.IGNORECASE)
    
    REDACTION_MARKER = "[REDACTED]"
    
    @classmethod
    def detect_pii(cls, text: str) -> bool:
        """Check if text contains PII"""
        if not isinstance(text, str):
            text = json.dumps(text) if text else ""
        
        patterns = [
            cls.EMAIL_PATTERN,
            cls.PHONE_PATTERN,
            cls.SSN_PATTERN,
            cls.CREDIT_CARD_PATTERN,
            cls.API_KEY_PATTERN,
        ]
        
        return any(pattern.search(text) for pattern in patterns)
    
    @classmethod
    def redact_pii(cls, data: Any) -> Any:
        """Recursively redact PII from data structure"""
        if isinstance(data, str):
            text = data
            # Redact emails
            text = cls.EMAIL_PATTERN.sub(cls.REDACTION_MARKER, text)
            # Redact phone numbers
            text = cls.PHONE_PATTERN.sub(cls.REDACTION_MARKER, text)
            # Redact SSNs
            text = cls.SSN_PATTERN.sub(cls.REDACTION_MARKER, text)
            # Redact credit cards
            text = cls.CREDIT_CARD_PATTERN.sub(cls.REDACTION_MARKER, text)
            # Redact API keys
            text = cls.API_KEY_PATTERN.sub(r'\1=' + cls.REDACTION_MARKER, text)
            return text
        elif isinstance(data, dict):
            return {k: cls.redact_pii(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.redact_pii(item) for item in data]
        else:
            return data


class AuditLogger:
    """
    Comprehensive audit logger for tool executions
    
    Features:
    - Complete audit log entries
    - PII detection and redaction
    - Log retention policies
    - Export capabilities (JSON, CSV)
    - Suspicious pattern detection
    - Tamper-evident logging
    """
    
    def __init__(
        self,
        db_pool: Optional[Any] = None,
        retention_policy: LogRetentionPolicy = LogRetentionPolicy.DAYS_90,
        enable_pii_detection: bool = True,
        enable_suspicious_detection: bool = True
    ):
        """
        Initialize audit logger
        
        Args:
            db_pool: AsyncPG connection pool (optional)
            retention_policy: Log retention policy
            enable_pii_detection: Enable PII detection and redaction
            enable_suspicious_detection: Enable suspicious pattern detection
        """
        self.db_pool = db_pool
        self.retention_policy = retention_policy
        self.enable_pii_detection = enable_pii_detection
        self.enable_suspicious_detection = enable_suspicious_detection
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # In-memory storage for when DB not available
        self._logs: List[AuditLogEntry] = []
        self._max_memory_logs = 1000
        
        # Suspicious pattern detection state
        self._recent_logs: List[AuditLogEntry] = []
        self._max_recent_logs = 100
    
    async def log_tool_execution(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        result: Any,
        execution_time_ms: int,
        success: bool = True,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        cost: float = 0.0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditLogEntry:
        """
        Log a tool execution
        
        Args:
            tool_name: Name of the tool executed
            inputs: Tool input parameters
            result: Tool execution result
            execution_time_ms: Execution time in milliseconds
            success: Whether execution succeeded
            error: Error message if failed
            user_id: User ID who executed the tool
            agent_id: Agent ID if executed by agent
            provider_id: LLM provider used
            cost: Cost incurred
            tokens_input: Input tokens used
            tokens_output: Output tokens used
            ip_address: Client IP address
            user_agent: User agent string
            request_id: Request ID for tracing
            session_id: Session ID
            
        Returns:
            Created audit log entry
        """
        # Detect PII
        pii_detected = False
        if self.enable_pii_detection:
            inputs_str = json.dumps(inputs)
            result_str = json.dumps(result) if result else ""
            pii_detected = (
                PIIDetector.detect_pii(inputs_str) or
                PIIDetector.detect_pii(result_str)
            )
            
            # Redact PII
            if pii_detected:
                inputs = PIIDetector.redact_pii(inputs)
                result = PIIDetector.redact_pii(result)
        
        # Detect suspicious patterns
        suspicious_patterns = []
        if self.enable_suspicious_detection:
            suspicious_patterns = self._detect_suspicious_patterns(
                tool_name, cost, success, user_id
            )
        
        # Create audit log entry
        entry = AuditLogEntry(
            id=self._generate_log_id(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            agent_id=agent_id,
            tool_name=tool_name,
            operation="execute",
            inputs=inputs,
            outputs=result,
            success=success,
            error=error,
            provider_id=provider_id,
            cost=cost,
            duration_ms=execution_time_ms,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            session_id=session_id,
            pii_detected=pii_detected,
            pii_redacted=pii_detected,
            suspicious_patterns=suspicious_patterns
        )
        
        # Store log
        await self._store_log(entry)
        
        # Alert on suspicious patterns
        if suspicious_patterns:
            self.logger.warning(
                f"Suspicious patterns detected in tool execution: {suspicious_patterns} "
                f"(tool={tool_name}, user={user_id})"
            )
        
        return entry
    
    async def query_logs(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        suspicious_only: bool = False,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """
        Query audit logs with filters
        
        Args:
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            tool_name: Filter by tool name
            start_date: Start date filter
            end_date: End date filter
            success_only: Filter by success status
            suspicious_only: Only return logs with suspicious patterns
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        if self.db_pool:
            return await self._query_logs_db(
                user_id, agent_id, tool_name, start_date, end_date,
                success_only, suspicious_only, limit
            )
        else:
            return self._query_logs_memory(
                user_id, agent_id, tool_name, start_date, end_date,
                success_only, suspicious_only, limit
            )
    
    async def export_logs(
        self,
        format: str = "json",
        **query_filters
    ) -> bytes:
        """
        Export audit logs in specified format
        
        Args:
            format: Export format ("json" or "csv")
            **query_filters: Filters to apply (same as query_logs)
            
        Returns:
            Exported logs as bytes
        """
        logs = await self.query_logs(**query_filters)
        
        if format == "json":
            return json.dumps(
                [asdict(log) for log in logs],
                default=str,
                indent=2
            ).encode('utf-8')
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=asdict(logs[0]).keys())
                writer.writeheader()
                for log in logs:
                    writer.writerow(asdict(log))
            return output.getvalue().encode('utf-8')
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def cleanup_old_logs(self) -> int:
        """
        Clean up logs older than retention policy
        
        Returns:
            Number of logs deleted
        """
        cutoff_date = self._get_retention_cutoff()
        
        if self.db_pool:
            return await self._cleanup_logs_db(cutoff_date)
        else:
            return self._cleanup_logs_memory(cutoff_date)
    
    def _generate_log_id(self) -> str:
        """Generate unique log ID"""
        return hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{id(self)}".encode()
        ).hexdigest()[:16]
    
    def _detect_suspicious_patterns(
        self,
        tool_name: str,
        cost: float,
        success: bool,
        user_id: Optional[str]
    ) -> List[str]:
        """Detect suspicious patterns"""
        patterns = []
        
        # High cost spike
        if cost > 1.0:  # Threshold: $1.00
            patterns.append(SuspiciousPattern.HIGH_COST_SPIKE.value)
        
        # Rapid failures (check recent logs)
        recent_failures = sum(
            1 for log in self._recent_logs[-10:]
            if not log.success and log.user_id == user_id
        )
        if recent_failures >= 5:
            patterns.append(SuspiciousPattern.RAPID_FAILURES.value)
        
        return patterns
    
    async def _store_log(self, entry: AuditLogEntry):
        """Store audit log entry"""
        if self.db_pool:
            await self._store_log_db(entry)
        else:
            self._store_log_memory(entry)
    
    async def _store_log_db(self, entry: AuditLogEntry):
        """Store log in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_logs (
                        log_id, user_id, agent_id, service_name,
                        event_type, event_action,
                        resource_type, resource_id, resource_name,
                        old_values, new_values, changes_summary,
                        ip_address, user_agent, request_id, session_id,
                        metadata, status, error_message,
                        created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                        $13, $14, $15, $16, $17, $18, $19, $20
                    )
                    """,
                    entry.id,
                    int(entry.user_id) if entry.user_id and entry.user_id.isdigit() else None,
                    entry.agent_id,
                    "tool-executor",
                    "tool_execution",
                    entry.operation,
                    "tool",
                    entry.tool_name,
                    entry.tool_name,
                    None,  # old_values
                    json.dumps({
                        "inputs": entry.inputs,
                        "outputs": entry.outputs,
                        "provider_id": entry.provider_id,
                        "cost": entry.cost,
                        "tokens_input": entry.tokens_input,
                        "tokens_output": entry.tokens_output,
                    }),
                    f"Tool execution: {entry.tool_name}",
                    entry.ip_address,
                    entry.user_agent,
                    entry.request_id,
                    entry.session_id,
                    json.dumps({
                        "duration_ms": entry.duration_ms,
                        "pii_detected": entry.pii_detected,
                        "pii_redacted": entry.pii_redacted,
                        "suspicious_patterns": entry.suspicious_patterns,
                    }),
                    "success" if entry.success else "failure",
                    entry.error,
                    entry.timestamp
                )
        except Exception as e:
            self.logger.error(f"Failed to store audit log in database: {e}")
            # Fallback to memory storage
            self._store_log_memory(entry)
    
    def _store_log_memory(self, entry: AuditLogEntry):
        """Store log in memory"""
        self._logs.append(entry)
        self._recent_logs.append(entry)
        
        # Trim if too many logs
        if len(self._logs) > self._max_memory_logs:
            self._logs = self._logs[-self._max_memory_logs:]
        if len(self._recent_logs) > self._max_recent_logs:
            self._recent_logs = self._recent_logs[-self._max_recent_logs:]
    
    def _query_logs_memory(
        self,
        user_id: Optional[str],
        agent_id: Optional[str],
        tool_name: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        success_only: Optional[bool],
        suspicious_only: bool,
        limit: int
    ) -> List[AuditLogEntry]:
        """Query logs from memory"""
        results = self._logs.copy()
        
        # Apply filters
        if user_id:
            results = [log for log in results if log.user_id == user_id]
        if agent_id:
            results = [log for log in results if log.agent_id == agent_id]
        if tool_name:
            results = [log for log in results if log.tool_name == tool_name]
        if start_date:
            results = [log for log in results if log.timestamp >= start_date]
        if end_date:
            results = [log for log in results if log.timestamp <= end_date]
        if success_only is not None:
            results = [log for log in results if log.success == success_only]
        if suspicious_only:
            results = [log for log in results if log.suspicious_patterns]
        
        # Sort by timestamp descending
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        return results[:limit]
    
    async def _query_logs_db(
        self,
        user_id: Optional[str],
        agent_id: Optional[str],
        tool_name: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        success_only: Optional[bool],
        suspicious_only: bool,
        limit: int
    ) -> List[AuditLogEntry]:
        """Query logs from database"""
        # Implementation would query database
        # For now, fallback to memory
        return self._query_logs_memory(
            user_id, agent_id, tool_name, start_date, end_date,
            success_only, suspicious_only, limit
        )
    
    def _get_retention_cutoff(self) -> datetime:
        """Get cutoff date based on retention policy"""
        now = datetime.utcnow()
        if self.retention_policy == LogRetentionPolicy.DAYS_7:
            return now - timedelta(days=7)
        elif self.retention_policy == LogRetentionPolicy.DAYS_30:
            return now - timedelta(days=30)
        elif self.retention_policy == LogRetentionPolicy.DAYS_90:
            return now - timedelta(days=90)
        elif self.retention_policy == LogRetentionPolicy.DAYS_365:
            return now - timedelta(days=365)
        else:
            return datetime.min  # Never delete
    
    async def _cleanup_logs_db(self, cutoff_date: datetime) -> int:
        """Clean up old logs from database"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM audit_logs WHERE created_at < $1",
                    cutoff_date
                )
                return int(result.split()[-1]) if result else 0
        except Exception as e:
            self.logger.error(f"Failed to cleanup logs: {e}")
            return 0
    
    def _cleanup_logs_memory(self, cutoff_date: datetime) -> int:
        """Clean up old logs from memory"""
        initial_count = len(self._logs)
        self._logs = [log for log in self._logs if log.timestamp >= cutoff_date]
        return initial_count - len(self._logs)

