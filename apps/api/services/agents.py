"""
Agent Service

Business logic for agent management operations.
"""
import os
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg
from fastapi import HTTPException, status

from packages.db.db_connection import get_db_connection


class AgentService:
    """Service for agent operations"""

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

    async def create_agent(
        self,
        project_id: UUID,
        agent_type: str,
        config: Dict[str, Any],
        user_id: int,
        auto_start: bool = True
    ) -> Dict[str, Any]:
        """Create a new agent"""
        agent_id = uuid4()
        
        # Map agent_type to database agent_type
        type_mapping = {
            "issue_resolver": "debugger",
            "pr_reviewer": "reviewer",
            "code_analyzer": "analytics",
            "custom": "custom"
        }
        db_agent_type = type_mapping.get(agent_type, "custom")
        
        # Default model configuration
        model_provider = config.get("model_provider", "anthropic")
        model_name = config.get("model_name", "claude-3-5-sonnet-20241022")
        
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
            
            # Create agent
            row = await conn.fetchrow(
                """
                INSERT INTO agents (
                    agent_id, name, display_name, agent_type,
                    model_provider, model_name, configuration,
                    is_active, created_at, updated_at, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
                """,
                agent_id,
                f"{agent_type}-{agent_id.hex[:8]}",
                f"{agent_type.replace('_', ' ').title()} Agent",
                db_agent_type,
                model_provider,
                model_name,
                config,
                True,
                datetime.utcnow(),
                datetime.utcnow(),
                user_id
            )
            
            agent = self._row_to_dict(row)
            
            # If auto_start, create execution record
            if auto_start:
                await self._create_execution(conn, agent_id, project_id)
            
            return agent
        finally:
            await self._release_connection(conn)

    async def _create_execution(
        self,
        conn: asyncpg.Connection,
        agent_id: UUID,
        project_id: UUID
    ) -> None:
        """Create agent execution record"""
        execution_id = uuid4()
        await conn.execute(
            """
            INSERT INTO agent_executions (
                execution_id, agent_id, project_id, status, started_at
            ) VALUES ($1, $2, $3, $4, $5)
            """,
            execution_id, agent_id, project_id, "pending", datetime.utcnow()
        )

    async def get_agent(self, agent_id: UUID, user_id: int) -> Dict[str, Any]:
        """Get agent by ID"""
        conn = await self._get_connection()
        try:
            # Get agent with project ownership check
            row = await conn.fetchrow(
                """
                SELECT a.*, ae.project_id, ae.status as execution_status
                FROM agents a
                LEFT JOIN agent_executions ae ON ae.agent_id = a.agent_id
                LEFT JOIN projects p ON p.project_id = ae.project_id
                WHERE a.agent_id = $1 AND (p.owner_id = $2 OR p.owner_id IS NULL)
                ORDER BY ae.created_at DESC
                LIMIT 1
                """,
                agent_id, user_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def list_agents(
        self,
        user_id: int,
        project_id: Optional[UUID] = None,
        agent_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List agents with filters"""
        conn = await self._get_connection()
        try:
            # Build query with joins for project ownership
            where_clauses = ["p.owner_id = $1"]
            params = [user_id]
            param_idx = 2
            
            if project_id:
                where_clauses.append(f"ae.project_id = ${param_idx}")
                params.append(project_id)
                param_idx += 1
            
            if agent_type:
                type_mapping = {
                    "issue_resolver": "debugger",
                    "pr_reviewer": "reviewer",
                    "code_analyzer": "analytics",
                    "custom": "custom"
                }
                db_type = type_mapping.get(agent_type, agent_type)
                where_clauses.append(f"a.agent_type = ${param_idx}")
                params.append(db_type)
                param_idx += 1
            
            where_sql = " AND ".join(where_clauses)
            
            # Get total count
            total_row = await conn.fetchrow(
                f"""
                SELECT COUNT(DISTINCT a.agent_id) as total
                FROM agents a
                JOIN agent_executions ae ON ae.agent_id = a.agent_id
                JOIN projects p ON p.project_id = ae.project_id
                WHERE {where_sql}
                """,
                *params
            )
            total = total_row["total"]
            
            # Get paginated results
            offset = (page - 1) * page_size
            rows = await conn.fetch(
                f"""
                SELECT DISTINCT a.* FROM agents a
                JOIN agent_executions ae ON ae.agent_id = a.agent_id
                JOIN projects p ON p.project_id = ae.project_id
                WHERE {where_sql}
                ORDER BY a.created_at DESC
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

    async def update_agent(
        self,
        agent_id: UUID,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update agent"""
        conn = await self._get_connection()
        try:
            # Verify agent exists and user has access
            agent = await self.get_agent(agent_id, user_id)
            
            # Build update query
            update_fields = []
            update_params = []
            param_idx = 1
            
            if "config" in updates:
                update_fields.append(f"configuration = ${param_idx}")
                update_params.append(updates["config"])
                param_idx += 1
            
            if not update_fields:
                return agent
            
            # Add updated_at
            update_fields.append(f"updated_at = ${param_idx}")
            update_params.append(datetime.utcnow())
            param_idx += 1
            
            # Add agent_id for WHERE clause
            update_params.append(agent_id)
            
            # Execute update
            update_sql = ", ".join(update_fields)
            row = await conn.fetchrow(
                f"""
                UPDATE agents
                SET {update_sql}
                WHERE agent_id = ${param_idx}
                RETURNING *
                """,
                *update_params
            )
            
            return self._row_to_dict(row)
        finally:
            await self._release_connection(conn)

    async def start_agent(self, agent_id: UUID, user_id: int) -> Dict[str, Any]:
        """Start agent execution"""
        conn = await self._get_connection()
        try:
            agent = await self.get_agent(agent_id, user_id)
            
            # Get latest execution
            exec_row = await conn.fetchrow(
                """
                SELECT execution_id, status FROM agent_executions
                WHERE agent_id = $1
                ORDER BY created_at DESC LIMIT 1
                """,
                agent_id
            )
            
            if exec_row and exec_row["status"] not in ["pending", "failure"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Agent cannot be started from status: {exec_row['status']}"
                )
            
            # Create new execution or update existing
            if exec_row and exec_row["status"] == "pending":
                execution_id = exec_row["execution_id"]
                await conn.execute(
                    """
                    UPDATE agent_executions
                    SET status = 'running', started_at = $1
                    WHERE execution_id = $2
                    """,
                    datetime.utcnow(), execution_id
                )
            else:
                # Get project_id from latest execution
                project_row = await conn.fetchrow(
                    """
                    SELECT project_id FROM agent_executions
                    WHERE agent_id = $1
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    agent_id
                )
                if project_row:
                    await self._create_execution(conn, agent_id, project_row["project_id"])
            
            return await self.get_agent(agent_id, user_id)
        finally:
            await self._release_connection(conn)

    async def cancel_agent(self, agent_id: UUID, user_id: int) -> Dict[str, Any]:
        """Cancel agent execution"""
        conn = await self._get_connection()
        try:
            agent = await self.get_agent(agent_id, user_id)
            
            # Update latest execution
            result = await conn.execute(
                """
                UPDATE agent_executions
                SET status = 'timeout', completed_at = $1
                WHERE execution_id = (
                    SELECT execution_id FROM agent_executions
                    WHERE agent_id = $2 AND status = 'running'
                    ORDER BY created_at DESC LIMIT 1
                )
                """,
                datetime.utcnow(), agent_id
            )
            
            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Agent is not currently running"
                )
            
            return await self.get_agent(agent_id, user_id)
        finally:
            await self._release_connection(conn)

    async def get_agent_logs(
        self,
        agent_id: UUID,
        user_id: int,
        level: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get agent logs"""
        # Verify agent exists and user has access
        await self.get_agent(agent_id, user_id)
        
        # TODO: Implement log retrieval from structured logging system
        # For now, return empty logs
        return {
            "agent_id": str(agent_id),
            "logs": []
        }

    async def delete_agent(self, agent_id: UUID, user_id: int) -> None:
        """Delete agent"""
        conn = await self._get_connection()
        try:
            # Verify agent exists and user has access
            agent = await self.get_agent(agent_id, user_id)
            
            # Check if agent has running executions
            running = await conn.fetchrow(
                """
                SELECT COUNT(*) as count FROM agent_executions
                WHERE agent_id = $1 AND status = 'running'
                """,
                agent_id
            )
            
            if running and running["count"] > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete agent with running executions"
                )
            
            # Delete agent (cascade will handle executions)
            result = await conn.execute(
                "DELETE FROM agents WHERE agent_id = $1",
                agent_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
        finally:
            await self._release_connection(conn)

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        if not row:
            return {}
        
        from uuid import UUID
        
        # Map database agent_type back to API agent_type
        type_mapping = {
            "debugger": "issue_resolver",
            "reviewer": "pr_reviewer",
            "analytics": "code_analyzer",
            "custom": "custom"
        }
        api_agent_type = type_mapping.get(row["agent_type"], "custom")
        
        # Get execution status
        status_value = row.get("execution_status", "pending")
        if status_value == "success":
            status_value = "completed"
        elif status_value == "failure":
            status_value = "failed"
        elif status_value == "timeout":
            status_value = "cancelled"
        
        project_id = row.get("project_id")
        
        return {
            "id": UUID(str(row["agent_id"])),
            "project_id": UUID(str(project_id)) if project_id else None,
            "agent_type": api_agent_type,
            "status": status_value,
            "config": dict(row.get("configuration", {})),
            "result": None,
            "error": None,
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            "started_at": None,
            "completed_at": None,
        }


# Global service instance
agent_service = AgentService()

