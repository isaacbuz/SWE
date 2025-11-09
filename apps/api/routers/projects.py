"""
Project management endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

import asyncpg

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter
from db.connection import get_db_pool
from db.projects import ProjectsService
from db.users import UsersService
from services.github import get_github_service


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


# Dependency to get projects service
async def get_projects_service() -> ProjectsService:
    """Get projects database service"""
    pool = await get_db_pool()
    return ProjectsService(pool)


# Dependency to get users service
async def get_users_service() -> UsersService:
    """Get users database service"""
    pool = await get_db_pool()
    return UsersService(pool)


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
    current_user: CurrentUser = Depends(require_user),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> Project:
    """
    Create a new project.

    - **name**: Project name (required)
    - **description**: Project description (optional)
    - **repository_url**: GitHub repository URL (required)
    - **branch**: Git branch to monitor (default: main)
    - **enabled**: Whether project is enabled (default: true)
    """
    # Get user integer ID from UUID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate repository exists and user has access (GitHub API check)
    github_service = get_github_service()
    if not await github_service.validate_repository(project.repository_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository {project.repository_url} does not exist or is not accessible"
        )
    
    # Create project in database
    try:
        project_data = await projects_service.create_project(
            name=project.name,
            description=project.description,
            repository_url=project.repository_url,
            branch=project.branch,
            owner_id=user_id,
            enabled=project.enabled
        )
        
        # TODO: Initialize project configuration
        # TODO: Queue initial repository scan
        
        return Project(
            id=project_data["project_id"],
            name=project_data["name"],
            description=project_data["description"],
            repository_url=project_data["repository_url"],
            branch=project_data["default_branch"],
            enabled=project_data["status"] == "active",
            owner_id=current_user.id,  # Return UUID
            created_at=project_data["created_at"].isoformat(),
            updated_at=project_data["updated_at"].isoformat()
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this name or repository already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


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
    current_user: CurrentUser = Depends(require_user),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> ProjectList:
    """
    List all projects for the current user.

    Supports pagination and filtering.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query projects from database
    projects_data, total = await projects_service.list_projects(
        user_id=user_id,
        enabled=enabled,
        page=page,
        page_size=page_size
    )
    
    # Convert to response models
    items = [
        Project(
            id=proj["project_id"],
            name=proj["name"],
            description=proj["description"],
            repository_url=proj["repository_url"],
            branch=proj["default_branch"],
            enabled=proj["status"] == "active",
            owner_id=current_user.id,  # Return UUID (would need to fetch actual owner UUID)
            created_at=proj["created_at"].isoformat(),
            updated_at=proj["updated_at"].isoformat()
        )
        for proj in projects_data
    ]
    
    return ProjectList(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get project by ID"
)
@limiter.limit("30/minute")
async def get_project(
    project_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> Project:
    """
    Get a specific project by ID.

    - **project_id**: Project UUID
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Load project from database
    project_data = await projects_service.get_project(project_id, user_id)
    if not project_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
        # Get owner UUID
        owner_uuid = project_data.get("owner_uuid") or current_user.id
        
        return Project(
            id=project_data["project_id"],
            name=project_data["name"],
            description=project_data["description"],
            repository_url=project_data["repository_url"],
            branch=project_data["default_branch"],
            enabled=project_data["status"] == "active",
            owner_id=owner_uuid,
            created_at=project_data["created_at"].isoformat(),
            updated_at=project_data["updated_at"].isoformat()
        )


@router.patch(
    "/{project_id}",
    response_model=Project,
    summary="Update project"
)
@limiter.limit("10/minute")
async def update_project(
    project_id: UUID,
    update: ProjectUpdate,
    current_user: CurrentUser = Depends(require_user),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> Project:
    """
    Update a project.

    Only provided fields will be updated.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update project in database
    project_data = await projects_service.update_project(
        project_id=project_id,
        user_id=user_id,
        name=update.name,
        description=update.description,
        repository_url=update.repository_url,
        branch=update.branch,
        enabled=update.enabled
    )
    
    if not project_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    return Project(
        id=project_data["project_id"],
        name=project_data["name"],
        description=project_data["description"],
        repository_url=project_data["repository_url"],
        branch=project_data["default_branch"],
        enabled=project_data["status"] == "active",
        owner_id=current_user.id,  # Return UUID
        created_at=project_data["created_at"].isoformat(),
        updated_at=project_data["updated_at"].isoformat()
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project"
)
@limiter.limit("5/minute")
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    projects_service: ProjectsService = Depends(get_projects_service),
    users_service: UsersService = Depends(get_users_service)
) -> None:
    """
    Delete a project.

    This will also delete all associated data (agents, issues, PRs, etc.).
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # TODO: Cancel any running agents for this project
    
    # Delete project (cascade will handle associated data)
    deleted = await projects_service.delete_project(project_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
