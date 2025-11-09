"""
Agent management endpoints.
"""
from typing import List, Optional
from uuid import UUID
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter
from services.agents import agent_service


router = APIRouter(prefix="/agents", tags=["agents"])


# Enums

class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Agent type."""
    ISSUE_RESOLVER = "issue_resolver"
    PR_REVIEWER = "pr_reviewer"
    CODE_ANALYZER = "code_analyzer"
    CUSTOM = "custom"


# Request/Response Models

class AgentCreate(BaseModel):
    """Agent creation request."""
    project_id: UUID
    agent_type: AgentType
    config: dict = Field(default_factory=dict)
    auto_start: bool = True


class AgentUpdate(BaseModel):
    """Agent update request."""
    config: Optional[dict] = None
    status: Optional[AgentStatus] = None


class Agent(BaseModel):
    """Agent response model."""
    id: UUID
    project_id: UUID
    agent_type: AgentType
    status: AgentStatus
    config: dict
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class AgentList(BaseModel):
    """Agent list response."""
    items: List[Agent]
    total: int
    page: int
    page_size: int


class AgentLog(BaseModel):
    """Agent log entry."""
    timestamp: str
    level: str
    message: str
    metadata: Optional[dict] = None


class AgentLogs(BaseModel):
    """Agent logs response."""
    agent_id: UUID
    logs: List[AgentLog]


# Endpoints

@router.post(
    "",
    response_model=Agent,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent"
)
@limiter.limit("10/minute")
async def create_agent(
    agent: AgentCreate,
    current_user: CurrentUser = Depends(require_user)
) -> Agent:
    """
    Create and optionally start a new agent.

    - **project_id**: Project UUID
    - **agent_type**: Type of agent to create
    - **config**: Agent-specific configuration
    - **auto_start**: Whether to start agent immediately
    """
    agent_data = await agent_service.create_agent(
        project_id=agent.project_id,
        agent_type=agent.agent_type.value,
        config=agent.config,
        user_id=current_user.id,
        auto_start=agent.auto_start
    )
    return Agent(**agent_data)


@router.get(
    "",
    response_model=AgentList,
    summary="List agents"
)
@limiter.limit("30/minute")
async def list_agents(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    agent_type: Optional[AgentType] = Query(None, description="Filter by type"),
    status: Optional[AgentStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(require_user)
) -> AgentList:
    """
    List agents with optional filtering.

    Supports filtering by project, type, and status.
    """
    result = await agent_service.list_agents(
        user_id=current_user.id,
        project_id=project_id,
        agent_type=agent_type.value if agent_type else None,
        status_filter=status.value if status else None,
        page=page,
        page_size=page_size
    )
    return AgentList(
        items=[Agent(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get(
    "/{agent_id}",
    response_model=Agent,
    summary="Get agent by ID"
)
@limiter.limit("30/minute")
async def get_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> Agent:
    """
    Get a specific agent by ID.

    - **agent_id**: Agent UUID
    """
    agent_data = await agent_service.get_agent(agent_id, current_user.id)
    return Agent(**agent_data)


@router.patch(
    "/{agent_id}",
    response_model=Agent,
    summary="Update agent"
)
@limiter.limit("10/minute")
async def update_agent(
    agent_id: UUID,
    update: AgentUpdate,
    current_user: CurrentUser = Depends(require_user)
) -> Agent:
    """
    Update an agent's configuration or status.

    - **config**: Updated configuration
    - **status**: Updated status (admin only for certain transitions)
    """
    updates = update.dict(exclude_unset=True)
    if "status" in updates:
        updates["status"] = updates["status"].value if updates["status"] else None
    agent_data = await agent_service.update_agent(
        agent_id=agent_id,
        user_id=current_user.id,
        updates=updates
    )
    return Agent(**agent_data)


@router.post(
    "/{agent_id}/start",
    response_model=Agent,
    summary="Start agent"
)
@limiter.limit("10/minute")
async def start_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> Agent:
    """
    Start an agent execution.

    Agent must be in PENDING or FAILED status.
    """
    agent_data = await agent_service.start_agent(agent_id, current_user.id)
    return Agent(**agent_data)


@router.post(
    "/{agent_id}/cancel",
    response_model=Agent,
    summary="Cancel agent"
)
@limiter.limit("10/minute")
async def cancel_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> Agent:
    """
    Cancel a running agent.

    Agent must be in RUNNING status.
    """
    agent_data = await agent_service.cancel_agent(agent_id, current_user.id)
    return Agent(**agent_data)


@router.get(
    "/{agent_id}/logs",
    response_model=AgentLogs,
    summary="Get agent logs"
)
@limiter.limit("30/minute")
async def get_agent_logs(
    agent_id: UUID,
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of logs"),
    current_user: CurrentUser = Depends(require_user)
) -> AgentLogs:
    """
    Get logs for a specific agent.

    - **agent_id**: Agent UUID
    - **level**: Filter by log level (DEBUG, INFO, WARNING, ERROR)
    - **limit**: Maximum number of log entries to return
    """
    logs_data = await agent_service.get_agent_logs(
        agent_id=agent_id,
        user_id=current_user.id,
        level=level,
        limit=limit
    )
    return AgentLogs(**logs_data)


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent"
)
@limiter.limit("5/minute")
async def delete_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> None:
    """
    Delete an agent.

    Agent must be in COMPLETED, FAILED, or CANCELLED status.
    """
    await agent_service.delete_agent(agent_id, current_user.id)
