"""
Analytics Service

Business logic for analytics and metrics operations.
"""
import os
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import asyncpg
from fastapi import HTTPException, status

from apps.api.db import get_db_pool


class AnalyticsService:
    """Service for analytics operations"""

    async def _get_connection(self):
        """Get database connection from pool"""
        pool = await get_db_pool()
        return await pool.acquire()
    
    async def _release_connection(self, conn):
        """Release database connection back to pool"""
        pool = await get_db_pool()
        await pool.release(conn)

    async def get_dashboard_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard overview metrics"""
        conn = await self._get_connection()
        try:
            # Get project counts
            projects_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as total FROM projects WHERE owner_id = $1
                """,
                user_id
            )
            
            # Get issue counts
            issues_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'closed') as resolved,
                    COUNT(*) FILTER (WHERE github_pr_number IS NULL) as issues
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE p.owner_id = $1
                """,
                user_id
            )
            
            # Get PR counts
            prs_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'closed') as reviewed
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE p.owner_id = $1 AND t.github_pr_number IS NOT NULL
                """,
                user_id
            )
            
            # Get active agents count
            agents_row = await conn.fetchrow(
                """
                SELECT COUNT(DISTINCT a.agent_id) as active
                FROM agents a
                JOIN agent_executions ae ON ae.agent_id = a.agent_id
                JOIN projects p ON p.project_id = ae.project_id
                WHERE p.owner_id = $1 AND ae.status = 'running'
                """,
                user_id
            )
            
            # Get recent activity (last 10 items)
            recent_activity = await conn.fetch(
                """
                SELECT 
                    t.task_id as id,
                    t.title,
                    t.status,
                    t.created_at,
                    'task' as type,
                    p.name as project_name
                FROM tasks t
                JOIN projects p ON p.project_id = t.project_id
                WHERE p.owner_id = $1
                ORDER BY t.created_at DESC
                LIMIT 10
                """,
                user_id
            )
            
            return {
                "total_projects": projects_row["total"],
                "total_issues": issues_row["issues"] if issues_row else 0,
                "resolved_issues": issues_row["resolved"] if issues_row else 0,
                "total_prs": prs_row["total"] if prs_row else 0,
                "reviewed_prs": prs_row["reviewed"] if prs_row else 0,
                "active_agents": agents_row["active"] if agents_row else 0,
                "recent_activity": [
                    {
                        "id": str(row["id"]),
                        "title": row["title"],
                        "status": row["status"],
                        "type": row["type"],
                        "project_name": row["project_name"],
                        "created_at": row["created_at"].isoformat() if row.get("created_at") else None
                    }
                    for row in recent_activity
                ]
            }
        finally:
            await self._release_connection(conn)

    async def get_project_metrics(
        self,
        project_id: UUID,
        user_id: int
    ) -> Dict[str, Any]:
        """Get project-level metrics"""
        conn = await self._get_connection()
        try:
            # Verify project access
            project_row = await conn.fetchrow(
                "SELECT project_id FROM projects WHERE project_id = $1 AND owner_id = $2",
                project_id, user_id
            )
            if not project_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project {project_id} not found"
                )
            
            # Get issue metrics
            issues_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'closed') as resolved,
                    COUNT(*) FILTER (WHERE status = 'open' OR status = 'in_progress') as open
                FROM tasks
                WHERE project_id = $1 AND github_pr_number IS NULL
                """,
                project_id
            )
            
            # Get PR metrics
            prs_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'closed') as reviewed
                FROM tasks
                WHERE project_id = $1 AND github_pr_number IS NOT NULL
                """,
                project_id
            )
            
            # Get agent metrics
            agents_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT ae.agent_id) as total,
                    COUNT(DISTINCT ae.agent_id) FILTER (WHERE ae.status = 'running') as active
                FROM agent_executions ae
                WHERE ae.project_id = $1
                """,
                project_id
            )
            
            # Calculate average resolution time
            resolution_time_row = await conn.fetchrow(
                """
                SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 3600) as avg_hours
                FROM tasks
                WHERE project_id = $1 AND completed_at IS NOT NULL AND started_at IS NOT NULL
                """,
                project_id
            )
            
            # Calculate average review time
            review_time_row = await conn.fetchrow(
                """
                SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 3600) as avg_hours
                FROM tasks
                WHERE project_id = $1 AND github_pr_number IS NOT NULL 
                    AND completed_at IS NOT NULL AND started_at IS NOT NULL
                """,
                project_id
            )
            
            return {
                "project_id": str(project_id),
                "total_issues": issues_row["total"] if issues_row else 0,
                "resolved_issues": issues_row["resolved"] if issues_row else 0,
                "open_issues": issues_row["open"] if issues_row else 0,
                "total_prs": prs_row["total"] if prs_row else 0,
                "reviewed_prs": prs_row["reviewed"] if prs_row else 0,
                "total_agents": agents_row["total"] if agents_row else 0,
                "active_agents": agents_row["active"] if agents_row else 0,
                "avg_resolution_time_hours": float(resolution_time_row["avg_hours"]) if resolution_time_row and resolution_time_row["avg_hours"] else None,
                "avg_review_time_hours": float(review_time_row["avg_hours"]) if review_time_row and review_time_row["avg_hours"] else None,
                "code_quality_score": None  # Would need separate tracking
            }
        finally:
            await self._release_connection(conn)

    async def get_agent_metrics(
        self,
        agent_id: UUID,
        user_id: int
    ) -> Dict[str, Any]:
        """Get agent performance metrics"""
        conn = await self._get_connection()
        try:
            # Verify agent access
            agent_row = await conn.fetchrow(
                """
                SELECT a.agent_id FROM agents a
                JOIN agent_executions ae ON ae.agent_id = a.agent_id
                JOIN projects p ON p.project_id = ae.project_id
                WHERE a.agent_id = $1 AND p.owner_id = $2
                LIMIT 1
                """,
                agent_id, user_id
            )
            if not agent_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
            
            # Get execution metrics
            metrics_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as executions,
                    COUNT(*) FILTER (WHERE status = 'success') as successes,
                    COUNT(*) FILTER (WHERE status = 'failure') as failures,
                    AVG(execution_time_ms) / 60000.0 as avg_time_minutes
                FROM agent_executions
                WHERE agent_id = $1
                """,
                agent_id
            )
            
            executions = metrics_row["executions"] if metrics_row else 0
            successes = metrics_row["successes"] if metrics_row else 0
            success_rate = (successes / executions * 100) if executions > 0 else 0.0
            
            return {
                "agent_id": str(agent_id),
                "executions": executions,
                "successes": successes,
                "failures": metrics_row["failures"] if metrics_row else 0,
                "avg_execution_time_minutes": float(metrics_row["avg_time_minutes"]) if metrics_row and metrics_row["avg_time_minutes"] else 0.0,
                "success_rate": success_rate
            }
        finally:
            await self._release_connection(conn)

    async def get_timeseries_metrics(
        self,
        metric_type: str,
        time_range: str,
        user_id: int,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get time series metrics"""
        conn = await self._get_connection()
        try:
            # Determine time window
            now = datetime.utcnow()
            time_deltas = {
                "day": timedelta(days=1),
                "week": timedelta(weeks=1),
                "month": timedelta(days=30),
                "quarter": timedelta(days=90),
                "year": timedelta(days=365)
            }
            start_time = now - time_deltas.get(time_range, timedelta(days=30))
            
            # Build query based on metric type
            where_clauses = ["p.owner_id = $1", "t.created_at >= $2"]
            params = [user_id, start_time]
            param_idx = 3
            
            if project_id:
                where_clauses.append(f"t.project_id = ${param_idx}")
                params.append(project_id)
                param_idx += 1
            
            where_sql = " AND ".join(where_clauses)
            
            # Query based on metric type
            if metric_type == "issues_resolved":
                rows = await conn.fetch(
                    f"""
                    SELECT 
                        DATE_TRUNC('day', t.completed_at) as timestamp,
                        COUNT(*) as value
                    FROM tasks t
                    JOIN projects p ON p.project_id = t.project_id
                    WHERE {where_sql} AND t.github_pr_number IS NULL 
                        AND t.status = 'closed' AND t.completed_at IS NOT NULL
                    GROUP BY DATE_TRUNC('day', t.completed_at)
                    ORDER BY timestamp
                    """,
                    *params
                )
            elif metric_type == "prs_reviewed":
                rows = await conn.fetch(
                    f"""
                    SELECT 
                        DATE_TRUNC('day', t.completed_at) as timestamp,
                        COUNT(*) as value
                    FROM tasks t
                    JOIN projects p ON p.project_id = t.project_id
                    WHERE {where_sql} AND t.github_pr_number IS NOT NULL 
                        AND t.status = 'closed' AND t.completed_at IS NOT NULL
                    GROUP BY DATE_TRUNC('day', t.completed_at)
                    ORDER BY timestamp
                    """,
                    *params
                )
            elif metric_type == "agent_executions":
                rows = await conn.fetch(
                    f"""
                    SELECT 
                        DATE_TRUNC('day', ae.started_at) as timestamp,
                        COUNT(*) as value
                    FROM agent_executions ae
                    JOIN projects p ON p.project_id = ae.project_id
                    WHERE p.owner_id = $1 AND ae.started_at >= $2
                    GROUP BY DATE_TRUNC('day', ae.started_at)
                    ORDER BY timestamp
                    """,
                    user_id, start_time
                )
            else:
                # Default: return empty series
                rows = []
            
            data = [
                {
                    "timestamp": row["timestamp"].isoformat() if row.get("timestamp") else None,
                    "value": float(row["value"]),
                    "metadata": None
                }
                for row in rows
            ]
            
            values = [d["value"] for d in data]
            total = sum(values) if values else 0.0
            average = (total / len(values)) if values else 0.0
            
            return {
                "metric_type": metric_type,
                "time_range": time_range,
                "data": data,
                "total": total,
                "average": average,
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0
            }
        finally:
            await self._release_connection(conn)

    async def get_performance_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get system performance metrics"""
        # These would typically come from monitoring/observability system
        # For now, return placeholder data
        return {
            "avg_response_time_ms": 0.0,
            "requests_per_minute": 0.0,
            "error_rate": 0.0,
            "active_users": 1
        }

    async def record_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: int
    ) -> None:
        """Record custom analytics event"""
        # TODO: Implement event tracking
        # Would typically write to analytics/events table or external service
        pass


# Global service instance
analytics_service = AnalyticsService()

