"""
Database service for Issues/Tasks operations.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class IssuesService:
    """Database service for Issues operations"""
    
    def __init__(self, pool: Pool):
        """Initialize issues service"""
        self.pool = pool
    
    async def create_issue(
        self,
        project_id: UUID,
        title: str,
        description: str,
        github_issue_url: Optional[str],
        priority: str,
        labels: List[str],
        created_by_user_id: int
    ) -> Dict[str, Any]:
        """Create a new issue"""
        async with self.pool.acquire() as conn:
            # Extract GitHub issue number if URL provided
            github_issue_number = None
            if github_issue_url and "github.com" in github_issue_url:
                try:
                    parts = github_issue_url.split("/")
                    if "issues" in parts:
                        idx = parts.index("issues")
                        if idx + 1 < len(parts):
                            github_issue_number = int(parts[idx + 1])
                except (ValueError, IndexError):
                    pass
            
            row = await conn.fetchrow(
                """
                INSERT INTO tasks (
                    project_id, title, description, github_issue_number, github_url,
                    type, status, priority, labels, created_by_user_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING 
                    task_id, project_id, title, description, github_issue_number,
                    github_url, type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    created_at, updated_at
                """,
                project_id,
                title,
                description,
                github_issue_number,
                github_issue_url,
                "task",  # type
                "open",  # status
                priority,
                labels,
                created_by_user_id
            )
            
            return dict(row)
    
    async def get_issue(self, issue_id: UUID, user_id: int) -> Optional[Dict[str, Any]]:
        """Get issue by ID, verifying user access via project"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    t.task_id, t.project_id, t.title, t.description,
                    t.github_issue_number, t.github_url,
                    t.type, t.status, t.priority, t.labels,
                    t.assigned_to_user_id, t.assigned_to_agent_id,
                    t.created_at, t.updated_at, t.completed_at,
                    p.owner_id, u.user_id as owner_uuid
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                JOIN users u ON p.owner_id = u.id
                WHERE t.task_id = $1 AND (p.owner_id = $2 OR p.is_public = true)
                """,
                issue_id,
                user_id
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def list_issues(
        self,
        user_id: int,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """List issues with filters and pagination"""
        async with self.pool.acquire() as conn:
            # Build WHERE clause
            conditions = ["p.owner_id = $1 OR p.is_public = true"]
            params: List[Any] = [user_id]
            param_count = 1
            
            if project_id:
                param_count += 1
                conditions.append(f"t.project_id = ${param_count}")
                params.append(project_id)
            
            if status:
                param_count += 1
                conditions.append(f"t.status = ${param_count}")
                params.append(status)
            
            if priority:
                param_count += 1
                conditions.append(f"t.priority = ${param_count}")
                params.append(priority)
            
            if labels:
                param_count += 1
                conditions.append(f"t.labels @> ${param_count}")
                params.append(labels)
            
            where_clause = " AND ".join(conditions)
            
            # Get total count
            count_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*) as total
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE {where_clause}
                """,
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
                    t.task_id, t.project_id, t.title, t.description,
                    t.github_issue_number, t.github_url,
                    t.type, t.status, t.priority, t.labels,
                    t.assigned_to_user_id, t.assigned_to_agent_id,
                    t.created_at, t.updated_at, t.completed_at
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE {where_clause}
                ORDER BY t.created_at DESC
                LIMIT ${param_count - 1} OFFSET ${param_count}
                """,
                *params
            )
            
            return [dict(row) for row in rows], total
    
    async def get_issue_stats(
        self,
        user_id: int,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get issue statistics"""
        async with self.pool.acquire() as conn:
            conditions = ["p.owner_id = $1 OR p.is_public = true"]
            params: List[Any] = [user_id]
            param_count = 1
            
            if project_id:
                param_count += 1
                conditions.append(f"t.project_id = ${param_count}")
                params.append(project_id)
            
            where_clause = " AND ".join(conditions)
            
            # Get basic stats
            stats_row = await conn.fetchrow(
                f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE t.status = 'open') as open,
                    COUNT(*) FILTER (WHERE t.status = 'in_progress') as in_progress,
                    COUNT(*) FILTER (WHERE t.status = 'closed') as resolved,
                    COUNT(*) FILTER (WHERE t.status = 'closed') as closed
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE {where_clause}
                """,
                *params
            )
            
            # Get priority breakdown
            priority_rows = await conn.fetch(
                f"""
                SELECT priority, COUNT(*) as count
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE {where_clause} AND t.priority IS NOT NULL
                GROUP BY t.priority
                """,
                *params
            )
            
            by_priority = {row["priority"]: row["count"] for row in priority_rows}
            
            return {
                "total": stats_row["total"] if stats_row else 0,
                "open": stats_row["open"] if stats_row else 0,
                "in_progress": stats_row["in_progress"] if stats_row else 0,
                "resolved": stats_row["resolved"] if stats_row else 0,
                "closed": stats_row["closed"] if stats_row else 0,
                "by_priority": by_priority
            }
            
    
    async def update_issue(
        self,
        issue_id: UUID,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update issue, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access
            issue = await self.get_issue(issue_id, user_id)
            if not issue:
                return None
            
            # Build update query
            updates = []
            params: List[Any] = []
            param_count = 0
            
            if title is not None:
                param_count += 1
                updates.append(f"title = ${param_count}")
                params.append(title)
            
            if description is not None:
                param_count += 1
                updates.append(f"description = ${param_count}")
                params.append(description)
            
            if priority is not None:
                param_count += 1
                updates.append(f"priority = ${param_count}")
                params.append(priority)
            
            if status is not None:
                param_count += 1
                updates.append(f"status = ${param_count}")
                params.append(status)
                
                # Set completed_at if closing
                if status == "closed":
                    param_count += 1
                    updates.append(f"completed_at = CURRENT_TIMESTAMP")
            
            if labels is not None:
                param_count += 1
                updates.append(f"labels = ${param_count}")
                params.append(labels)
            
            if not updates:
                return issue
            
            # Add updated_at
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add WHERE params
            param_count += 1
            params.append(issue_id)
            
            row = await conn.fetchrow(
                f"""
                UPDATE tasks
                SET {', '.join(updates)}
                WHERE task_id = ${param_count}
                RETURNING 
                    task_id, project_id, title, description,
                    github_issue_number, github_url,
                    type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    created_at, updated_at, completed_at
                """,
                *params
            )
            
            return dict(row) if row else None
    
    async def assign_agent(
        self,
        issue_id: UUID,
        user_id: int,
        agent_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Assign agent to issue"""
        async with self.pool.acquire() as conn:
            # Verify access
            issue = await self.get_issue(issue_id, user_id)
            if not issue:
                return None
            
            # TODO: Verify agent exists and is available
            
            # Update issue
            row = await conn.fetchrow(
                """
                UPDATE tasks
                SET assigned_to_agent_id = $1,
                    status = 'in_progress',
                    started_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $2
                RETURNING 
                    task_id, project_id, title, description,
                    github_issue_number, github_url,
                    type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    created_at, updated_at, completed_at
                """,
                agent_id,
                issue_id
            )
            
            return dict(row) if row else None
    
    async def resolve_issue(
        self,
        issue_id: UUID,
        user_id: int,
        pr_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Mark issue as resolved"""
        async with self.pool.acquire() as conn:
            # Verify access
            issue = await self.get_issue(issue_id, user_id)
            if not issue:
                return None
            
            # Update issue
            row = await conn.fetchrow(
                """
                UPDATE tasks
                SET status = 'closed',
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('resolution_pr_url', $1)
                WHERE task_id = $2
                RETURNING 
                    task_id, project_id, title, description,
                    github_issue_number, github_url,
                    type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    created_at, updated_at, completed_at
                """,
                pr_url,
                issue_id
            )
            
            return dict(row) if row else None
    
    async def delete_issue(self, issue_id: UUID, user_id: int) -> bool:
        """Delete issue, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access
            issue = await self.get_issue(issue_id, user_id)
            if not issue:
                return False
            
            # TODO: Cancel any assigned agents
            
            # Delete issue
            result = await conn.execute(
                "DELETE FROM tasks WHERE task_id = $1",
                issue_id
            )
            
            return result == "DELETE 1"

