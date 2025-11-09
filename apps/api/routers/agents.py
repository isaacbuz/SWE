"""
Agent management endpoints.
"""
from typing import List, Optional
from uuid import UUID
from enum import Enum
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter
from db.connection import get_db_pool
from db.agents import AgentsService
from db.users import UsersService
from db.projects import ProjectsService


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


# Dependencies
async def get_agents_service() -> AgentsService:
    """Get agents database service"""
    pool = await get_db_pool()
    return AgentsService(pool)


async def get_projects_service() -> ProjectsService:
    """Get projects database service"""
    pool = await get_db_pool()
    from db.projects import ProjectsService
    return ProjectsService(pool)


async def get_users_service() -> UsersService:
    """Get users database service"""
    pool = await get_db_pool()
    from db.users import UsersService
    return UsersService(pool)


# Helper function to convert agent data to response model
def agent_data_to_model(agent_data: dict) -> Agent:
    """Convert database agent data to response model"""
    # Extract result and error from config or last execution
    result = agent_data.get("config", {}).get("last_result")
    error = agent_data.get("config", {}).get("last_error")
    
    # Map database status to router status
    db_status = agent_data.get("status", "pending")
    status_map = {
        "idle": "pending",
        "running": "running",
        "completed": "completed",
        "failed": "failed",
        "cancelled": "cancelled"
    }
    router_status = status_map.get(db_status, "pending")
    
    return Agent(
        id=agent_data["agent_id"],
        project_id=agent_data["project_id"],
        agent_type=AgentType(agent_data["agent_type"]),
        status=AgentStatus(router_status),
        config=agent_data.get("config", {}),
        result=result,
        error=error,
        created_at=agent_data["created_at"].isoformat(),
        updated_at=agent_data["updated_at"].isoformat(),
        started_at=agent_data["last_execution_at"].isoformat() if agent_data.get("last_execution_at") else None,
        completed_at=agent_data["last_execution_at"].isoformat() if agent_data.get("last_execution_at") and router_status in ["completed", "failed", "cancelled"] else None
    )


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
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> Agent:
    """
    Create and optionally start a new agent.

    - **project_id**: Project UUID
    - **agent_type**: Type of agent to create
    - **config**: Agent-specific configuration
    - **auto_start**: Whether to start agent immediately
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify project exists and user has access
    project = await projects_service.get_project(agent.project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {agent.project_id} not found"
        )
    
    # Extract model info from config or use defaults
    model_provider = agent.config.get("model_provider", "anthropic")
    model_name = agent.config.get("model_name", "claude-3-5-sonnet-20241022")
    name = agent.config.get("name", f"{agent.agent_type.value} Agent")
    
    # Create agent in database
    try:
        agent_data = await agents_service.create_agent(
            project_id=agent.project_id,
            name=name,
            agent_type=agent.agent_type.value,
            model_provider=model_provider,
            model_name=model_name,
            config=agent.config,
            created_by_user_id=user_id
        )
        
        # TODO: If auto_start, queue agent for execution via agent registry
        
        return agent_data_to_model(agent_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


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
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    users_service: UsersService = Depends(get_users_service)
) -> AgentList:
    """
    List agents with optional filtering.

    Supports filtering by project, type, and status.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Map router status to database status
    db_status = None
    if status:
        status_map = {
            "pending": "idle",
            "running": "running",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled"
        }
        db_status = status_map.get(status.value)
    
    # Query agents from database
    agents_data, total = await agents_service.list_agents(
        user_id=user_id,
        project_id=project_id,
        agent_type=agent_type.value if agent_type else None,
        status=db_status,
        page=page,
        page_size=page_size
    )
    
    # Convert to response models
    items = [agent_data_to_model(agent) for agent in agents_data]
    
    return AgentList(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{agent_id}",
    response_model=Agent,
    summary="Get agent by ID"
)
@limiter.limit("30/minute")
async def get_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    users_service: UsersService = Depends(get_users_service)
) -> Agent:
    """
    Get a specific agent by ID.

    - **agent_id**: Agent UUID
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Load agent from database
    agent_data = await agents_service.get_agent(agent_id, user_id)
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    return agent_data_to_model(agent_data)


@router.patch(
    "/{agent_id}",
    response_model=Agent,
    summary="Update agent"
)
@limiter.limit("10/minute")
async def update_agent(
    agent_id: UUID,
    update: AgentUpdate,
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    users_service: UsersService = Depends(get_users_service)
) -> Agent:
    """
    Update an agent's configuration or status.

    - **config**: Updated configuration
    - **status**: Updated status (admin only for certain transitions)
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Map router status to database status
    db_status = None
    if update.status:
        status_map = {
            "pending": "idle",
            "running": "running",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled"
        }
        db_status = status_map.get(update.status.value)
    
    # Update agent in database
    agent_data = await agents_service.update_agent(
        agent_id=agent_id,
        user_id=user_id,
        config=update.config,
        status=db_status
    )
    
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # TODO: If status changed, handle agent lifecycle via agent registry
    
    return agent_data_to_model(agent_data)


