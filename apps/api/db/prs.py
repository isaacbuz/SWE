"""
Database service for Pull Requests operations.
PRs are stored in the tasks table with github_pr_number set.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class PRsService:
    """Database service for PRs operations"""
    
    def __init__(self, pool: Pool):
        """Initialize PRs service"""
        self.pool = pool
    
    # Map PR status to task status
    PR_STATUS_TO_TASK_STATUS = {
        "pending": "open",
        "approved": "in_review",
        "changes_requested": "in_review",
        "merged": "closed",
        "closed": "closed"
    }
    
    TASK_STATUS_TO_PR_STATUS = {
        "open": "pending",
        "in_progress": "pending",
        "in_review": "approved",  # Default, check metadata for actual status
        "blocked": "pending",
        "closed": "merged",  # Default, check metadata for actual status
        "draft": "pending"
    }
    
    async def create_pr(
        self,
        project_id: UUID,
        github_pr_url: str,
        title: str,
        description: Optional[str],
        github_pr_number: int,
        author: str,
        review_level: str,
        created_by_user_id: int
    ) -> Dict[str, Any]:
        """Create a new PR tracking record"""
        async with self.pool.acquire() as conn:
            # Store PR status in metadata
            metadata = {
                "pr_status": "pending",
                "review_level": review_level,
                "author": author
            }
            
            row = await conn.fetchrow(
                """
                INSERT INTO tasks (
                    project_id, title, description, github_pr_number, github_url,
                    type, status, priority, metadata, created_by_user_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING 
                    task_id, project_id, title, description, github_pr_number,
                    github_url, type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    metadata, created_at, updated_at
                """,
                project_id,
                title,
                description,
                github_pr_number,
                github_pr_url,
                "task",  # type
                "open",  # status (pending)
                "medium",  # priority
                metadata,
                created_by_user_id
            )
            
            return dict(row)
    
    async def get_pr(self, pr_id: UUID, user_id: int) -> Optional[Dict[str, Any]]:
        """Get PR by ID, verifying user access via project"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    t.task_id, t.project_id, t.title, t.description,
                    t.github_pr_number, t.github_url,
                    t.type, t.status, t.priority, t.labels,
                    t.assigned_to_user_id, t.assigned_to_agent_id,
                    t.metadata, t.created_at, t.updated_at, t.completed_at
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.task_id = $1 
                    AND t.github_pr_number IS NOT NULL
                    AND (p.owner_id = $2 OR p.is_public = true)
                """,
                pr_id,
                user_id
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def list_prs(
        self,
        user_id: int,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """List PRs with filters and pagination"""
        async with self.pool.acquire() as conn:
            # Build WHERE clause
            conditions = [
                "p.owner_id = $1 OR p.is_public = true",
                "t.github_pr_number IS NOT NULL"
            ]
            params: List[Any] = [user_id]
            param_count = 1
            
            if project_id:
                param_count += 1
                conditions.append(f"t.project_id = ${param_count}")
                params.append(project_id)
            
            if status:
                # Filter by PR status in metadata
                param_count += 1
                conditions.append(f"(t.metadata->>'pr_status' = ${param_count} OR (t.metadata->>'pr_status' IS NULL AND t.status = 'open'))")
                params.append(status)
            
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
                    t.github_pr_number, t.github_url,
                    t.type, t.status, t.priority, t.labels,
                    t.assigned_to_user_id, t.assigned_to_agent_id,
                    t.metadata, t.created_at, t.updated_at, t.completed_at
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE {where_clause}
                ORDER BY t.created_at DESC
                LIMIT ${param_count - 1} OFFSET ${param_count}
                """,
                *params
            )
            
            return [dict(row) for row in rows], total
    
    async def get_pr_stats(
        self,
        user_id: int,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get PR statistics"""
        async with self.pool.acquire() as conn:
            conditions = [
                "p.owner_id = $1 OR p.is_public = true",
                "t.github_pr_number IS NOT NULL"
            ]
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
                    COUNT(*) FILTER (WHERE t.metadata->>'pr_status' = 'pending' OR (t.metadata->>'pr_status' IS NULL AND t.status = 'open')) as pending,
                    COUNT(*) FILTER (WHERE t.metadata->>'pr_status' = 'approved') as approved,
                    COUNT(*) FILTER (WHERE t.metadata->>'pr_status' = 'changes_requested') as changes_requested,
                    COUNT(*) FILTER (WHERE t.metadata->>'pr_status' = 'merged') as merged,
                    COUNT(*) FILTER (WHERE t.metadata->>'pr_status' = 'closed') as closed,
                    AVG(EXTRACT(EPOCH FROM (t.completed_at - t.created_at)) / 3600) as avg_review_time_hours
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE {where_clause}
                """,
                *params
            )
            
            return {
                "total": stats_row["total"] if stats_row else 0,
                "pending": stats_row["pending"] if stats_row else 0,
                "approved": stats_row["approved"] if stats_row else 0,
                "changes_requested": stats_row["changes_requested"] if stats_row else 0,
                "merged": stats_row["merged"] if stats_row else 0,
                "closed": stats_row["closed"] if stats_row else 0,
                "avg_review_time_hours": float(stats_row["avg_review_time_hours"]) if stats_row and stats_row["avg_review_time_hours"] else None
            }
    
    async def update_pr(
        self,
        pr_id: UUID,
        user_id: int,
        status: Optional[str] = None,
        review_level: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update PR, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access
            pr = await self.get_pr(pr_id, user_id)
            if not pr:
                return None
            
            # Build update query
            updates = []
            params: List[Any] = []
            param_count = 0
            
            metadata = pr.get("metadata", {}) or {}
            
            if status is not None:
                # Update both task status and PR status in metadata
                task_status = self.PR_STATUS_TO_TASK_STATUS.get(status, "open")
                param_count += 1
                updates.append(f"status = ${param_count}")
                params.append(task_status)
                metadata["pr_status"] = status
                
                # Set completed_at if merged/closed
                if status in ["merged", "closed"]:
                    updates.append("completed_at = CURRENT_TIMESTAMP")
            
            if review_level is not None:
                metadata["review_level"] = review_level
            
            if status is not None or review_level is not None:
                param_count += 1
                updates.append(f"metadata = ${param_count}")
                params.append(metadata)
            
            if not updates:
                return pr
            
            # Add updated_at
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add WHERE params
            param_count += 1
            params.append(pr_id)
            
            row = await conn.fetchrow(
                f"""
                UPDATE tasks
                SET {', '.join(updates)}
                WHERE task_id = ${param_count}
                RETURNING 
                    task_id, project_id, title, description,
                    github_pr_number, github_url,
                    type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    metadata, created_at, updated_at, completed_at
                """,
                *params
            )
            
            return dict(row) if row else None
    
    async def assign_review_agent(
        self,
        pr_id: UUID,
        user_id: int,
        agent_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Assign review agent to PR"""
        async with self.pool.acquire() as conn:
            # Verify access
            pr = await self.get_pr(pr_id, user_id)
            if not pr:
                return None
            
            # TODO: Verify agent exists and is available
            
            # Update PR
            row = await conn.fetchrow(
                """
                UPDATE tasks
                SET assigned_to_agent_id = $1,
                    status = 'in_review',
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $2
                RETURNING 
                    task_id, project_id, title, description,
                    github_pr_number, github_url,
                    type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    metadata, created_at, updated_at, completed_at
                """,
                agent_id,
                pr_id
            )
            
            return dict(row) if row else None
    
    async def store_review(
        self,
        pr_id: UUID,
        user_id: int,
        review_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Store PR review results"""
        async with self.pool.acquire() as conn:
            # Verify access
            pr = await self.get_pr(pr_id, user_id)
            if not pr:
                return None
            
            # Update metadata with review
            metadata = pr.get("metadata", {}) or {}
            metadata["review"] = review_data
            metadata["reviewed_at"] = datetime.utcnow().isoformat()
            
            # Update PR status based on review
            approval_status = review_data.get("approval_status", "pending")
            if approval_status == "approved":
                metadata["pr_status"] = "approved"
            elif approval_status == "changes_requested":
                metadata["pr_status"] = "changes_requested"
            
            row = await conn.fetchrow(
                """
                UPDATE tasks
                SET metadata = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $2
                RETURNING 
                    task_id, project_id, title, description,
                    github_pr_number, github_url,
                    type, status, priority, labels,
                    assigned_to_user_id, assigned_to_agent_id,
                    metadata, created_at, updated_at, completed_at
                """,
                metadata,
                pr_id
            )
            
            return dict(row) if row else None
    
    async def delete_pr(self, pr_id: UUID, user_id: int) -> bool:
        """Delete PR, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access
            pr = await self.get_pr(pr_id, user_id)
            if not pr:
                return False
            
            # TODO: Cancel any assigned agents
            
            # Delete PR
            result = await conn.execute(
                "DELETE FROM tasks WHERE task_id = $1",
                pr_id
            )
            
            return result == "DELETE 1"

