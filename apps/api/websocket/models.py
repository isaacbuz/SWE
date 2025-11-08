"""
WebSocket event and data models.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """WebSocket event types."""
    # Project events
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"

    # Agent events
    AGENT_STATUS_CHANGED = "agent.status_changed"
    AGENT_CONNECTED = "agent.connected"
    AGENT_DISCONNECTED = "agent.disconnected"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PROGRESS = "workflow.progress"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # PR events
    PR_CREATED = "pr.created"
    PR_UPDATED = "pr.updated"
    PR_CLOSED = "pr.closed"

    # Issue events
    ISSUE_CREATED = "issue.created"
    ISSUE_UPDATED = "issue.updated"
    ISSUE_CLOSED = "issue.closed"

    # AI events
    AI_SUGGESTION = "ai.suggestion"
    AI_ANALYSIS_COMPLETE = "ai.analysis_complete"

    # Connection events
    CONNECTION_ESTABLISHED = "connection.established"
    CONNECTION_ERROR = "connection.error"


class AgentStatus(str, Enum):
    """Agent availability status."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RoomType(str, Enum):
    """Room types for organizing subscriptions."""
    PROJECT = "project"
    USER = "user"
    AGENT = "agent"
    GLOBAL = "global"


class WebSocketEvent(BaseModel):
    """WebSocket event payload."""
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    source: Optional[str] = None  # Which part of the app sent this event

    class Config:
        from_attributes = True


class ProjectUpdateEvent(BaseModel):
    """Project update event data."""
    project_id: UUID
    project_name: str
    repository_url: str
    status: str
    updated_by: UUID
    changes: Dict[str, Any] = Field(default_factory=dict)


class AgentStatusEvent(BaseModel):
    """Agent status change event data."""
    agent_id: UUID
    agent_name: str
    status: AgentStatus
    availability: int = Field(0, ge=0, le=100)  # Availability percentage
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowProgressEvent(BaseModel):
    """Workflow progress event data."""
    workflow_id: UUID
    status: WorkflowStatus
    progress: int = Field(0, ge=0, le=100)
    current_step: str
    total_steps: int
    estimated_time_remaining: Optional[int] = None  # seconds
    logs: Optional[list] = None
    errors: Optional[list] = None


class PRCreatedEvent(BaseModel):
    """Pull request created event data."""
    pr_id: UUID
    project_id: UUID
    title: str
    description: Optional[str] = None
    author: str
    branch: str
    github_url: str
    status: str
    created_at: datetime


class IssueUpdateEvent(BaseModel):
    """Issue update event data."""
    issue_id: UUID
    project_id: UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: Optional[str] = None
    assigned_to: Optional[UUID] = None
    updated_at: datetime


class AISuggestionEvent(BaseModel):
    """AI suggestion event data."""
    suggestion_id: UUID
    target_type: str  # 'issue', 'pr', 'code'
    target_id: UUID
    category: str  # 'optimization', 'refactor', 'bug_fix', etc.
    title: str
    description: str
    severity: str = Field(default="info")  # 'info', 'warning', 'critical'
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    suggested_action: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConnectionEstablishedEvent(BaseModel):
    """Connection established event data."""
    connection_id: str
    user_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    protocol_version: str = "1.0"


class ConnectionErrorEvent(BaseModel):
    """Connection error event data."""
    connection_id: Optional[str] = None
    error_code: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
