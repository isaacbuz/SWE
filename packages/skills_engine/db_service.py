"""
Database service for Skills operations.

Handles all database interactions for Skills marketplace, execution tracking,
and analytics.
"""
import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
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
                ORDER BY version DESC
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
        status: Optional[str] = None,
        sort: str = "updated_at",
        order: str = "desc",
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List skills with filters"""
        async with self.pool.acquire() as conn:
            conditions = ["status != 'archived'"]
            params: List[Any] = []
            param_count = 0
            
            if category:
                param_count += 1
                conditions.append(f"category = ${param_count}")
                params.append(category)
            
            if tags:
                param_count += 1
                conditions.append(f"tags && ${param_count}")
                params.append(tags)
            
            if search:
                param_count += 1
                conditions.append(
                    f"(name ILIKE ${param_count} OR description ILIKE ${param_count})"
                )
                params.append(f"%{search}%")
            
            if visibility:
                param_count += 1
                conditions.append(f"visibility = ${param_count}")
                params.append(visibility)
            
            if status:
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(status)
            
            where_clause = " AND ".join(conditions)
            
            # Validate sort field
            valid_sorts = [
                "created_at", "updated_at", "download_count", 
                "avg_rating", "execution_count", "name"
            ]
            if sort not in valid_sorts:
                sort = "updated_at"
            
            order_dir = "DESC" if order.lower() == "desc" else "ASC"
            
            param_count += 1
            params.append(limit)
            param_count += 1
            params.append(offset)
            
            query = f"""
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
                WHERE {where_clause}
                ORDER BY {sort} {order_dir}
                LIMIT ${param_count - 1}
                OFFSET ${param_count}
            """
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def create_skill(
        self,
        skill_data: Dict[str, Any],
        author_id: UUID
    ) -> Dict[str, Any]:
        """Create a new skill"""
        skill_id = uuid4()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO skills (
                    id, name, slug, version, description, detailed_description,
                    category, tags, prompt_template, input_schema, output_schema,
                    examples, model_preferences, validation_rules, dependencies,
                    author_id, author_name, author_email, organization,
                    visibility, license, pricing_model, status,
                    created_at, updated_at, published_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26
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
                json.dumps(skill_data.get("examples", [])),
                json.dumps(skill_data.get("model_preferences", {})),
                json.dumps(skill_data.get("validation_rules", [])),
                json.dumps(skill_data.get("dependencies", {})),
                author_id,
                skill_data.get("author_name"),
                skill_data.get("author_email"),
                skill_data.get("organization"),
                skill_data.get("visibility", "public"),
                skill_data.get("license", "MIT"),
                skill_data.get("pricing_model", "free"),
                skill_data.get("status", "draft"),
                datetime.utcnow(),
                datetime.utcnow(),
                datetime.utcnow() if skill_data.get("status") == "active" else None,
            )
            
            return dict(row)
    
    async def update_skill(
        self,
        skill_id: UUID,
        skill_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a skill"""
        async with self.pool.acquire() as conn:
            updates = []
            params: List[Any] = []
            param_count = 0
            
            for key, value in skill_data.items():
                if value is not None:
                    param_count += 1
                    if key in ["input_schema", "output_schema", "examples", 
                              "model_preferences", "validation_rules", "dependencies"]:
                        updates.append(f"{key} = ${param_count}::jsonb")
                        params.append(json.dumps(value))
                    else:
                        updates.append(f"{key} = ${param_count}")
                        params.append(value)
            
            if not updates:
                return await self.get_skill_by_id(skill_id)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            param_count += 1
            params.append(skill_id)
            
            query = f"""
                UPDATE skills
                SET {', '.join(updates)}
                WHERE id = ${param_count}
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *params)
            return dict(row) if row else None
    
    async def log_execution(self, execution_data: Dict[str, Any]) -> UUID:
        """Log skill execution"""
        execution_id = uuid4()
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO skill_executions (
                    id, skill_id, skill_version, user_id, agent_id, workflow_id,
                    inputs, outputs, rendered_prompt, model_id, model_provider,
                    status, error_message, validation_passed, validation_results,
                    latency_ms, tokens_input, tokens_output, cost_usd,
                    cache_hit, cache_key, executed_at, completed_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22, $23
                )
                """,
                execution_id,
                UUID(execution_data["skill_id"]),
                execution_data.get("skill_version", "1.0.0"),
                UUID(execution_data["user_id"]) if execution_data.get("user_id") else None,
                UUID(execution_data["agent_id"]) if execution_data.get("agent_id") else None,
                execution_data.get("workflow_id"),
                json.dumps(execution_data.get("inputs", {})),
                json.dumps(execution_data.get("outputs", {})),
                execution_data.get("rendered_prompt"),
                execution_data.get("model_id"),
                execution_data.get("model_provider"),
                execution_data.get("status", "pending"),
                execution_data.get("error_message"),
                execution_data.get("validation_passed", False),
                json.dumps(execution_data.get("validation_results", {})),
                execution_data.get("latency_ms", 0),
                execution_data.get("tokens_input", 0),
                execution_data.get("tokens_output", 0),
                execution_data.get("cost_usd", 0.0),
                execution_data.get("cache_hit", False),
                execution_data.get("cache_key"),
                execution_data.get("executed_at", datetime.utcnow()),
                execution_data.get("completed_at", datetime.utcnow()),
            )
            
            return execution_id
    
    async def install_skill(
        self,
        skill_id: UUID,
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Install a skill for a user"""
        async with self.pool.acquire() as conn:
            # Check if already installed
            existing = await conn.fetchrow(
                "SELECT * FROM skill_installations WHERE skill_id = $1 AND user_id = $2",
                skill_id, user_id
            )
            
            if existing:
                return dict(existing)
            
            # Get skill version
            skill = await conn.fetchrow(
                "SELECT version FROM skills WHERE id = $1",
                skill_id
            )
            
            if not skill:
                return None
            
            # Create installation
            installation_id = uuid4()
            row = await conn.fetchrow(
                """
                INSERT INTO skill_installations (
                    id, skill_id, user_id, version, auto_update, enabled, installed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                installation_id,
                skill_id,
                user_id,
                skill["version"],
                True,
                True,
                datetime.utcnow(),
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
                "DELETE FROM skill_installations WHERE skill_id = $1 AND user_id = $2",
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
                SELECT si.*, s.name, s.slug, s.description, s.category
                FROM skill_installations si
                JOIN skills s ON si.skill_id = s.id
                WHERE si.user_id = $1 AND si.enabled = true
                ORDER BY si.installed_at DESC
                """,
                user_id
            )
            return [dict(row) for row in rows]
    
    async def list_skill_reviews(
        self,
        skill_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List reviews for a skill"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, skill_id, user_id, rating, title, review_text, created_at
                FROM skill_reviews
                WHERE skill_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                skill_id, limit, offset
            )
            return [dict(row) for row in rows]
    
    async def create_skill_review(
        self,
        skill_id: UUID,
        user_id: UUID,
        rating: int,
        title: Optional[str] = None,
        review_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a review for a skill"""
        async with self.pool.acquire() as conn:
            # Check if skill exists
            skill = await conn.fetchrow(
                "SELECT id FROM skills WHERE id = $1",
                skill_id
            )
            
            if not skill:
                raise ValueError(f"Skill {skill_id} not found")
            
            # Check if user already reviewed
            existing = await conn.fetchrow(
                "SELECT id FROM skill_reviews WHERE skill_id = $1 AND user_id = $2",
                skill_id, user_id
            )
            
            if existing:
                # Update existing review
                review_id = existing["id"]
                row = await conn.fetchrow(
                    """
                    UPDATE skill_reviews
                    SET rating = $1, title = $2, review_text = $3, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $4
                    RETURNING *
                    """,
                    rating, title, review_text, review_id
                )
            else:
                # Create new review
                review_id = uuid4()
                row = await conn.fetchrow(
                    """
                    INSERT INTO skill_reviews (
                        id, skill_id, user_id, rating, title, review_text, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING *
                    """,
                    review_id, skill_id, user_id, rating, title, review_text
                )
            
            # Update skill's avg_rating and review_count
            await conn.execute(
                """
                UPDATE skills
                SET avg_rating = (
                    SELECT AVG(rating)::NUMERIC(3,2)
                    FROM skill_reviews
                    WHERE skill_id = $1
                ),
                review_count = (
                    SELECT COUNT(*)
                    FROM skill_reviews
                    WHERE skill_id = $1
                )
                WHERE id = $1
                """,
                skill_id
            )
            
            return dict(row)
    
    async def get_skill_analytics(
        self,
        skill_id: UUID,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get analytics for a skill"""
        async with self.pool.acquire() as conn:
            # Parse dates
            start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today() - timedelta(days=30)
            end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
            
            # Get execution stats
            exec_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as executions,
                    COUNT(*) FILTER (WHERE status = 'success') as executions_success,
                    COUNT(*) FILTER (WHERE status = 'failed') as executions_failed,
                    AVG(latency_ms)::INTEGER as avg_latency_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms)::INTEGER as p50_latency_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)::INTEGER as p95_latency_ms,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms)::INTEGER as p99_latency_ms,
                    SUM(cost_usd) as total_cost_usd,
                    AVG(cost_usd) as avg_cost_per_execution,
                    COUNT(DISTINCT user_id) as unique_users
                FROM skill_executions
                WHERE skill_id = $1 
                    AND executed_at::date BETWEEN $2 AND $3
                """,
                skill_id, start, end
            )
            
            # Get installation stats
            install_stats = await conn.fetchrow(
                """
                SELECT COUNT(*) as installations
                FROM skill_installations
                WHERE skill_id = $1
                    AND installed_at::date BETWEEN $2 AND $3
                """,
                skill_id, start, end
            )
            
            # Get review stats
            review_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as review_count,
                    AVG(rating) as avg_rating,
                    COUNT(*) FILTER (WHERE rating = 5) as rating_5,
                    COUNT(*) FILTER (WHERE rating = 4) as rating_4,
                    COUNT(*) FILTER (WHERE rating = 3) as rating_3,
                    COUNT(*) FILTER (WHERE rating = 2) as rating_2,
                    COUNT(*) FILTER (WHERE rating = 1) as rating_1
                FROM skill_reviews
                WHERE skill_id = $1
                """,
                skill_id
            )
            
            # Get download count from skill
            skill = await conn.fetchrow(
                "SELECT download_count FROM skills WHERE id = $1",
                skill_id
            )
            
            return {
                "skill_id": str(skill_id),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "executions": exec_stats["executions"] or 0,
                "installations": install_stats["installations"] or 0,
                "downloads": skill["download_count"] if skill else 0,
                "avg_rating": float(review_stats["avg_rating"] or 0),
                "review_count": review_stats["review_count"] or 0,
                "rating_breakdown": {
                    5: review_stats["rating_5"] or 0,
                    4: review_stats["rating_4"] or 0,
                    3: review_stats["rating_3"] or 0,
                    2: review_stats["rating_2"] or 0,
                    1: review_stats["rating_1"] or 0,
                },
                "avg_latency_ms": exec_stats["avg_latency_ms"] or 0,
                "p50_latency_ms": exec_stats["p50_latency_ms"] or 0,
                "p95_latency_ms": exec_stats["p95_latency_ms"] or 0,
                "p99_latency_ms": exec_stats["p99_latency_ms"] or 0,
                "total_cost_usd": float(exec_stats["total_cost_usd"] or 0),
                "avg_cost_per_execution": float(exec_stats["avg_cost_per_execution"] or 0),
                "unique_users": exec_stats["unique_users"] or 0,
                "updated_at": datetime.utcnow().isoformat(),
            }
    
    async def list_skill_versions(
        self,
        skill_id: UUID
    ) -> List[Dict[str, Any]]:
        """List versions for a skill"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, skill_id, version, changelog, breaking_changes, 
                       migration_guide, status, created_at
                FROM skill_versions
                WHERE skill_id = $1
                ORDER BY created_at DESC
                """,
                skill_id
            )
            return [dict(row) for row in rows]
    
    def skill_dict_to_model(self, skill_dict: Dict[str, Any]) -> Skill:
        """Convert database dict to Skill model"""
        # Parse JSON fields
        input_schema = json.loads(skill_dict.get("input_schema", "{}"))
        output_schema = json.loads(skill_dict.get("output_schema", "{}"))
        examples = json.loads(skill_dict.get("examples", "[]"))
        model_preferences = json.loads(skill_dict.get("model_preferences", "{}"))
        validation_rules = json.loads(skill_dict.get("validation_rules", "[]")) if skill_dict.get("validation_rules") else []
        tags = skill_dict.get("tags", [])
        
        return Skill(
            id=str(skill_dict["id"]),
            name=skill_dict["name"],
            slug=skill_dict["slug"],
            version=skill_dict.get("version", "1.0.0"),
            description=skill_dict.get("description", ""),
            detailed_description=skill_dict.get("detailed_description"),
            prompt_template=skill_dict.get("prompt_template", ""),
            input_schema=input_schema,
            output_schema=output_schema,
            examples=examples,
            model_preferences=model_preferences,
            validation_rules=validation_rules,
            category=skill_dict.get("category", "GENERAL"),
            tags=tags if isinstance(tags, list) else [],
            author_id=str(skill_dict["author_id"]) if skill_dict.get("author_id") else None,
            author_name=skill_dict.get("author_name"),
            organization=skill_dict.get("organization"),
            visibility=skill_dict.get("visibility", "public"),
            license=skill_dict.get("license", "MIT"),
            pricing_model=skill_dict.get("pricing_model", "free"),
            status=skill_dict.get("status", "draft"),
        )
