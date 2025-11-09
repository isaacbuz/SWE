"""
Project Service

Business logic for project management operations.
"""
import os
import re
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg
from fastapi import HTTPException, status

from packages.db.db_connection import get_db_connection


class ProjectService:
    """Service for project operations"""

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")

    async def _get_connection(self):
        """Get database connection from pool"""
        from apps.api.db import get_db_pool
        pool = await get_db_pool()
        return await pool.acquire()
    
    async def _release_connection(self, conn):
        """Release database connection back to pool"""
        from apps.api.db import get_db_pool
        pool = await get_db_pool()
        await pool.release(conn)

    async def create_project(
        self,
        name: str,
        repository_url: str,
        owner_id: int,
        description: Optional[str] = None,
        branch: str = "main",
        enabled: bool = True
    ) -> Dict[str, Any]:
        """Create a new project"""
        # Generate slug from name
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        
        # Extract repository info
        repo_match = re.match(r'https://github\.com/([\w-]+)/([\w-]+)', repository_url)
        if not repo_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid repository URL format"
            )
        
        repository_owner, repository_name = repo_match.groups()
        project_id = uuid4()
        
        conn = await self._get_connection()
        try:
            # Check if slug exists
            existing = await conn.fetchrow(
                "SELECT project_id FROM projects WHERE slug = $1",
                slug
            )
            if existing:
                slug = f"{slug}-{project_id.hex[:8]}"
            
            # Insert project
            row = await conn.fetchrow(
                """
                INSERT INTO projects (
                    project_id, name, description, slug,
                    repository_url, repository_provider, repository_owner, repository_name,
                    default_branch, status, owner_id, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING *
                """,
                project_id, name, description, slug,
                repository_url, "github", repository_owner, repository_name,
                branch, "active" if enabled else "archived", owner_id,
                datetime.utcnow(), datetime.utcnow()
            )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def get_project(self, project_id: UUID, user_id: int) -> Dict[str, Any]:
        """Get project by ID"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT * FROM projects
                WHERE project_id = $1 AND owner_id = $2
                """,
                project_id, user_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project {project_id} not found"
                )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def list_projects(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List projects for user"""
        conn = await self._get_connection()
        try:
            # Build query
            where_clauses = ["owner_id = $1"]
            params = [user_id]
            param_idx = 2
            
            if enabled is not None:
                status_filter = "active" if enabled else "archived"
                where_clauses.append(f"status = ${param_idx}")
                params.append(status_filter)
                param_idx += 1
            
            where_sql = " AND ".join(where_clauses)
            
            # Get total count
            total_row = await conn.fetchrow(
                f"SELECT COUNT(*) as total FROM projects WHERE {where_sql}",
                *params
            )
            total = total_row["total"]
            
            # Get paginated results
            offset = (page - 1) * page_size
            rows = await conn.fetch(
                f"""
                SELECT * FROM projects
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """,
                *params, page_size, offset
            )
            
            return {
                "items": [self._row_to_dict(row) for row in rows],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        finally:
            await conn.close()

    async def update_project(
        self,
        project_id: UUID,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update project"""
        conn = await self._get_connection()
        try:
            # Verify project exists and user has access
            project = await self.get_project(project_id, user_id)
            
            # Build update query
            update_fields = []
            update_params = []
            param_idx = 1
            
            if "name" in updates:
                update_fields.append(f"name = ${param_idx}")
                update_params.append(updates["name"])
                param_idx += 1
                
                # Update slug if name changed
                slug = re.sub(r'[^a-z0-9]+', '-', updates["name"].lower()).strip('-')
                update_fields.append(f"slug = ${param_idx}")
                update_params.append(slug)
                param_idx += 1
            
            if "description" in updates:
                update_fields.append(f"description = ${param_idx}")
                update_params.append(updates["description"])
                param_idx += 1
            
            if "repository_url" in updates:
                update_fields.append(f"repository_url = ${param_idx}")
                update_params.append(updates["repository_url"])
                param_idx += 1
                
                # Update repository info
                repo_match = re.match(r'https://github\.com/([\w-]+)/([\w-]+)', updates["repository_url"])
                if repo_match:
                    update_fields.append(f"repository_owner = ${param_idx}")
                    update_params.append(repo_match.group(1))
                    param_idx += 1
                    update_fields.append(f"repository_name = ${param_idx}")
                    update_params.append(repo_match.group(2))
                    param_idx += 1
            
            if "branch" in updates:
                update_fields.append(f"default_branch = ${param_idx}")
                update_params.append(updates["branch"])
                param_idx += 1
            
            if "enabled" in updates:
                status_value = "active" if updates["enabled"] else "archived"
                update_fields.append(f"status = ${param_idx}")
                update_params.append(status_value)
                param_idx += 1
            
            if not update_fields:
                return project
            
            # Add updated_at
            update_fields.append(f"updated_at = ${param_idx}")
            update_params.append(datetime.utcnow())
            param_idx += 1
            
            # Add project_id for WHERE clause
            update_params.append(project_id)
            
            # Execute update
            update_sql = ", ".join(update_fields)
            row = await conn.fetchrow(
                f"""
                UPDATE projects
                SET {update_sql}
                WHERE project_id = ${param_idx}
                RETURNING *
                """,
                *update_params
            )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def delete_project(self, project_id: UUID, user_id: int) -> None:
        """Delete project"""
        conn = await self._get_connection()
        try:
            # Verify project exists and user has access
            await self.get_project(project_id, user_id)
            
            # Delete project (cascade will handle related data)
            result = await conn.execute(
                "DELETE FROM projects WHERE project_id = $1",
                project_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project {project_id} not found"
                )
        finally:
            await conn.close()

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        if not row:
            return {}
        
        from uuid import UUID
        return {
            "id": UUID(str(row["project_id"])),
            "name": row["name"],
            "description": row.get("description"),
            "repository_url": row.get("repository_url"),
            "branch": row.get("default_branch", "main"),
            "enabled": row.get("status") == "active",
            "owner_id": UUID(str(row["owner_id"])),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }


# Global service instance
project_service = ProjectService()

