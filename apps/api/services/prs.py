"""
PR Service

Business logic for pull request management operations.
"""
import os
import re
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg
from fastapi import HTTPException, status

from apps.api.db import get_db_pool


class PRService:
    """Service for PR operations"""

    async def _get_connection(self):
        """Get database connection from pool"""
        pool = await get_db_pool()
        return await pool.acquire()
    
    async def _release_connection(self, conn):
        """Release database connection back to pool"""
        pool = await get_db_pool()
        await pool.release(conn)

    async def create_pr(
        self,
        project_id: UUID,
        github_pr_url: str,
        user_id: int,
        auto_review: bool = True,
        review_level: str = "standard"
    ) -> Dict[str, Any]:
        """Create/track a new PR"""
        conn = await self._get_connection()
        try:
            # Verify project exists and user has access
            project_row = await conn.fetchrow(
                "SELECT project_id FROM projects WHERE project_id = $1 AND owner_id = $2",
                project_id, user_id
            )
            if not project_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project {project_id} not found"
                )
            
            # Extract GitHub PR number
            match = re.search(r'/pull/(\d+)$', github_pr_url)
            if not match:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid GitHub PR URL format"
                )
            
            github_pr_number = int(match.group(1))
            
            # Check if PR already tracked
            existing = await conn.fetchrow(
                "SELECT task_id FROM tasks WHERE github_pr_number = $1 AND project_id = $2",
                github_pr_number, project_id
            )
            if existing:
                return await self.get_pr(UUID(str(existing["task_id"])), user_id)
            
            task_id = uuid4()
            
            # Insert PR (as task with github_pr_number)
            row = await conn.fetchrow(
                """
                INSERT INTO tasks (
                    task_id, project_id, title, description,
                    github_pr_number, github_url, type,
                    status, metadata, created_by_user_id,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
                """,
                task_id, project_id, "PR #" + str(github_pr_number), None,
                github_pr_number, github_pr_url, "task",
                "open", {"review_level": review_level, "auto_review": auto_review}, user_id,
                datetime.utcnow(), datetime.utcnow()
            )
            
            pr_data = self._row_to_dict(row)
            
            # If auto_review, trigger review (TODO: implement review agent trigger)
            
            return pr_data
        finally:
            await self._release_connection(conn)

    async def get_pr(self, pr_id: UUID, user_id: int) -> Dict[str, Any]:
        """Get PR by ID"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT t.* FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE t.task_id = $1 AND p.owner_id = $2 AND t.github_pr_number IS NOT NULL
                """,
                pr_id, user_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PR {pr_id} not found"
                )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def list_prs(
        self,
        user_id: int,
        project_id: Optional[UUID] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List PRs with filters"""
        conn = await self._get_connection()
        try:
            # Build query
            where_clauses = ["p.owner_id = $1", "t.github_pr_number IS NOT NULL"]
            params = [user_id]
            param_idx = 2
            
            if project_id:
                where_clauses.append(f"t.project_id = ${param_idx}")
                params.append(project_id)
                param_idx += 1
            
            if status_filter:
                # Map API status to database status/metadata
                where_clauses.append(f"t.status = ${param_idx}")
                params.append(status_filter)
                param_idx += 1
            
            where_sql = " AND ".join(where_clauses)
            
            # Get total count
            total_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*) as total
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE {where_sql}
                """,
                *params
            )
            total = total_row["total"]
            
            # Get paginated results
            offset = (page - 1) * page_size
            rows = await conn.fetch(
                f"""
                SELECT t.* FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE {where_sql}
                ORDER BY t.created_at DESC
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
            await self._release_connection(conn)

    async def get_pr_stats(
        self,
        user_id: int,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get PR statistics"""
        conn = await self._get_connection()
        try:
            where_clauses = ["p.owner_id = $1", "t.github_pr_number IS NOT NULL"]
            params = [user_id]
            param_idx = 2
            
            if project_id:
                where_clauses.append(f"t.project_id = ${param_idx}")
                params.append(project_id)
                param_idx += 1
            
            where_sql = " AND ".join(where_clauses)
            
            # Get counts by status
            stats_row = await conn.fetchrow(
                f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE t.status = 'open') as pending,
                    COUNT(*) FILTER (WHERE t.status = 'closed' AND t.metadata->>'merged' = 'true') as merged,
                    COUNT(*) FILTER (WHERE t.status = 'closed' AND (t.metadata->>'merged' IS NULL OR t.metadata->>'merged' = 'false')) as closed
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE {where_sql}
                """,
                *params
            )
            
            # Calculate average review time (simplified)
            avg_review_row = await conn.fetchrow(
                f"""
                SELECT AVG(EXTRACT(EPOCH FROM (t.completed_at - t.started_at)) / 3600) as avg_hours
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE {where_sql} AND t.started_at IS NOT NULL AND t.completed_at IS NOT NULL
                """,
                *params
            )
            
            return {
                "total": stats_row["total"],
                "pending": stats_row["pending"],
                "approved": 0,  # Would need separate tracking
                "changes_requested": 0,  # Would need separate tracking
                "merged": stats_row["merged"],
                "closed": stats_row["closed"],
                "avg_review_time_hours": float(avg_review_row["avg_hours"]) if avg_review_row["avg_hours"] else None
            }
        finally:
            await self._release_connection(conn)

    async def update_pr(
        self,
        pr_id: UUID,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update PR"""
        conn = await self._get_connection()
        try:
            # Verify PR exists and user has access
            pr = await self.get_pr(pr_id, user_id)
            
            # Build update query
            update_fields = []
            update_params = []
            param_idx = 1
            
            if "status" in updates:
                update_fields.append(f"status = ${param_idx}")
                update_params.append(updates["status"])
                param_idx += 1
            
            if "review_level" in updates:
                metadata = dict(pr.get("metadata", {}))
                metadata["review_level"] = updates["review_level"]
                update_fields.append(f"metadata = ${param_idx}")
                update_params.append(metadata)
                param_idx += 1
            
            if not update_fields:
                return pr
            
            # Add updated_at
            update_fields.append(f"updated_at = ${param_idx}")
            update_params.append(datetime.utcnow())
            param_idx += 1
            
            # Add task_id for WHERE clause
            update_params.append(pr_id)
            
            # Execute update
            update_sql = ", ".join(update_fields)
            row = await conn.fetchrow(
                f"""
                UPDATE tasks
                SET {update_sql}
                WHERE task_id = ${param_idx}
                RETURNING *
                """,
                *update_params
            )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def trigger_review(
        self,
        pr_id: UUID,
        user_id: int,
        review_level: str = "standard"
    ) -> Dict[str, Any]:
        """Trigger PR review"""
        # Verify PR exists and user has access
        pr = await self.get_pr(pr_id, user_id)
        
        # TODO: Trigger review agent
        # For now, just update metadata
        return await self.update_pr(pr_id, user_id, {"review_level": review_level})

    async def get_pr_review(
        self,
        pr_id: UUID,
        user_id: int
    ) -> Dict[str, Any]:
        """Get PR review details"""
        pr = await self.get_pr(pr_id, user_id)
        
        # Get review from metadata or AI analysis
        metadata = pr.get("metadata", {})
        ai_analysis = pr.get("ai_analysis", {})
        
        # Construct review response
        review = {
            "summary": ai_analysis.get("summary", "Review pending"),
            "approval_status": metadata.get("approval_status", "pending"),
            "comments": ai_analysis.get("comments", []),
            "security_issues": ai_analysis.get("security_issues", []),
            "performance_issues": ai_analysis.get("performance_issues", []),
            "code_quality_score": ai_analysis.get("code_quality_score")
        }
        
        return review

    async def sync_pr(
        self,
        pr_id: UUID,
        user_id: int
    ) -> Dict[str, Any]:
        """Sync PR with GitHub"""
        conn = await self._get_connection()
        try:
            # Get PR data with repository info
            pr_row = await conn.fetchrow(
                """
                SELECT t.task_id, t.github_pr_number, t.github_url, t.status,
                       p.repository_owner, p.repository_name
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.task_id = $1 AND p.owner_id = $2 AND t.github_pr_number IS NOT NULL
                """,
                pr_id, user_id
            )
            if not pr_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PR {pr_id} not found"
                )
            
            github_pr_number = pr_row["github_pr_number"]
            owner = pr_row["repository_owner"]
            repo = pr_row["repository_name"]
            
            # Fetch from GitHub API if token available
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                try:
                    from packages.integrations.github import GitHubClient
                    from packages.integrations.github.prs import PullRequestOperations
                    
                    client = GitHubClient(token=github_token)
                    pr_ops = PullRequestOperations(client)
                    
                    # Fetch PR from GitHub
                    github_pr = await pr_ops.get_pull_request(owner, repo, github_pr_number)
                    
                    # Map GitHub state to our status
                    state_map = {
                        "open": "open",
                        "closed": "closed"
                    }
                    new_status = state_map.get(github_pr.get("state", "open"), "open")
                    
                    # Check if merged
                    if github_pr.get("merged", False):
                        new_status = "merged"
                    
                    # Update database with latest status
                    await conn.execute(
                        """
                        UPDATE tasks
                        SET status = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE task_id = $2
                        """,
                        new_status, pr_id
                    )
                    
                except Exception:
                    # If GitHub API fails, continue with current data
                    pass
            
            return await self.get_pr(pr_id, user_id)
            
        finally:
            await self._release_connection(conn)

    async def delete_pr(self, pr_id: UUID, user_id: int) -> None:
        """Stop tracking PR"""
        conn = await self._get_connection()
        try:
            # Verify PR exists and user has access
            await self.get_pr(pr_id, user_id)
            
            # Delete PR
            result = await conn.execute(
                "DELETE FROM tasks WHERE task_id = $1",
                pr_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PR {pr_id} not found"
                )
        finally:
            await self._release_connection(conn)

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        if not row:
            return {}
        
        from uuid import UUID
        
        metadata = dict(row.get("metadata", {}))
        ai_analysis = dict(row.get("ai_analysis", {}))
        
        # Map database status to API status
        status_value = row.get("status", "pending")
        if status_value == "closed" and metadata.get("merged"):
            status_value = "merged"
        
        # Get review from metadata/ai_analysis
        review = None
        if ai_analysis:
            review = {
                "summary": ai_analysis.get("summary", ""),
                "approval_status": metadata.get("approval_status", "pending"),
                "comments": ai_analysis.get("comments", []),
                "security_issues": ai_analysis.get("security_issues", []),
                "performance_issues": ai_analysis.get("performance_issues", []),
                "code_quality_score": ai_analysis.get("code_quality_score")
            }
        
        return {
            "id": UUID(str(row["task_id"])),
            "project_id": UUID(str(row["project_id"])),
            "github_pr_url": row.get("github_url", ""),
            "github_pr_number": row.get("github_pr_number"),
            "title": row.get("title", ""),
            "description": row.get("description"),
            "author": metadata.get("author", "unknown"),
            "status": status_value,
            "review_level": metadata.get("review_level", "standard"),
            "assigned_agent_id": UUID(str(row["assigned_to_agent_id"])) if row.get("assigned_to_agent_id") else None,
            "review": review,
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            "reviewed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
        }


# Global service instance
pr_service = PRService()