@router.post(
    "/{agent_id}/start",
    response_model=Agent,
    summary="Start agent"
)
@limiter.limit("10/minute")
async def start_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    users_service: UsersService = Depends(get_users_service)
) -> Agent:
    """
    Start an agent execution.

    Agent must be in PENDING or FAILED status.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify agent exists
    agent_data = await agents_service.get_agent(agent_id, user_id)
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # TODO: Verify agent can be started (not already running)
    # TODO: Queue agent for execution via agent registry
    
    # Update agent status to running
    updated_agent = await agents_service.update_agent(
        agent_id=agent_id,
        user_id=user_id,
        status="running"
    )
    
    return agent_data_to_model(updated_agent)


@router.post(
    "/{agent_id}/cancel",
    response_model=Agent,
    summary="Cancel agent"
)
@limiter.limit("10/minute")
async def cancel_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    users_service: UsersService = Depends(get_users_service)
) -> Agent:
    """
    Cancel a running agent.

    Agent must be in RUNNING status.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify agent exists and is running
    agent_data = await agents_service.get_agent(agent_id, user_id)
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    if agent_data.get("status") != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent {agent_id} is not running"
        )
    
    # TODO: Send cancellation signal to agent via agent registry
    
    # Update agent status to cancelled
    updated_agent = await agents_service.update_agent(
        agent_id=agent_id,
        user_id=user_id,
        status="cancelled"
    )
    
    return agent_data_to_model(updated_agent)


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
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    users_service: UsersService = Depends(get_users_service)
) -> AgentLogs:
    """
    Get logs for a specific agent.

    - **agent_id**: Agent UUID
    - **level**: Filter by log level (DEBUG, INFO, WARNING, ERROR)
    - **limit**: Maximum number of log entries to return
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify agent exists
    agent_data = await agents_service.get_agent(agent_id, user_id)
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # Fetch logs from database
    logs_data = await agents_service.get_agent_logs(agent_id, user_id, limit)
    
    # Convert to log models
    logs = [
        AgentLog(
            timestamp=log["started_at"].isoformat() if log.get("started_at") else datetime.utcnow().isoformat(),
            level="error" if log.get("error_message") else "info",
            message=log.get("error_message") or f"Execution {log.get('status', 'unknown')}",
            metadata={
                "execution_id": str(log["execution_id"]),
                "status": log.get("status"),
                "tokens": {
                    "input": log.get("input_tokens", 0),
                    "output": log.get("output_tokens", 0)
                },
                "cost": float(log.get("cost_usd", 0)) if log.get("cost_usd") else None
            }
        )
        for log in logs_data
    ]
    
    # Apply level filter if provided
    if level:
        logs = [log for log in logs if log.level.lower() == level.lower()]
    
    return AgentLogs(
        agent_id=agent_id,
        logs=logs
    )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent"
)
@limiter.limit("5/minute")
async def delete_agent(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    agents_service: AgentsService = Depends(get_agents_service),
    users_service: UsersService = Depends(get_users_service)
) -> None:
    """
    Delete an agent.

    Agent must be in COMPLETED, FAILED, or CANCELLED status.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify agent exists and can be deleted
    agent_data = await agents_service.get_agent(agent_id, user_id)
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # Check if agent can be deleted (not running)
    if agent_data.get("status") == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete running agent {agent_id}. Cancel it first."
        )
    
    # TODO: Cancel any running executions via agent registry
    
    # Delete agent
    deleted = await agents_service.delete_agent(agent_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
