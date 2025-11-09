"""
Database service for Projects operations.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class ProjectsService:
    """Database service for Projects operations"""
    
    def __init__(self, pool: Pool):
        """
        Initialize projects service
        
        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool
    
    async def create_project(
        self,
        name: str,
        description: Optional[str],
        repository_url: str,
        branch: str,
        owner_id: int,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """Create a new project"""
        async with self.pool.acquire() as conn:
            # Generate slug from name
            slug = name.lower().replace(" ", "-").replace("_", "-")
            
            # Extract repository info
            repo_owner = None
            repo_name = None
            repo_provider = None
            
            if repository_url:
                if "github.com" in repository_url:
                    repo_provider = "github"
                    parts = repository_url.replace("https://github.com/", "").split("/")
                    if len(parts) >= 2:
                        repo_owner = parts[0]
                        repo_name = parts[1].replace(".git", "")
            
            row = await conn.fetchrow(
                """
                INSERT INTO projects (
                    name, description, slug, repository_url, repository_provider,
                    repository_owner, repository_name, default_branch,
                    owner_id, status, is_public
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING 
                    project_id, name, description, repository_url, default_branch,
                    status, owner_id, created_at, updated_at
                """,
                name,
                description,
                slug,
                repository_url,
                repo_provider,
                repo_owner,
                repo_name,
                branch,
                owner_id,
                "active" if enabled else "archived",
                False  # is_public
            )
            
            return dict(row)
    
    async def get_project(self, project_id: UUID, user_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID, verifying user access"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    project_id, name, description, repository_url, default_branch,
                    status, owner_id, created_at, updated_at
                FROM projects
                WHERE project_id = $1 AND (owner_id = $2 OR is_public = true)
                """,
                project_id,
                user_id
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def list_projects(
        self,
        user_id: int,
        enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """List projects for user with pagination"""
        async with self.pool.acquire() as conn:
            # Build WHERE clause
            conditions = ["(owner_id = $1 OR is_public = true)"]
            params: List[Any] = [user_id]
            param_count = 1
            
            if enabled is not None:
                param_count += 1
                status = "active" if enabled else "archived"
                conditions.append(f"status = ${param_count}")
                params.append(status)
            
            where_clause = " AND ".join(conditions)
            
            # Get total count
            count_row = await conn.fetchrow(
                f"SELECT COUNT(*) as total FROM projects WHERE {where_clause}",
                *params
            )
            total = count_row["total"] if count_row else 0
            
            # Get paginated results
            offset = (page - 1) * page_size
            param_count += 1
            params.append(page_size)
            param_count += 1
            params.append(offset)
            
            rows = await conn.fetch(
                f"""
                SELECT 
                    p.project_id, p.name, p.description, p.repository_url, p.default_branch,
                    p.status, p.owner_id, p.created_at, p.updated_at,
                    u.user_id as owner_uuid
                FROM projects p
                JOIN users u ON p.owner_id = u.id
                WHERE {where_clause}
                ORDER BY p.created_at DESC
                LIMIT ${param_count - 1} OFFSET ${param_count}
                """,
                *params
            )
            
            return [dict(row) for row in rows], total
    
    async def update_project(
        self,
        project_id: UUID,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        repository_url: Optional[str] = None,
        branch: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Update project, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access
            project = await self.get_project(project_id, user_id)
            if not project:
                return None
            
            # Build update query
            updates = []
            params: List[Any] = []
            param_count = 0
            
            if name is not None:
                param_count += 1
                updates.append(f"name = ${param_count}")
                params.append(name)
            
            if description is not None:
                param_count += 1
                updates.append(f"description = ${param_count}")
                params.append(description)
            
            if repository_url is not None:
                param_count += 1
                updates.append(f"repository_url = ${param_count}")
                params.append(repository_url)
                
                # Update repo info
                if "github.com" in repository_url:
                    repo_provider = "github"
                    parts = repository_url.replace("https://github.com/", "").split("/")
                    if len(parts) >= 2:
                        repo_owner = parts[0]
                        repo_name = parts[1].replace(".git", "")
                        param_count += 1
                        updates.append(f"repository_provider = ${param_count}")
                        params.append(repo_provider)
                        param_count += 1
                        updates.append(f"repository_owner = ${param_count}")
                        params.append(repo_owner)
                        param_count += 1
                        updates.append(f"repository_name = ${param_count}")
                        params.append(repo_name)
            
            if branch is not None:
                param_count += 1
                updates.append(f"default_branch = ${param_count}")
                params.append(branch)
            
            if enabled is not None:
                param_count += 1
                status = "active" if enabled else "archived"
                updates.append(f"status = ${param_count}")
                params.append(status)
            
            if not updates:
                return project
            
            # Add updated_at
            param_count += 1
            updates.append(f"updated_at = CURRENT_TIMESTAMP")
            
            # Add WHERE params
            param_count += 1
            params.append(project_id)
            param_count += 1
            params.append(user_id)
            
            row = await conn.fetchrow(
                f"""
                UPDATE projects p
                SET {', '.join(updates)}
                FROM users u
                WHERE p.project_id = ${param_count - 1} AND p.owner_id = ${param_count}
                    AND p.owner_id = u.id
                RETURNING 
                    p.project_id, p.name, p.description, p.repository_url, p.default_branch,
                    p.status, p.owner_id, p.created_at, p.updated_at,
                    u.user_id as owner_uuid
                """,
                *params
            )
            
            return dict(row) if row else None
    
    async def delete_project(self, project_id: UUID, user_id: int) -> bool:
        """Delete project, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access and delete
            result = await conn.execute(
                """
                DELETE FROM projects
                WHERE project_id = $1 AND owner_id = $2
                """,
                project_id,
                user_id
            )
            
            return result == "DELETE 1"

