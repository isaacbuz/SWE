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
    # TODO: Verify project exists and user has access
    # TODO: If github_issue_url provided, fetch issue details
    # TODO: Create issue in database
    # TODO: Optionally trigger agent to analyze issue

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Issue creation not yet implemented"
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
    current_user: CurrentUser = Depends(require_user)
) -> IssueList:
    """
    List issues with optional filtering.

    Supports filtering by project, status, priority, and labels.
    """
    # TODO: Query issues from database with filters
    # TODO: Apply pagination
    # TODO: Return issue list

    return IssueList(items=[], total=0, page=page, page_size=page_size)


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
    # TODO: Query issue statistics from database
    # TODO: Calculate counts by status and priority
    # TODO: Return statistics

    return IssueStats(
        total=0,
        open=0,
        in_progress=0,
        resolved=0,
        closed=0,
        by_priority={}
    )


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
    # TODO: Load issue from database
    # TODO: Verify user has access to issue's project
    # TODO: Return issue details

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Issue {issue_id} not found"
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
    current_user: CurrentUser = Depends(require_user)
) -> Issue:
    """
    Update an issue.

    Only provided fields will be updated.
    """
    # TODO: Load issue from database
    # TODO: Verify user has access to issue's project
    # TODO: Validate updates
    # TODO: Update issue in database
    # TODO: Return updated issue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Issue {issue_id} not found"
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
    current_user: CurrentUser = Depends(require_user)
) -> Issue:
    """
    Assign an agent to work on an issue.

    - **issue_id**: Issue UUID
    - **agent_id**: Agent UUID to assign
    """
    # TODO: Load issue from database
    # TODO: Verify user has access to issue's project
    # TODO: Verify agent exists and is available
    # TODO: Assign agent to issue
    # TODO: Update issue status to IN_PROGRESS
    # TODO: Start agent execution

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Issue {issue_id} not found"
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
    current_user: CurrentUser = Depends(require_user)
) -> Issue:
    """
    Mark an issue as resolved.

    - **issue_id**: Issue UUID
    - **pr_url**: Optional PR URL that resolved the issue
    """
    # TODO: Load issue from database
    # TODO: Verify user has access to issue's project
    # TODO: Update issue status to RESOLVED
    # TODO: Record resolution PR URL if provided
    # TODO: Set resolved_at timestamp

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Issue {issue_id} not found"
    )


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
    # TODO: Load issue from database
    # TODO: Verify user has access to issue's project
    # TODO: Cancel any assigned agents
    # TODO: Delete issue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Issue {issue_id} not found"
    )
