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
from services.issues import issue_service


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
    current_user: CurrentUser = Depends(require_user)
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
    issue_data = await issue_service.create_issue(
        project_id=issue.project_id,
        title=issue.title,
        description=issue.description,
        user_id=current_user.id,
        github_issue_url=issue.github_issue_url,
        priority=issue.priority.value,
        labels=issue.labels
    )
    return Issue(**issue_data)


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
    current_user: CurrentUser = Depends(require_user)
) -> IssueList:
    """
    List issues with optional filtering.

    Supports filtering by project, status, priority, and labels.
    """
    result = await issue_service.list_issues(
        user_id=current_user.id,
        project_id=project_id,
        status_filter=status.value if status else None,
        priority_filter=priority.value if priority else None,
        labels_filter=labels,
        page=page,
        page_size=page_size
    )
    return IssueList(
        items=[Issue(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get(
    "/stats",
    response_model=IssueStats,
    summary="Get issue statistics"
)
@limiter.limit("30/minute")
async def get_issue_stats(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    current_user: CurrentUser = Depends(require_user)
) -> IssueStats:
    """
    Get aggregated issue statistics.

    - **project_id**: Optional project filter
    """
    stats = await issue_service.get_issue_stats(
        user_id=current_user.id,
        project_id=project_id
    )
    return IssueStats(**stats)


@router.get(
    "/{issue_id}",
    response_model=Issue,
    summary="Get issue by ID"
)
@limiter.limit("30/minute")
async def get_issue(
    issue_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> Issue:
    """
    Get a specific issue by ID.

    - **issue_id**: Issue UUID
    """
    issue_data = await issue_service.get_issue(issue_id, current_user.id)
    return Issue(**issue_data)


@router.patch(
    "/{issue_id}",
    response_model=Issue,
    summary="Update issue"
)
@limiter.limit("10/minute")
async def update_issue(
    issue_id: UUID,
    update: IssueUpdate,
    current_user: CurrentUser = Depends(require_user)
) -> Issue:
    """
    Update an issue.

    Only provided fields will be updated.
    """
    updates = update.dict(exclude_unset=True)
    if "priority" in updates:
        updates["priority"] = updates["priority"].value if updates["priority"] else None
    if "status" in updates:
        updates["status"] = updates["status"].value if updates["status"] else None
    issue_data = await issue_service.update_issue(
        issue_id=issue_id,
        user_id=current_user.id,
        updates=updates
    )
    return Issue(**issue_data)


@router.post(
    "/{issue_id}/assign",
    response_model=Issue,
    summary="Assign agent to issue"
)
@limiter.limit("10/minute")
async def assign_agent_to_issue(
    issue_id: UUID,
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> Issue:
    """
    Assign an agent to work on an issue.

    - **issue_id**: Issue UUID
    - **agent_id**: Agent UUID to assign
    """
    issue_data = await issue_service.assign_agent(
        issue_id=issue_id,
        agent_id=agent_id,
        user_id=current_user.id
    )
    return Issue(**issue_data)


@router.post(
    "/{issue_id}/resolve",
    response_model=Issue,
    summary="Mark issue as resolved"
)
@limiter.limit("10/minute")
async def resolve_issue(
    issue_id: UUID,
    pr_url: Optional[str] = None,
    current_user: CurrentUser = Depends(require_user)
) -> Issue:
    """
    Mark an issue as resolved.

    - **issue_id**: Issue UUID
    - **pr_url**: Optional PR URL that resolved the issue
    """
    issue_data = await issue_service.resolve_issue(
        issue_id=issue_id,
        user_id=current_user.id,
        pr_url=pr_url
    )
    return Issue(**issue_data)


@router.delete(
    "/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete issue"
)
@limiter.limit("5/minute")
async def delete_issue(
    issue_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> None:
    """
    Delete an issue.

    This will also cancel any assigned agents.
    """
    await issue_service.delete_issue(issue_id, current_user.id)
