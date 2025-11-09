"""
Database service for Agents operations.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class AgentsService:
    """Database service for Agents operations"""
    
    def __init__(self, pool: Pool):
        """Initialize agents service"""
        self.pool = pool
    
    async def create_agent(
        self,
        project_id: UUID,
        name: str,
        agent_type: str,
        model_provider: str,
        model_name: str,
        config: Dict[str, Any],
        created_by_user_id: int
    ) -> Dict[str, Any]:
        """Create a new agent"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO agents (
                    project_id, name, agent_type, model_provider, model_name,
                    capabilities, config, status, created_by_user_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING 
                    agent_id, project_id, name, agent_type, model_provider,
                    model_name, capabilities, config, status,
                    is_active, created_at, updated_at
                """,
                project_id,
                name,
                agent_type,
                model_provider,
                model_name,
                config.get("capabilities", []),  # capabilities
                config,  # config
                "pending",  # status
                created_by_user_id
            )
            
            return dict(row)
    
    async def get_agent(self, agent_id: UUID, user_id: int) -> Optional[Dict[str, Any]]:
        """Get agent by ID, verifying user access via project"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    a.agent_id, a.project_id, a.name, a.agent_type,
                    a.model_provider, a.model_name, a.capabilities,
                    a.config, a.status, a.is_active,
                    a.success_rate, a.avg_execution_time_ms,
                    a.created_at, a.updated_at, a.last_execution_at
                FROM agents a
                JOIN projects p ON a.project_id = p.project_id
                WHERE a.agent_id = $1 AND (p.owner_id = $2 OR p.is_public = true)
                """,
                agent_id,
                user_id
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def list_agents(
        self,
        user_id: int,
        project_id: Optional[UUID] = None,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """List agents with filters and pagination"""
        async with self.pool.acquire() as conn:
            # Build WHERE clause
            conditions = ["p.owner_id = $1 OR p.is_public = true"]
            params: List[Any] = [user_id]
            param_count = 1
            
            if project_id:
                param_count += 1
                conditions.append(f"a.project_id = ${param_count}")
                params.append(project_id)
            
            if agent_type:
                param_count += 1
                conditions.append(f"a.agent_type = ${param_count}")
                params.append(agent_type)
            
            if status:
                param_count += 1
                conditions.append(f"a.status = ${param_count}")
                params.append(status)
            
            if is_active is not None:
                param_count += 1
                conditions.append(f"a.is_active = ${param_count}")
                params.append(is_active)
            
            where_clause = " AND ".join(conditions)
            
            # Get total count
            count_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*) as total
                FROM agents a
                JOIN projects p ON a.project_id = p.project_id
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
                    a.agent_id, a.project_id, a.name, a.agent_type,
                    a.model_provider, a.model_name, a.capabilities,
                    a.config, a.status, a.is_active,
                    a.success_rate, a.avg_execution_time_ms,
                    a.created_at, a.updated_at, a.last_execution_at
                FROM agents a
                JOIN projects p ON a.project_id = p.project_id
                WHERE {where_clause}
                ORDER BY a.created_at DESC
                LIMIT ${param_count - 1} OFFSET ${param_count}
                """,
                *params
            )
            
            return [dict(row) for row in rows], total
    
    async def update_agent(
        self,
        agent_id: UUID,
        user_id: int,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update agent, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access
            agent = await self.get_agent(agent_id, user_id)
            if not agent:
                return None
            
            # Build update query
            updates = []
            params: List[Any] = []
            param_count = 0
            
            if config is not None:
                param_count += 1
                updates.append(f"config = ${param_count}")
                params.append(config)
            
            if status is not None:
                param_count += 1
                updates.append(f"status = ${param_count}")
                params.append(status)
                
                # Update last_execution_at if starting/completing
                if status == "running":
                    updates.append("last_execution_at = CURRENT_TIMESTAMP")
                elif status in ["completed", "failed", "cancelled"]:
                    updates.append("last_execution_at = CURRENT_TIMESTAMP")
            
            if not updates:
                return agent
            
            # Add updated_at
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add WHERE params
            param_count += 1
            params.append(agent_id)
            
            row = await conn.fetchrow(
                f"""
                UPDATE agents
                SET {', '.join(updates)}
                WHERE agent_id = ${param_count}
                RETURNING 
                    agent_id, project_id, name, agent_type,
                    model_provider, model_name, capabilities,
                    config, status, is_active,
                    success_rate, avg_execution_time_ms,
                    created_at, updated_at, last_execution_at
                """,
                *params
            )
            
            return dict(row) if row else None
    
    async def delete_agent(self, agent_id: UUID, user_id: int) -> bool:
        """Delete agent, verifying user access"""
        async with self.pool.acquire() as conn:
            # Verify access
            agent = await self.get_agent(agent_id, user_id)
            if not agent:
                return False
            
            # TODO: Cancel any running executions
            
            # Delete agent
            result = await conn.execute(
                "DELETE FROM agents WHERE agent_id = $1",
                agent_id
            )
            
            return result == "DELETE 1"
    
    async def get_agent_logs(
        self,
        agent_id: UUID,
        user_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get agent execution logs"""
        async with self.pool.acquire() as conn:
            # Verify access
            agent = await self.get_agent(agent_id, user_id)
            if not agent:
                return []
            
            # Get logs from agent_executions table
            rows = await conn.fetch(
                """
                SELECT 
                    execution_id, agent_id, task_id, project_id,
                    status, input_tokens, output_tokens, cost_usd,
                    started_at, completed_at, result, error_message
                FROM agent_executions
                WHERE agent_id = $1
                ORDER BY started_at DESC
                LIMIT $2
                """,
                agent_id,
                limit
            )
            
            return [dict(row) for row in rows]

