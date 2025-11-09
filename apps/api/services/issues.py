"""
Issue Service

Business logic for issue management operations.
"""
import os
import re
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg
from fastapi import HTTPException, status

from apps.api.db import get_db_pool


class IssueService:
    """Service for issue operations"""

    async def _get_connection(self):
        """Get database connection from pool"""
        pool = await get_db_pool()
        return await pool.acquire()
    
    async def _release_connection(self, conn):
        """Release database connection back to pool"""
        pool = await get_db_pool()
        await pool.release(conn)

    async def create_issue(
        self,
        project_id: UUID,
        title: str,
        description: str,
        user_id: int,
        github_issue_url: Optional[str] = None,
        priority: str = "medium",
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new issue"""
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
            
            # Extract GitHub issue number if URL provided
            github_issue_number = None
            if github_issue_url:
                match = re.search(r'/pull/(\d+)$|/issues/(\d+)$', github_issue_url)
                if match:
                    github_issue_number = int(match.group(1) or match.group(2))
            
            task_id = uuid4()
            
            # Insert issue (as task with type)
            row = await conn.fetchrow(
                """
                INSERT INTO tasks (
                    task_id, project_id, title, description,
                    github_issue_number, github_url, type,
                    status, priority, labels, created_by_user_id,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING *
                """,
                task_id, project_id, title, description,
                github_issue_number, github_issue_url, "task",
                "open", priority, labels or [], user_id,
                datetime.utcnow(), datetime.utcnow()
            )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def get_issue(self, issue_id: UUID, user_id: int) -> Dict[str, Any]:
        """Get issue by ID"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT t.* FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE t.task_id = $1 AND p.owner_id = $2 AND t.github_pr_number IS NULL
                """,
                issue_id, user_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Issue {issue_id} not found"
                )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def list_issues(
        self,
        user_id: int,
        project_id: Optional[UUID] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        labels_filter: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List issues with filters"""
        conn = await self._get_connection()
        try:
            # Build query
            where_clauses = ["p.owner_id = $1", "t.github_pr_number IS NULL"]
            params = [user_id]
            param_idx = 2
            
            if project_id:
                where_clauses.append(f"t.project_id = ${param_idx}")
                params.append(project_id)
                param_idx += 1
            
            if status_filter:
                # Map API status to database status
                status_mapping = {
                    "open": "open",
                    "in_progress": "in_progress",
                    "resolved": "closed",
                    "closed": "closed"
                }
                db_status = status_mapping.get(status_filter, status_filter)
                where_clauses.append(f"t.status = ${param_idx}")
                params.append(db_status)
                param_idx += 1
            
            if priority_filter:
                where_clauses.append(f"t.priority = ${param_idx}")
                params.append(priority_filter)
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

    async def get_issue_stats(
        self,
        user_id: int,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get issue statistics"""
        conn = await self._get_connection()
        try:
            where_clauses = ["p.owner_id = $1", "t.github_pr_number IS NULL"]
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
                    COUNT(*) FILTER (WHERE t.status = 'open') as open,
                    COUNT(*) FILTER (WHERE t.status = 'in_progress') as in_progress,
                    COUNT(*) FILTER (WHERE t.status = 'closed') as closed
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE {where_sql}
                """,
                *params
            )
            
            # Get counts by priority
            priority_rows = await conn.fetch(
                f"""
                SELECT t.priority, COUNT(*) as count
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE {where_sql}
                GROUP BY t.priority
                """,
                *params
            )
            
            by_priority = {row["priority"]: row["count"] for row in priority_rows}
            
            return {
                "total": stats_row["total"],
                "open": stats_row["open"],
                "in_progress": stats_row["in_progress"],
                "resolved": stats_row["closed"],  # Map closed to resolved
                "closed": stats_row["closed"],
                "by_priority": by_priority
            }
        finally:
            await self._release_connection(conn)

    async def update_issue(
        self,
        issue_id: UUID,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update issue"""
        conn = await self._get_connection()
        try:
            # Verify issue exists and user has access
            issue = await self.get_issue(issue_id, user_id)
            
            # Build update query
            update_fields = []
            update_params = []
            param_idx = 1
            
            if "title" in updates:
                update_fields.append(f"title = ${param_idx}")
                update_params.append(updates["title"])
                param_idx += 1
            
            if "description" in updates:
                update_fields.append(f"description = ${param_idx}")
                update_params.append(updates["description"])
                param_idx += 1
            
            if "priority" in updates:
                update_fields.append(f"priority = ${param_idx}")
                update_params.append(updates["priority"])
                param_idx += 1
            
            if "status" in updates:
                # Map API status to database status
                status_mapping = {
                    "open": "open",
                    "in_progress": "in_progress",
                    "resolved": "closed",
                    "closed": "closed"
                }
                db_status = status_mapping.get(updates["status"], updates["status"])
                update_fields.append(f"status = ${param_idx}")
                update_params.append(db_status)
                param_idx += 1
                
                # Set completed_at if resolved/closed
                if db_status == "closed":
                    update_fields.append(f"completed_at = ${param_idx}")
                    update_params.append(datetime.utcnow())
                    param_idx += 1
            
            if "labels" in updates:
                update_fields.append(f"labels = ${param_idx}")
                update_params.append(updates["labels"])
                param_idx += 1
            
            if not update_fields:
                return issue
            
            # Add updated_at
            update_fields.append(f"updated_at = ${param_idx}")
            update_params.append(datetime.utcnow())
            param_idx += 1
            
            # Add task_id for WHERE clause
            update_params.append(issue_id)
            
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

    async def assign_agent(
        self,
        issue_id: UUID,
        agent_id: UUID,
        user_id: int
    ) -> Dict[str, Any]:
        """Assign agent to issue"""
        conn = await self._get_connection()
        try:
            # Verify issue exists and user has access
            issue = await self.get_issue(issue_id, user_id)
            
            # Verify agent exists
            agent_row = await conn.fetchrow(
                "SELECT agent_id FROM agents WHERE agent_id = $1",
                agent_id
            )
            if not agent_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
            
            # Update issue
            row = await conn.fetchrow(
                """
                UPDATE tasks
                SET assigned_to_agent_id = $1, status = 'in_progress', started_at = $2, updated_at = $3
                WHERE task_id = $4
                RETURNING *
                """,
                agent_id, datetime.utcnow(), datetime.utcnow(), issue_id
            )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def resolve_issue(
        self,
        issue_id: UUID,
        user_id: int,
        pr_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark issue as resolved"""
        conn = await self._get_connection()
        try:
            # Verify issue exists and user has access
            issue = await self.get_issue(issue_id, user_id)
            
            # Update issue
            updates = {"status": "resolved", "completed_at": datetime.utcnow()}
            if pr_url:
                updates["metadata"] = {**(issue.get("metadata", {})), "resolution_pr_url": pr_url}
            
            return await self.update_issue(issue_id, user_id, updates)
        finally:
            await self._release_connection(conn)

    async def delete_issue(self, issue_id: UUID, user_id: int) -> None:
        """Delete issue"""
        conn = await self._get_connection()
        try:
            # Verify issue exists and user has access
            await self.get_issue(issue_id, user_id)
            
            # Delete issue
            result = await conn.execute(
                "DELETE FROM tasks WHERE task_id = $1",
                issue_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Issue {issue_id} not found"
                )
        finally:
            await self._release_connection(conn)

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        if not row:
            return {}
        
        from uuid import UUID
        
        # Map database status to API status
        status_mapping = {
            "open": "open",
            "in_progress": "in_progress",
            "closed": "resolved",
            "draft": "open"
        }
        api_status = status_mapping.get(row.get("status", "open"), "open")
        
        # Extract resolution PR URL from metadata
        metadata = dict(row.get("metadata", {}))
        resolution_pr_url = metadata.get("resolution_pr_url")
        
        return {
            "id": UUID(str(row["task_id"])),
            "project_id": UUID(str(row["project_id"])),
            "title": row["title"],
            "description": row.get("description", ""),
            "github_issue_url": row.get("github_url"),
            "github_issue_number": row.get("github_issue_number"),
            "priority": row.get("priority", "medium"),
            "status": api_status,
            "labels": list(row.get("labels", [])),
            "assigned_agent_id": UUID(str(row["assigned_to_agent_id"])) if row.get("assigned_to_agent_id") else None,
            "resolution_pr_url": resolution_pr_url,
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            "resolved_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
        }


# Global service instance
issue_service = IssueService()

