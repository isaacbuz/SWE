"""
Issue management endpoints.
"""
from typing import List, Optional
from uuid import UUID
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter
from db.connection import get_db_pool
from db.issues import IssuesService
from db.users import UsersService
from db.projects import ProjectsService


router = APIRouter(prefix="/issues", tags=["issues"])


# Enums

class IssuePriority(str, Enum):
    """Issue priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, Enum):
    """Issue resolution status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# Request/Response Models

class IssueCreate(BaseModel):
    """Issue creation request."""
    project_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    github_issue_url: Optional[str] = None
    priority: IssuePriority = IssuePriority.MEDIUM
    labels: List[str] = Field(default_factory=list)


class IssueUpdate(BaseModel):
    """Issue update request."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[IssuePriority] = None
    status: Optional[IssueStatus] = None
    labels: Optional[List[str]] = None


class Issue(BaseModel):
    """Issue response model."""
    id: UUID
    project_id: UUID
    title: str
    description: str
    github_issue_url: Optional[str]
    github_issue_number: Optional[int]
    priority: IssuePriority
    status: IssueStatus
    labels: List[str]
    assigned_agent_id: Optional[UUID]
    resolution_pr_url: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]

    class Config:
        from_attributes = True


class IssueList(BaseModel):
    """Issue list response."""
    items: List[Issue]
    total: int
    page: int
    page_size: int


class IssueStats(BaseModel):
    """Issue statistics."""
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    by_priority: dict


# Dependencies
async def get_issues_service() -> IssuesService:
    """Get issues database service"""
    pool = await get_db_pool()
    return IssuesService(pool)


async def get_projects_service() -> ProjectsService:
    """Get projects database service"""
    pool = await get_db_pool()
    return ProjectsService(pool)


async def get_users_service() -> UsersService:
    """Get users database service"""
    pool = await get_db_pool()
    return UsersService(pool)


# Endpoints

@router.post(
    "",
    response_model=Issue,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new issue"
)
@limiter.limit("10/minute")
async def create_issue(
    issue: IssueCreate,
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> Issue:
    """
    Create a new issue for a project.

    - **project_id**: Project UUID
    - **title**: Issue title
    - **description**: Detailed description
    - **github_issue_url**: Optional GitHub issue URL
    - **priority**: Issue priority (default: medium)
    - **labels**: Optional list of labels
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify project exists and user has access
    project = await projects_service.get_project(issue.project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {issue.project_id} not found"
        )
    
    # TODO: If github_issue_url provided, fetch issue details from GitHub API
    
    # Create issue in database
    try:
        issue_data = await issues_service.create_issue(
            project_id=issue.project_id,
            title=issue.title,
            description=issue.description,
            github_issue_url=issue.github_issue_url,
            priority=issue.priority.value,
            labels=issue.labels,
            created_by_user_id=user_id
        )
        
        # TODO: Optionally trigger agent to analyze issue
        
        return Issue(
            id=issue_data["task_id"],
            project_id=issue_data["project_id"],
            title=issue_data["title"],
            description=issue_data["description"],
            github_issue_url=issue_data.get("github_url"),
            github_issue_number=issue_data.get("github_issue_number"),
            priority=IssuePriority(issue_data["priority"]),
            status=IssueStatus(issue_data["status"]),
            labels=issue_data.get("labels", []),
            assigned_agent_id=issue_data.get("assigned_to_agent_id"),
            resolution_pr_url=None,
            created_at=issue_data["created_at"].isoformat(),
            updated_at=issue_data["updated_at"].isoformat(),
            resolved_at=issue_data["completed_at"].isoformat() if issue_data.get("completed_at") else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create issue: {str(e)}"
        )


