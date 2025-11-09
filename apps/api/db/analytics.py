"""
Database service for Analytics operations.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Database service for Analytics operations"""
    
    def __init__(self, pool: Pool):
        """Initialize analytics service"""
        self.pool = pool
    
    async def get_dashboard_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard overview metrics"""
        async with self.pool.acquire() as conn:
            # Get project counts
            project_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM projects
                WHERE owner_id = $1 OR is_public = true
                """,
                user_id
            )
            
            # Get issue counts
            issue_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE t.status = 'closed') as resolved
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE (p.owner_id = $1 OR p.is_public = true)
                    AND t.github_issue_number IS NOT NULL
                    AND t.github_pr_number IS NULL
                """,
                user_id
            )
            
            # Get PR counts
            pr_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE t.metadata->>'pr_status' IN ('approved', 'merged')) as reviewed
                FROM tasks t
                JOIN projects p ON t.project_id = p.project_id
                WHERE (p.owner_id = $1 OR p.is_public = true)
                    AND t.github_pr_number IS NOT NULL
                """,
                user_id
            )
            
            # Get active agents count
            active_agents = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM agents
                WHERE is_active = true
                """
            )
            
            # Get recent activity (last 10 activities)
            recent_activity = await conn.fetch(
                """
                SELECT 
                    activity_id, project_id, task_id, user_id, agent_id,
                    activity_type, description, created_at
                FROM activity_feed
                WHERE project_id IN (
                    SELECT project_id FROM projects WHERE owner_id = $1 OR is_public = true
                )
                ORDER BY created_at DESC
                LIMIT 10
                """,
                user_id
            )
            
            return {
                "total_projects": project_count or 0,
                "total_issues": issue_stats["total"] if issue_stats else 0,
                "resolved_issues": issue_stats["resolved"] if issue_stats else 0,
                "total_prs": pr_stats["total"] if pr_stats else 0,
                "reviewed_prs": pr_stats["reviewed"] if pr_stats else 0,
                "active_agents": active_agents or 0,
                "recent_activity": [dict(row) for row in recent_activity]
            }
    
    async def get_project_metrics(self, project_id: UUID, user_id: int) -> Optional[Dict[str, Any]]:
        """Get project-level metrics"""
        async with self.pool.acquire() as conn:
            # Verify project access
            project = await conn.fetchrow(
                """
                SELECT project_id
                FROM projects
                WHERE project_id = $1 AND (owner_id = $2 OR is_public = true)
                """,
                project_id,
                user_id
            )
            
            if not project:
                return None
            
            # Get issue stats
            issue_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'closed') as resolved,
                    COUNT(*) FILTER (WHERE status = 'open') as open,
                    AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600) as avg_resolution_time_hours
                FROM tasks
                WHERE project_id = $1
                    AND github_issue_number IS NOT NULL
                    AND github_pr_number IS NULL
                """,
                project_id
            )
            
            # Get PR stats
            pr_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE metadata->>'pr_status' IN ('approved', 'merged')) as reviewed,
                    AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600) as avg_review_time_hours
                FROM tasks
                WHERE project_id = $1
                    AND github_pr_number IS NOT NULL
                """,
                project_id
            )
            
            # Get agent stats
            agent_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_active = true) as active
                FROM agents
                WHERE project_id = $1
                """,
                project_id
            )
            
            # Get code quality score (from project metadata or average of PR reviews)
            code_quality = await conn.fetchval(
                """
                SELECT AVG((metadata->>'review'->>'code_quality_score')::float)
                FROM tasks
                WHERE project_id = $1
                    AND github_pr_number IS NOT NULL
                    AND metadata->>'review' IS NOT NULL
                """,
                project_id
            )
            
            return {
                "project_id": project_id,
                "total_issues": issue_stats["total"] if issue_stats else 0,
                "resolved_issues": issue_stats["resolved"] if issue_stats else 0,
                "open_issues": issue_stats["open"] if issue_stats else 0,
                "total_prs": pr_stats["total"] if pr_stats else 0,
                "reviewed_prs": pr_stats["reviewed"] if pr_stats else 0,
                "total_agents": agent_stats["total"] if agent_stats else 0,
                "active_agents": agent_stats["active"] if agent_stats else 0,
                "avg_resolution_time_hours": float(issue_stats["avg_resolution_time_hours"]) if issue_stats and issue_stats["avg_resolution_time_hours"] else None,
                "avg_review_time_hours": float(pr_stats["avg_review_time_hours"]) if pr_stats and pr_stats["avg_review_time_hours"] else None,
                "code_quality_score": float(code_quality) if code_quality else None
            }
    
    async def get_agent_metrics(self, agent_id: UUID, user_id: int) -> Optional[Dict[str, Any]]:
        """Get agent performance metrics"""
        async with self.pool.acquire() as conn:
            # Verify agent exists and user has access via project
            agent = await conn.fetchrow(
                """
                SELECT a.agent_id, a.project_id
                FROM agents a
                JOIN projects p ON a.project_id = p.project_id
                WHERE a.agent_id = $1 AND (p.owner_id = $2 OR p.is_public = true)
                """,
                agent_id,
                user_id
            )
            
            if not agent:
                return None
            
            # Get execution stats
            execution_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as executions,
                    COUNT(*) FILTER (WHERE status = 'success') as successes,
                    COUNT(*) FILTER (WHERE status = 'failure') as failures,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 60) as avg_execution_time_minutes
                FROM agent_executions
                WHERE agent_id = $1
                """,
                agent_id
            )
            
            if not execution_stats:
                return {
                    "agent_id": agent_id,
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "avg_execution_time_minutes": 0.0,
                    "success_rate": 0.0
                }
            
            executions = execution_stats["executions"] or 0
            successes = execution_stats["successes"] or 0
            success_rate = (successes / executions * 100) if executions > 0 else 0.0
            
            return {
                "agent_id": agent_id,
                "executions": executions,
                "successes": successes,
                "failures": execution_stats["failures"] or 0,
                "avg_execution_time_minutes": float(execution_stats["avg_execution_time_minutes"]) if execution_stats["avg_execution_time_minutes"] else 0.0,
                "success_rate": success_rate
            }
    
    async def get_metric_series(
        self,
        user_id: int,
        metric_type: str,
        time_range: str,
        project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get time series metric data"""
        async with self.pool.acquire() as conn:
            # Determine time window
            time_windows = {
                "day": timedelta(days=1),
                "week": timedelta(weeks=1),
                "month": timedelta(days=30),
                "quarter": timedelta(days=90),
                "year": timedelta(days=365)
            }
            window = time_windows.get(time_range, timedelta(days=30))
            start_time = datetime.utcnow() - window
            
            # Build project filter
            project_filter = ""
            params: List[Any] = [user_id, start_time]
            param_count = 2
            
            if project_id:
                param_count += 1
                project_filter = f"AND t.project_id = ${param_count}"
                params.append(project_id)
            
            # Query based on metric type
            if metric_type == "issues_resolved":
                rows = await conn.fetch(
                    f"""
                    SELECT 
                        DATE_TRUNC('day', completed_at) as timestamp,
                        COUNT(*) as value
                    FROM tasks t
                    JOIN projects p ON t.project_id = p.project_id
                    WHERE (p.owner_id = $1 OR p.is_public = true)
                        AND t.github_issue_number IS NOT NULL
                        AND t.github_pr_number IS NULL
                        AND t.status = 'closed'
                        AND t.completed_at >= $2
                        {project_filter}
                    GROUP BY DATE_TRUNC('day', completed_at)
                    ORDER BY timestamp
                    """,
                    *params
                )
            elif metric_type == "prs_reviewed":
                rows = await conn.fetch(
                    f"""
                    SELECT 
                        DATE_TRUNC('day', completed_at) as timestamp,
                        COUNT(*) as value
                    FROM tasks t
                    JOIN projects p ON t.project_id = p.project_id
                    WHERE (p.owner_id = $1 OR p.is_public = true)
                        AND t.github_pr_number IS NOT NULL
                        AND t.metadata->>'pr_status' IN ('approved', 'merged')
                        AND t.completed_at >= $2
                        {project_filter}
                    GROUP BY DATE_TRUNC('day', completed_at)
                    ORDER BY timestamp
                    """,
                    *params
                )
            elif metric_type == "agent_executions":
                rows = await conn.fetch(
                    f"""
                    SELECT 
                        DATE_TRUNC('day', started_at) as timestamp,
                        COUNT(*) as value
                    FROM agent_executions ae
                    JOIN agents a ON ae.agent_id = a.agent_id
                    JOIN projects p ON a.project_id = p.project_id
                    WHERE (p.owner_id = $1 OR p.is_public = true)
                        AND ae.started_at >= $2
                        {project_filter.replace('t.project_id', 'a.project_id') if project_id else ''}
                    GROUP BY DATE_TRUNC('day', started_at)
                    ORDER BY timestamp
                    """,
                    *params
                )
            else:
                return []
            
            return [
                {
                    "timestamp": row["timestamp"],
                    "value": float(row["value"]),
                    "metadata": None
                }
                for row in rows
            ]

