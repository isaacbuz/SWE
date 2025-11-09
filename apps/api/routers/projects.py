"""
Project management endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter
from services.projects import project_service


router = APIRouter(prefix="/projects", tags=["projects"])


# Request/Response Models

class ProjectCreate(BaseModel):
    """Project creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    repository_url: str = Field(..., pattern=r"^https://github\.com/[\w-]+/[\w-]+$")
    branch: str = Field(default="main", max_length=255)
    enabled: bool = True


class ProjectUpdate(BaseModel):
    """Project update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    repository_url: Optional[str] = Field(None, pattern=r"^https://github\.com/[\w-]+/[\w-]+$")
    branch: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None


class Project(BaseModel):
    """Project response model."""
    id: UUID
    name: str
    description: Optional[str]
    repository_url: str
    branch: str
    enabled: bool
    owner_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    """Project list response."""
    items: List[Project]
    total: int
    page: int
    page_size: int


# Endpoints

@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project"
)
@limiter.limit("10/minute")
async def create_project(
    project: ProjectCreate,
    current_user: CurrentUser = Depends(require_user)
) -> Project:
    """
    Create a new project.

    - **name**: Project name (required)
    - **description**: Project description (optional)
    - **repository_url**: GitHub repository URL (required)
    - **branch**: Git branch to monitor (default: main)
    - **enabled**: Whether project is enabled (default: true)
    """
    project_data = await project_service.create_project(
        name=project.name,
        repository_url=project.repository_url,
        owner_id=current_user.id,
        description=project.description,
        branch=project.branch,
        enabled=project.enabled
    )
    return Project(**project_data)


@router.get(
    "",
    response_model=ProjectList,
    summary="List all projects"
)
@limiter.limit("30/minute")
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    current_user: CurrentUser = Depends(require_user)
) -> ProjectList:
    """
    List all projects for the current user.

    Supports pagination and filtering.
    """
    result = await project_service.list_projects(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        enabled=enabled
    )
    return ProjectList(
        items=[Project(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get project by ID"
)
@limiter.limit("30/minute")
async def get_project(
    project_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> Project:
    """
    Get a specific project by ID.

    - **project_id**: Project UUID
    """
    project_data = await project_service.get_project(project_id, current_user.id)
    return Project(**project_data)


@router.patch(
    "/{project_id}",
    response_model=Project,
    summary="Update project"
)
@limiter.limit("10/minute")
async def update_project(
    project_id: UUID,
    update: ProjectUpdate,
    current_user: CurrentUser = Depends(require_user)
) -> Project:
    """
    Update a project.

    Only provided fields will be updated.
    """
    updates = update.dict(exclude_unset=True)
    project_data = await project_service.update_project(
        project_id=project_id,
        user_id=current_user.id,
        updates=updates
    )
    return Project(**project_data)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project"
)
@limiter.limit("5/minute")
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser = Depends(require_user)
) -> None:
    """
    Delete a project.

    This will also delete all associated data (agents, issues, PRs, etc.).
    """
    await project_service.delete_project(project_id, current_user.id)
