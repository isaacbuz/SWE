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
from db.connection import get_db_pool
from db.prs import PRsService
from db.users import UsersService
from db.projects import ProjectsService
from services.github import get_github_service


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


# Dependencies
async def get_prs_service() -> PRsService:
    """Get PRs database service"""
    pool = await get_db_pool()
    return PRsService(pool)


async def get_projects_service() -> ProjectsService:
    """Get projects database service"""
    pool = await get_db_pool()
    return ProjectsService(pool)


async def get_users_service() -> UsersService:
    """Get users database service"""
    pool = await get_db_pool()
    return UsersService(pool)


# Helper function to convert PR data to response model
def pr_data_to_model(pr_data: dict) -> PR:
    """Convert database PR data to response model"""
    metadata = pr_data.get("metadata", {}) or {}
    review_data = metadata.get("review")
    
    # Extract PR status from metadata or infer from task status
    pr_status = metadata.get("pr_status")
    if not pr_status:
        # Infer from task status
        task_status = pr_data.get("status", "open")
        pr_status = PRsService.TASK_STATUS_TO_PR_STATUS.get(task_status, "pending")
    
    # Extract review level
    review_level = metadata.get("review_level", "standard")
    
    # Extract author
    author = metadata.get("author", "unknown")
    
    # Build review model if available
    review = None
    if review_data:
        review = PRReview(
            summary=review_data.get("summary", ""),
            approval_status=review_data.get("approval_status", "pending"),
            comments=[
                ReviewComment(**comment) if isinstance(comment, dict) else comment
                for comment in review_data.get("comments", [])
            ],
            security_issues=review_data.get("security_issues", []),
            performance_issues=review_data.get("performance_issues", []),
            code_quality_score=review_data.get("code_quality_score")
        )
    
    return PR(
        id=pr_data["task_id"],
        project_id=pr_data["project_id"],
        github_pr_url=pr_data.get("github_url", ""),
        github_pr_number=pr_data.get("github_pr_number", 0),
        title=pr_data["title"],
        description=pr_data.get("description"),
        author=author,
        status=PRStatus(pr_status),
        review_level=ReviewLevel(review_level),
        assigned_agent_id=pr_data.get("assigned_to_agent_id"),
        review=review,
        created_at=pr_data["created_at"].isoformat(),
        updated_at=pr_data["updated_at"].isoformat(),
        reviewed_at=metadata.get("reviewed_at")
    )


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
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> PR:
    """
    Start tracking a GitHub PR for review.

    - **project_id**: Project UUID
    - **github_pr_url**: GitHub PR URL
    - **auto_review**: Whether to automatically trigger review
    - **review_level**: Review detail level
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify project exists and user has access
    project = await projects_service.get_project(pr.project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {pr.project_id} not found"
        )
    
    # Extract PR number from URL
    try:
        parts = pr.github_pr_url.split("/")
        pr_number = int(parts[-1])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub PR URL"
        )
    
    # Fetch PR details from GitHub API
    title = f"PR #{pr_number}"
    description = None
    author = "unknown"
    
    github_service = get_github_service()
    github_pr = await github_service.get_pr_details(pr.github_pr_url)
    if github_pr:
        title = github_pr.get("title") or title
        description = github_pr.get("description") or description
        author = github_pr.get("author") or author
    
    # Create PR record in database
    try:
        pr_data = await prs_service.create_pr(
            project_id=pr.project_id,
            github_pr_url=pr.github_pr_url,
            title=title,
            description=description,
            github_pr_number=pr_number,
            author=author,
            review_level=pr.review_level.value,
            created_by_user_id=user_id
        )
        
        # TODO: If auto_review, trigger review agent
        
        return pr_data_to_model(pr_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create PR: {str(e)}"
        )


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
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> PRList:
    """
    List tracked PRs with optional filtering.

    Supports filtering by project and status.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query PRs from database
    prs_data, total = await prs_service.list_prs(
        user_id=user_id,
        project_id=project_id,
        status=status.value if status else None,
        page=page,
        page_size=page_size
    )
    
    # Convert to response models
    items = [pr_data_to_model(pr) for pr in prs_data]
    
    return PRList(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/stats",
    response_model=PRStats,
    summary="Get PR statistics"
)
@limiter.limit("30/minute")
async def get_pr_stats(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> PRStats:
    """
    Get aggregated PR statistics.

    - **project_id**: Optional project filter
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query PR statistics
    stats = await prs_service.get_pr_stats(user_id, project_id)
    
    return PRStats(
        total=stats.get("total", 0),
        pending=stats.get("pending", 0),
        approved=stats.get("approved", 0),
        changes_requested=stats.get("changes_requested", 0),
        merged=stats.get("merged", 0),
        closed=stats.get("closed", 0),
        avg_review_time_hours=stats.get("avg_review_time_hours")
    )


@router.get(
    "/{pr_id}",
    response_model=PR,
    summary="Get PR by ID"
)
@limiter.limit("30/minute")
async def get_pr(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> PR:
    """
    Get a specific PR by ID.

    - **pr_id**: PR UUID
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Load PR from database
    pr_data = await prs_service.get_pr(pr_id, user_id)
    if not pr_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PR {pr_id} not found"
        )
    
    return pr_data_to_model(pr_data)


