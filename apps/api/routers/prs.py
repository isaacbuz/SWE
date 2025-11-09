"""
Pull request management endpoints.
"""
from typing import List, Optional
from uuid import UUID
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter
from services.prs import pr_service


router = APIRouter(prefix="/prs", tags=["pull-requests"])


# Enums

class PRStatus(str, Enum):
    """PR review status."""
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"
    CLOSED = "closed"


class ReviewLevel(str, Enum):
    """Review detail level."""
    QUICK = "quick"
    STANDARD = "standard"
    THOROUGH = "thorough"


# Request/Response Models

class PRCreate(BaseModel):
    """PR creation/tracking request."""
    project_id: UUID
    github_pr_url: str = Field(..., pattern=r"^https://github\.com/[\w-]+/[\w-]+/pull/\d+$")
    auto_review: bool = True
    review_level: ReviewLevel = ReviewLevel.STANDARD


class PRUpdate(BaseModel):
    """PR update request."""
    status: Optional[PRStatus] = None
    review_level: Optional[ReviewLevel] = None


class ReviewComment(BaseModel):
    """Code review comment."""
    file_path: str
    line_number: int
    comment: str
    severity: str = Field(..., pattern="^(info|warning|error)$")


class PRReview(BaseModel):
    """PR review details."""
    summary: str
    approval_status: str
    comments: List[ReviewComment]
    security_issues: List[dict] = Field(default_factory=list)
    performance_issues: List[dict] = Field(default_factory=list)
    code_quality_score: Optional[float] = None


class PR(BaseModel):
    """Pull request response model."""
    id: UUID
    project_id: UUID
    github_pr_url: str
    github_pr_number: int
    title: str
    description: Optional[str]
    author: str
    status: PRStatus
    review_level: ReviewLevel
    assigned_agent_id: Optional[UUID]
    review: Optional[PRReview]
    created_at: str
    updated_at: str
    reviewed_at: Optional[str]

    class Config:
        from_attributes = True


class PRList(BaseModel):
    """PR list response."""
    items: List[PR]
    total: int
    page: int
    page_size: int


class PRStats(BaseModel):
    """PR statistics."""
    total: int
    pending: int
    approved: int
    changes_requested: int
    merged: int
    closed: int
    avg_review_time_hours: Optional[float]


# Endpoints

@router.post(
    "",
    response_model=PR,
    status_code=status.HTTP_201_CREATED,
    summary="Track a new PR"
)
@limiter.limit("10/minute")
async def create_pr(
    pr: PRCreate,
    current_user: CurrentUser = Depends(require_user)
) -> PR:
    """
    Start tracking a GitHub PR for review.

    - **project_id**: Project UUID
    - **github_pr_url**: GitHub PR URL
    - **auto_review**: Whether to automatically trigger review
    - **review_level**: Review detail level
    """
    pr_data = await pr_service.create_pr(
        project_id=pr.project_id,
        github_pr_url=pr.github_pr_url,
        user_id=current_user.id,
        auto_review=pr.auto_review,
        review_level=pr.review_level.value
    )
    return PR(**pr_data)


@router.get(
    "",
    response_model=PRList,
    summary="List tracked PRs"
)
@limiter.limit("30/minute")
async def list_prs(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    status: Optional[PRStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(require_user)
) -> PRList:
    """
    List tracked PRs with optional filtering.

    Supports filtering by project and status.
    """
    result = await pr_service.list_prs(
        user_id=current_user.id,
        project_id=project_id,
        status_filter=status.value if status else None,
        page=page,
        page_size=page_size
    )
    return PRList(
        items=[PR(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get(
    "/stats",
    response_model=PRStats,
    summary="Get PR statistics"
)
@limiter.limit("30/minute")
async def get_pr_stats(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    current_user: CurrentUser = Depends(require_user)
) -> PRStats:
    """
    Get aggregated PR statistics.

    - **project_id**: Optional project filter
    """
    stats = await pr_service.get_pr_stats(
        user_id=current_user.id,
        project_id=project_id
    )
    return PRStats(**stats)


@router.get(
    "/{pr_id}",
    response_model=PR,
    summary="Get PR by ID"
)
@limiter.limit("30/minute")
async def get_pr(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> PR:
    """
    Get a specific PR by ID.

    - **pr_id**: PR UUID
    """
    pr_data = await pr_service.get_pr(pr_id, current_user.id)
    return PR(**pr_data)


@router.patch(
    "/{pr_id}",
    response_model=PR,
    summary="Update PR"
)
@limiter.limit("10/minute")
async def update_pr(
    pr_id: UUID,
    update: PRUpdate,
    current_user: CurrentUser = Depends(require_user)
) -> PR:
    """
    Update a PR.

    Only provided fields will be updated.
    """
    updates = update.dict(exclude_unset=True)
    if "status" in updates:
        updates["status"] = updates["status"].value if updates["status"] else None
    if "review_level" in updates:
        updates["review_level"] = updates["review_level"].value if updates["review_level"] else None
    pr_data = await pr_service.update_pr(
        pr_id=pr_id,
        user_id=current_user.id,
        updates=updates
    )
    return PR(**pr_data)


@router.post(
    "/{pr_id}/review",
    response_model=PR,
    summary="Trigger PR review"
)
@limiter.limit("5/minute")
async def trigger_pr_review(
    pr_id: UUID,
    review_level: ReviewLevel = ReviewLevel.STANDARD,
    current_user: CurrentUser = Depends(require_user)
) -> PR:
    """
    Trigger an automated review of the PR.

    - **pr_id**: PR UUID
    - **review_level**: Detail level for the review
    """
    pr_data = await pr_service.trigger_review(
        pr_id=pr_id,
        user_id=current_user.id,
        review_level=review_level.value
    )
    return PR(**pr_data)


@router.get(
    "/{pr_id}/review",
    response_model=PRReview,
    summary="Get PR review"
)
@limiter.limit("30/minute")
async def get_pr_review(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> PRReview:
    """
    Get the automated review for a PR.

    - **pr_id**: PR UUID
    """
    review_data = await pr_service.get_pr_review(pr_id, current_user.id)
    return PRReview(**review_data)


@router.post(
    "/{pr_id}/sync",
    response_model=PR,
    summary="Sync PR with GitHub"
)
@limiter.limit("10/minute")
async def sync_pr(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> PR:
    """
    Sync PR data with GitHub.

    Fetches latest PR state from GitHub API.
    """
    pr_data = await pr_service.sync_pr(pr_id, current_user.id)
    return PR(**pr_data)


@router.delete(
    "/{pr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete PR"
)
@limiter.limit("5/minute")
async def delete_pr(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> None:
    """
    Stop tracking a PR.

    This will also cancel any assigned review agents.
    """
    await pr_service.delete_pr(pr_id, current_user.id)
