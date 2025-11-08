"""
Database service for Skills operations.

Handles all database interactions for Skills marketplace, execution tracking,
and analytics.
"""
import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg
from asyncpg import Pool, Connection

from .models import Skill, ExecutionContext, ExecutionStatus

logger = logging.getLogger(__name__)


class SkillsDatabaseService:
    """Database service for Skills operations"""
    
    def __init__(self, pool: Pool):
        """
        Initialize database service
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    async def get_skill_by_id(self, skill_id: UUID) -> Optional[Dict[str, Any]]:
        """Get skill by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, name, slug, version, description, detailed_description,
                    category, tags, prompt_template, input_schema, output_schema,
                    examples, model_preferences, validation_rules, dependencies,
                    author_id, author_name, author_email, organization,
                    visibility, license, pricing_model, status,
                    download_count, installation_count, execution_count,
                    avg_rating, review_count, quality_score,
                    created_at, updated_at, published_at
                FROM skills
                WHERE id = $1 AND status != 'archived'
                """,
                skill_id
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def get_skill_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get skill by slug"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, name, slug, version, description, detailed_description,
                    category, tags, prompt_template, input_schema, output_schema,
                    examples, model_preferences, validation_rules, dependencies,
                    author_id, author_name, author_email, organization,
                    visibility, license, pricing_model, status,
                    download_count, installation_count, execution_count,
                    avg_rating, review_count, quality_score,
                    created_at, updated_at, published_at
                FROM skills
                WHERE slug = $1 AND status != 'archived'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                slug
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def list_skills(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        visibility: Optional[str] = None,
        status: str = "active",
        sort: str = "updated_at",
        order: str = "desc",
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List skills with filtering and pagination"""
        async with self.pool.acquire() as conn:
            # Build query
            conditions = ["status = $1"]
            params = [status]
            param_idx = 2
            
            if category:
                conditions.append(f"category = ${param_idx}")
                params.append(category)
                param_idx += 1
            
            if tags:
                conditions.append(f"tags && ${param_idx}")
                params.append(tags)
                param_idx += 1
            
            if search:
                conditions.append(
                    f"(name ILIKE ${param_idx} OR description ILIKE ${param_idx})"
                )
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
                param_idx += 2
            
            if visibility:
                conditions.append(f"visibility = ${param_idx}")
                params.append(visibility)
                param_idx += 1
            
            where_clause = " AND ".join(conditions)
            
            # Validate sort column
            valid_sorts = {
                "created_at": "created_at",
                "updated_at": "updated_at",
                "download_count": "download_count",
                "avg_rating": "avg_rating",
                "execution_count": "execution_count"
            }
            sort_col = valid_sorts.get(sort, "updated_at")
            order_dir = "DESC" if order.lower() == "desc" else "ASC"
            
            query = f"""
                SELECT 
                    id, name, slug, version, description, detailed_description,
                    category, tags, author_id, author_name,
                    visibility, license, pricing_model, status,
                    download_count, installation_count, execution_count,
                    avg_rating, review_count,
                    created_at, updated_at
                FROM skills
                WHERE {where_clause}
                ORDER BY {sort_col} {order_dir}
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def create_skill(
        self,
        skill_data: Dict[str, Any],
        author_id: UUID
    ) -> Dict[str, Any]:
        """Create a new skill"""
        async with self.pool.acquire() as conn:
            skill_id = uuid4()
            
            row = await conn.fetchrow(
                """
                INSERT INTO skills (
                    id, name, slug, version, description, detailed_description,
                    category, tags, prompt_template, input_schema, output_schema,
                    examples, model_preferences, validation_rules, dependencies,
                    author_id, author_name, author_email, organization,
                    visibility, license, pricing_model, status, published_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22, $23, $24
                )
                RETURNING *
                """,
                skill_id,
                skill_data["name"],
                skill_data["slug"],
                skill_data.get("version", "1.0.0"),
                skill_data["description"],
                skill_data.get("detailed_description"),
                skill_data["category"],
                skill_data.get("tags", []),
                skill_data["prompt_template"],
                json.dumps(skill_data["input_schema"]),
                json.dumps(skill_data["output_schema"]),
                json.dumps(skill_data.get("examples")),
                json.dumps(skill_data.get("model_preferences", {})),
                json.dumps(skill_data.get("validation_rules")),
                json.dumps(skill_data.get("dependencies", {})),
                author_id,
                skill_data.get("author_name"),
                skill_data.get("author_email"),
                skill_data.get("organization"),
                skill_data.get("visibility", "public"),
                skill_data.get("license", "MIT"),
                skill_data.get("pricing_model", "free"),
                skill_data.get("status", "draft"),
                datetime.utcnow() if skill_data.get("status") == "active" else None
            )
            
            return dict(row)
    
    async def update_skill(
        self,
        skill_id: UUID,
        updates: Dict[str, Any],
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Update a skill (must be owner)"""
        async with self.pool.acquire() as conn:
            # Check ownership
            owner_check = await conn.fetchrow(
                "SELECT author_id FROM skills WHERE id = $1",
                skill_id
            )
            
            if not owner_check:
                return None
            
            if owner_check["author_id"] != user_id:
                raise PermissionError("Only skill owner can update")
            
            # Build update query
            set_clauses = []
            params = []
            param_idx = 1
            
            updateable_fields = {
                "name": "name",
                "description": "description",
                "detailed_description": "detailed_description",
                "category": "category",
                "tags": "tags",
                "prompt_template": "prompt_template",
                "input_schema": "input_schema",
                "output_schema": "output_schema",
                "examples": "examples",
                "model_preferences": "model_preferences",
                "validation_rules": "validation_rules",
                "status": "status"
            }
            
            for key, value in updates.items():
                if key in updateable_fields:
                    db_field = updateable_fields[key]
                    if key in ["input_schema", "output_schema", "examples", "model_preferences", "validation_rules"]:
                        set_clauses.append(f"{db_field} = ${param_idx}::jsonb")
                        params.append(json.dumps(value))
                    elif key == "tags":
                        set_clauses.append(f"{db_field} = ${param_idx}")
                        params.append(value)
                    else:
                        set_clauses.append(f"{db_field} = ${param_idx}")
                        params.append(value)
                    param_idx += 1
            
            if not set_clauses:
                # No updates
                return await self.get_skill_by_id(skill_id)
            
            set_clauses.append(f"updated_at = ${param_idx}")
            params.append(datetime.utcnow())
            param_idx += 1
            
            params.append(skill_id)
            
            query = f"""
                UPDATE skills
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx}
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *params)
            return dict(row) if row else None
    
    async def log_execution(
        self,
        execution_data: Dict[str, Any]
    ) -> UUID:
        """Log skill execution to database"""
        async with self.pool.acquire() as conn:
            execution_id = uuid4()
            
            await conn.execute(
                """
                INSERT INTO skill_executions (
                    id, skill_id, skill_version, user_id,
                    inputs, outputs, rendered_prompt,
                    model_id, model_provider,
                    status, error_message, validation_passed, validation_results,
                    latency_ms, tokens_input, tokens_output, cost_usd,
                    agent_id, workflow_id, parent_execution_id,
                    cache_hit, cache_key,
                    executed_at, completed_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                    $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
                )
                """,
                execution_id,
                execution_data["skill_id"],
                execution_data["skill_version"],
                execution_data.get("user_id"),
                json.dumps(execution_data["inputs"]),
                json.dumps(execution_data.get("outputs")),
                execution_data.get("rendered_prompt"),
                execution_data.get("model_id"),
                execution_data.get("model_provider"),
                execution_data["status"],
                execution_data.get("error_message"),
                execution_data.get("validation_passed"),
                json.dumps(execution_data.get("validation_results")),
                execution_data.get("latency_ms"),
                execution_data.get("tokens_input"),
                execution_data.get("tokens_output"),
                execution_data.get("cost_usd"),
                execution_data.get("agent_id"),
                execution_data.get("workflow_id"),
                execution_data.get("parent_execution_id"),
                execution_data.get("cache_hit", False),
                execution_data.get("cache_key"),
                execution_data.get("executed_at", datetime.utcnow()),
                execution_data.get("completed_at")
            )
            
            return execution_id
    
    async def install_skill(
        self,
        skill_id: UUID,
        user_id: UUID,
        version: Optional[str] = None,
        auto_update: bool = True
    ) -> Dict[str, Any]:
        """Install a skill for a user"""
        async with self.pool.acquire() as conn:
            # Get skill version
            if not version:
                skill = await self.get_skill_by_id(skill_id)
                if not skill:
                    raise ValueError("Skill not found")
                version = skill["version"]
            
            # Check if already installed
            existing = await conn.fetchrow(
                """
                SELECT * FROM skill_installations
                WHERE skill_id = $1 AND user_id = $2
                """,
                skill_id, user_id
            )
            
            if existing:
                # Update existing installation
                row = await conn.fetchrow(
                    """
                    UPDATE skill_installations
                    SET version = $1, auto_update = $2, enabled = TRUE
                    WHERE skill_id = $3 AND user_id = $4
                    RETURNING *
                    """,
                    version, auto_update, skill_id, user_id
                )
            else:
                # Create new installation
                row = await conn.fetchrow(
                    """
                    INSERT INTO skill_installations (
                        skill_id, user_id, version, auto_update, enabled
                    ) VALUES ($1, $2, $3, $4, TRUE)
                    RETURNING *
                    """,
                    skill_id, user_id, version, auto_update
                )
            
            return dict(row)
    
    async def uninstall_skill(
        self,
        skill_id: UUID,
        user_id: UUID
    ) -> bool:
        """Uninstall a skill for a user"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM skill_installations
                WHERE skill_id = $1 AND user_id = $2
                """,
                skill_id, user_id
            )
            return result == "DELETE 1"
    
    async def list_installed_skills(
        self,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """List skills installed by a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    si.*,
                    s.name as skill_name,
                    s.slug as skill_slug,
                    s.description as skill_description,
                    s.category as skill_category
                FROM skill_installations si
                JOIN skills s ON si.skill_id = s.id
                WHERE si.user_id = $1 AND si.enabled = TRUE
                ORDER BY si.last_used_at DESC NULLS LAST, si.installed_at DESC
                """,
                user_id
            )
            return [dict(row) for row in rows]
    
    async def get_execution_by_id(
        self,
        execution_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get execution details by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM skill_executions
                WHERE id = $1
                """,
                execution_id
            )
            return dict(row) if row else None
    
    def skill_dict_to_model(self, skill_dict: Dict[str, Any]) -> Skill:
        """Convert database dict to Skill model"""
        return Skill(
            id=str(skill_dict["id"]),
            name=skill_dict["name"],
            slug=skill_dict["slug"],
            version=skill_dict["version"],
            description=skill_dict["description"],
            prompt_template=skill_dict["prompt_template"],
            input_schema=skill_dict["input_schema"] if isinstance(skill_dict["input_schema"], dict) else json.loads(skill_dict["input_schema"]),
            output_schema=skill_dict["output_schema"] if isinstance(skill_dict["output_schema"], dict) else json.loads(skill_dict["output_schema"]),
            model_preferences=skill_dict.get("model_preferences", {}) if isinstance(skill_dict.get("model_preferences"), dict) else json.loads(skill_dict.get("model_preferences", "{}")),
            validation_rules=skill_dict.get("validation_rules") if isinstance(skill_dict.get("validation_rules"), list) else (json.loads(skill_dict["validation_rules"]) if skill_dict.get("validation_rules") else None),
            category=skill_dict["category"],
            created_at=skill_dict.get("created_at"),
            updated_at=skill_dict.get("updated_at")
        )

    async def list_skill_reviews(
        self,
        skill_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List skill reviews (not yet implemented for DB backend)."""
        raise NotImplementedError("Skill reviews listing requires database implementation")

    async def create_skill_review(
        self,
        skill_id: UUID,
        user_id: UUID,
        rating: int,
        title: Optional[str],
        review_text: Optional[str]
    ) -> Dict[str, Any]:
        """Create skill review (not yet implemented for DB backend)."""
        raise NotImplementedError("Skill reviews creation requires database implementation")

    async def get_skill_analytics(
        self,
        skill_id: UUID,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get analytics for a skill (not yet implemented for DB backend)."""
        raise NotImplementedError("Skill analytics requires database implementation")