@router.patch(
    "/{pr_id}",
    response_model=PR,
    summary="Update PR"
)
@limiter.limit("10/minute")
async def update_pr(
    pr_id: UUID,
    update: PRUpdate,
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> PR:
    """
    Update a PR.

    Only provided fields will be updated.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update PR in database
    pr_data = await prs_service.update_pr(
        pr_id=pr_id,
        user_id=user_id,
        status=update.status.value if update.status else None,
        review_level=update.review_level.value if update.review_level else None
    )
    
    if not pr_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PR {pr_id} not found"
        )
    
    return pr_data_to_model(pr_data)


@router.post(
    "/{pr_id}/review",
    response_model=PR,
    summary="Trigger PR review"
)
@limiter.limit("5/minute")
async def trigger_pr_review(
    pr_id: UUID,
    review_level: ReviewLevel = ReviewLevel.STANDARD,
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> PR:
    """
    Trigger an automated review of the PR.

    - **pr_id**: PR UUID
    - **review_level**: Detail level for the review
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify PR exists
    pr_data = await prs_service.get_pr(pr_id, user_id)
    if not pr_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PR {pr_id} not found"
        )
    
    # Update review level
    updated_pr = await prs_service.update_pr(
        pr_id=pr_id,
        user_id=user_id,
        review_level=review_level.value
    )
    
    # TODO: Create and start review agent
    # TODO: Assign agent to PR
    
    return pr_data_to_model(updated_pr)


@router.get(
    "/{pr_id}/review",
    response_model=PRReview,
    summary="Get PR review"
)
@limiter.limit("30/minute")
async def get_pr_review(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> PRReview:
    """
    Get the automated review for a PR.

    - **pr_id**: PR UUID
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Load PR from database
    pr_data = await prs_service.get_pr(pr_id, user_id)
    if not pr_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PR {pr_id} not found"
        )
    
    # Extract review from metadata
    metadata = pr_data.get("metadata", {}) or {}
    review_data = metadata.get("review")
    
    if not review_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review for PR {pr_id} not found"
        )
    
    return PRReview(
        summary=review_data.get("summary", ""),
        approval_status=review_data.get("approval_status", "pending"),
        comments=[
            ReviewComment(**comment) if isinstance(comment, dict) else comment
            for comment in review_data.get("comments", [])
        ],
        security_issues=review_data.get("security_issues", []),
        performance_issues=review_data.get("performance_issues", []),
        code_quality_score=review_data.get("code_quality_score")
    )


@router.post(
    "/{pr_id}/sync",
    response_model=PR,
    summary="Sync PR with GitHub"
)
@limiter.limit("10/minute")
async def sync_pr(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> PR:
    """
    Sync PR data with GitHub.

    Fetches latest PR state from GitHub API.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Load PR from database
    pr_data = await prs_service.get_pr(pr_id, user_id)
    if not pr_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PR {pr_id} not found"
        )
    
    # Fetch latest PR data from GitHub API
    github_service = get_github_service()
    github_pr = await github_service.get_pr_details(pr_data.get("github_url"))
    
    if github_pr:
        # Update PR in database with latest data
        updated_pr = await prs_service.update_pr(
            pr_id=pr_id,
            user_id=user_id,
            status="merged" if github_pr.get("merged") else "closed" if github_pr.get("state") == "closed" else None
        )
        if updated_pr:
            pr_data = updated_pr
    
    return pr_data_to_model(pr_data)


@router.delete(
    "/{pr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete PR"
)
@limiter.limit("5/minute")
async def delete_pr(
    pr_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    prs_service: PRsService = Depends(get_prs_service),
    users_service: UsersService = Depends(get_users_service)
) -> None:
    """
    Stop tracking a PR.

    This will also cancel any assigned review agents.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # TODO: Cancel any assigned agents
    
    # Delete PR
    deleted = await prs_service.delete_pr(pr_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PR {pr_id} not found"
        )