@router.get(
    "",
    response_model=IssueList,
    summary="List issues"
)
@limiter.limit("30/minute")
async def list_issues(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    status: Optional[IssueStatus] = Query(None, description="Filter by status"),
    priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
    labels: Optional[List[str]] = Query(None, description="Filter by labels"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    users_service: UsersService = Depends(get_users_service)
) -> IssueList:
    """
    List issues with optional filtering.

    Supports filtering by project, status, priority, and labels.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query issues from database
    issues_data, total = await issues_service.list_issues(
        user_id=user_id,
        project_id=project_id,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        labels=labels,
        page=page,
        page_size=page_size
    )
    
    # Convert to response models
    items = [
        Issue(
            id=issue["task_id"],
            project_id=issue["project_id"],
            title=issue["title"],
            description=issue["description"],
            github_issue_url=issue.get("github_url"),
            github_issue_number=issue.get("github_issue_number"),
            priority=IssuePriority(issue["priority"]),
            status=IssueStatus(issue["status"]),
            labels=issue.get("labels", []),
            assigned_agent_id=issue.get("assigned_to_agent_id"),
            resolution_pr_url=None,  # Would need to extract from metadata
            created_at=issue["created_at"].isoformat(),
            updated_at=issue["updated_at"].isoformat(),
            resolved_at=issue["completed_at"].isoformat() if issue.get("completed_at") else None
        )
        for issue in issues_data
    ]
    
    return IssueList(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/stats",
    response_model=IssueStats,
    summary="Get issue statistics"
)
@limiter.limit("30/minute")
async def get_issue_stats(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    users_service: UsersService = Depends(get_users_service)
) -> IssueStats:
    """
    Get aggregated issue statistics.

    - **project_id**: Optional project filter
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query issue statistics
    stats = await issues_service.get_issue_stats(user_id, project_id)
    
    return IssueStats(
        total=stats.get("total", 0),
        open=stats.get("open", 0),
        in_progress=stats.get("in_progress", 0),
        resolved=stats.get("resolved", 0),
        closed=stats.get("closed", 0),
        by_priority=stats.get("by_priority", {}) or {}
    )


@router.get(
    "/{issue_id}",
    response_model=Issue,
    summary="Get issue by ID"
)
@limiter.limit("30/minute")
async def get_issue(
    issue_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    users_service: UsersService = Depends(get_users_service)
) -> Issue:
    """
    Get a specific issue by ID.

    - **issue_id**: Issue UUID
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Load issue from database
    issue_data = await issues_service.get_issue(issue_id, user_id)
    if not issue_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found"
        )
    
    # Extract resolution PR URL from metadata if available
    resolution_pr_url = None
    if issue_data.get("metadata"):
        resolution_pr_url = issue_data["metadata"].get("resolution_pr_url")
    
    return Issue(
        id=issue_data["task_id"],
        project_id=issue_data["project_id"],
        title=issue_data["title"],
        description=issue_data["description"],
        github_issue_url=issue_data.get("github_url"),
        github_issue_number=issue_data.get("github_issue_number"),
        priority=IssuePriority(issue_data["priority"]),
        status=IssueStatus(issue_data["status"]),
        labels=issue_data.get("labels", []),
        assigned_agent_id=issue_data.get("assigned_to_agent_id"),
        resolution_pr_url=resolution_pr_url,
        created_at=issue_data["created_at"].isoformat(),
        updated_at=issue_data["updated_at"].isoformat(),
        resolved_at=issue_data["completed_at"].isoformat() if issue_data.get("completed_at") else None
    )


@router.patch(
    "/{issue_id}",
    response_model=Issue,
    summary="Update issue"
)
@limiter.limit("10/minute")
async def update_issue(
    issue_id: UUID,
    update: IssueUpdate,
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    users_service: UsersService = Depends(get_users_service)
) -> Issue:
    """
    Update an issue.

    Only provided fields will be updated.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update issue in database
    issue_data = await issues_service.update_issue(
        issue_id=issue_id,
        user_id=user_id,
        title=update.title,
        description=update.description,
        priority=update.priority.value if update.priority else None,
        status=update.status.value if update.status else None,
        labels=update.labels
    )
    
    if not issue_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found"
        )
    
    return Issue(
        id=issue_data["task_id"],
        project_id=issue_data["project_id"],
        title=issue_data["title"],
        description=issue_data["description"],
        github_issue_url=issue_data.get("github_url"),
        github_issue_number=issue_data.get("github_issue_number"),
        priority=IssuePriority(issue_data["priority"]),
        status=IssueStatus(issue_data["status"]),
        labels=issue_data.get("labels", []),
        assigned_agent_id=issue_data.get("assigned_to_agent_id"),
        resolution_pr_url=None,
        created_at=issue_data["created_at"].isoformat(),
        updated_at=issue_data["updated_at"].isoformat(),
        resolved_at=issue_data["completed_at"].isoformat() if issue_data.get("completed_at") else None
    )


@router.post(
    "/{issue_id}/assign",
    response_model=Issue,
    summary="Assign agent to issue"
)
@limiter.limit("10/minute")
async def assign_agent_to_issue(
    issue_id: UUID,
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    users_service: UsersService = Depends(get_users_service)
) -> Issue:
    """
    Assign an agent to work on an issue.

    - **issue_id**: Issue UUID
    - **agent_id**: Agent UUID to assign
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # TODO: Verify agent exists and is available
    
    # Assign agent to issue
    issue_data = await issues_service.assign_agent(issue_id, user_id, agent_id)
    if not issue_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found"
        )
    
    # TODO: Start agent execution
    
    return Issue(
        id=issue_data["task_id"],
        project_id=issue_data["project_id"],
        title=issue_data["title"],
        description=issue_data["description"],
        github_issue_url=issue_data.get("github_url"),
        github_issue_number=issue_data.get("github_issue_number"),
        priority=IssuePriority(issue_data["priority"]),
        status=IssueStatus(issue_data["status"]),
        labels=issue_data.get("labels", []),
        assigned_agent_id=issue_data.get("assigned_to_agent_id"),
        resolution_pr_url=None,
        created_at=issue_data["created_at"].isoformat(),
        updated_at=issue_data["updated_at"].isoformat(),
        resolved_at=issue_data["completed_at"].isoformat() if issue_data.get("completed_at") else None
    )


@router.post(
    "/{issue_id}/resolve",
    response_model=Issue,
    summary="Mark issue as resolved"
)
@limiter.limit("10/minute")
async def resolve_issue(
    issue_id: UUID,
    pr_url: Optional[str] = None,
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    users_service: UsersService = Depends(get_users_service)
) -> Issue:
    """
    Mark an issue as resolved.

    - **issue_id**: Issue UUID
    - **pr_url**: Optional PR URL that resolved the issue
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Resolve issue
    issue_data = await issues_service.resolve_issue(issue_id, user_id, pr_url)
    if not issue_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found"
        )
    
    # Extract resolution PR URL from metadata
    resolution_pr_url = None
    if issue_data.get("metadata"):
        resolution_pr_url = issue_data["metadata"].get("resolution_pr_url")
    
    return Issue(
        id=issue_data["task_id"],
        project_id=issue_data["project_id"],
        title=issue_data["title"],
        description=issue_data["description"],
        github_issue_url=issue_data.get("github_url"),
        github_issue_number=issue_data.get("github_issue_number"),
        priority=IssuePriority(issue_data["priority"]),
        status=IssueStatus(issue_data["status"]),
        labels=issue_data.get("labels", []),
        assigned_agent_id=issue_data.get("assigned_to_agent_id"),
        resolution_pr_url=resolution_pr_url,
        created_at=issue_data["created_at"].isoformat(),
        updated_at=issue_data["updated_at"].isoformat(),
        resolved_at=issue_data["completed_at"].isoformat() if issue_data.get("completed_at") else None
    )


@router.delete(
    "/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete issue"
)
@limiter.limit("5/minute")
async def delete_issue(
    issue_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    issues_service: IssuesService = Depends(get_issues_service),
    users_service: UsersService = Depends(get_users_service)
) -> None:
    """
    Delete an issue.

    This will also cancel any assigned agents.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # TODO: Cancel any assigned agents
    
    # Delete issue
    deleted = await issues_service.delete_issue(issue_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found"
        )
