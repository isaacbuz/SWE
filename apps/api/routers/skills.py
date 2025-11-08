"""
Skills marketplace and execution endpoints.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from pydantic import BaseModel, Field

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter

# Import database service
from packages.skills_engine import (
    SkillExecutionEngine,
    Skill,
    ExecutionContext,
    SkillsDatabaseService,
    InMemorySkillsService,
    get_db_pool,
    get_in_memory_skills_service,
)
from packages.moe_router import MoERouter
from packages.db.redis import RedisClient


router = APIRouter(prefix="/skills", tags=["skills"])
logger = logging.getLogger(__name__)

SkillsService = Union[SkillsDatabaseService, InMemorySkillsService]


def serialize_skill(skill_dict: Dict[str, Any]) -> Skill:
    """Convert raw skill dicts into response models."""
    if not skill_dict:
        raise ValueError("Skill dictionary is required for serialization")

    def fmt(dt: Optional[datetime]) -> Optional[str]:
        if not dt:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    return Skill(
        id=skill_dict["id"],
        name=skill_dict["name"],
        slug=skill_dict["slug"],
        version=skill_dict.get("version", "1.0.0"),
        description=skill_dict.get("description", ""),
        detailed_description=skill_dict.get("detailed_description"),
        category=skill_dict.get("category", "GENERAL"),
        tags=skill_dict.get("tags", []),
        author_id=skill_dict.get("author_id"),
        author_name=skill_dict.get("author_name"),
        download_count=skill_dict.get("download_count", 0),
        installation_count=skill_dict.get("installation_count", 0),
        execution_count=skill_dict.get("execution_count", 0),
        avg_rating=float(skill_dict.get("avg_rating", 0) or 0),
        review_count=skill_dict.get("review_count", 0),
        status=skill_dict.get("status", "draft"),
        visibility=skill_dict.get("visibility", "public"),
        license=skill_dict.get("license", "MIT"),
        pricing_model=skill_dict.get("pricing_model", "free"),
        created_at=fmt(skill_dict.get("created_at")),
        updated_at=fmt(skill_dict.get("updated_at")),
    )


def serialize_review(review_dict: Dict[str, Any]) -> SkillReview:
    def fmt(dt: Optional[datetime]) -> str:
        if not dt:
            return datetime.utcnow().isoformat()
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    return SkillReview(
        id=review_dict["id"],
        skill_id=review_dict["skill_id"],
        user_id=review_dict["user_id"],
        rating=review_dict["rating"],
        title=review_dict.get("title"),
        review_text=review_dict.get("review_text"),
        created_at=fmt(review_dict.get("created_at")),
    )


def serialize_analytics(analytics_dict: Dict[str, Any]) -> SkillAnalytics:
    return SkillAnalytics(
        skill_id=analytics_dict["skill_id"],
        start_date=analytics_dict.get("start_date"),
        end_date=analytics_dict.get("end_date"),
        executions=analytics_dict.get("executions", 0),
        installations=analytics_dict.get("installations", 0),
        downloads=analytics_dict.get("downloads", 0),
        avg_rating = float(analytics_dict.get("avg_rating", 0) or 0),
        review_count=analytics_dict.get("review_count", 0),
        rating_breakdown=analytics_dict.get("rating_breakdown", {}),
        updated_at=analytics_dict.get("updated_at", datetime.utcnow().isoformat()),
    )

# Dependency to get database service
async def get_skills_db_service() -> SkillsService:
    """Get Skills database service instance, falling back to in-memory store."""
    try:
        pool = await get_db_pool()
        return SkillsDatabaseService(pool)
    except Exception as exc:
        logger.warning("Falling back to in-memory skills service: %s", exc)
        return await get_in_memory_skills_service()


# Dependency to get Skills execution engine
def get_skills_engine() -> SkillExecutionEngine:
    """Get Skills execution engine instance (singleton)"""
    # In production, this would be a proper singleton
    moe_router = MoERouter()
    redis_client = RedisClient()
    return SkillExecutionEngine(moe_router, redis_client)


# Request/Response Models

class SkillCreate(BaseModel):
    """Skill creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    detailed_description: Optional[str] = None
    category: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    prompt_template: str = Field(..., min_length=1)
    input_schema: Dict[str, Any] = Field(...)
    output_schema: Dict[str, Any] = Field(...)
    examples: Optional[List[Dict[str, Any]]] = None
    model_preferences: Optional[Dict[str, Any]] = None
    validation_rules: Optional[List[Dict[str, Any]]] = None
    visibility: str = Field(default="public", pattern="^(public|private|unlisted)$")
    license: str = Field(default="MIT")
    pricing_model: str = Field(default="free", pattern="^(free|paid|freemium)$")


class SkillUpdate(BaseModel):
    """Skill update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    prompt_template: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    model_preferences: Optional[Dict[str, Any]] = None
    validation_rules: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|deprecated|archived)$")


class SkillExecutionRequest(BaseModel):
    """Skill execution request."""
    skill_id: UUID
    inputs: Dict[str, Any] = Field(...)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Skill(BaseModel):
    """Skill response model."""
    id: UUID
    name: str
    slug: str
    version: str
    description: str
    detailed_description: Optional[str]
    category: str
    tags: List[str]
    author_id: Optional[UUID]
    author_name: Optional[str]
    download_count: int
    installation_count: int
    execution_count: int
    avg_rating: float
    review_count: int
    status: str
    visibility: str
    license: str
    pricing_model: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SkillDetail(Skill):
    """Detailed skill response with execution config."""
    prompt_template: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    examples: Optional[List[Dict[str, Any]]]
    model_preferences: Dict[str, Any]
    validation_rules: Optional[List[Dict[str, Any]]]


class SkillExecutionResult(BaseModel):
    """Skill execution result."""
    execution_id: str
    skill_id: UUID
    skill_version: str
    status: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]]
    validation_passed: bool
    validation_result: Optional[Dict[str, Any]]
    model_id: Optional[str]
    model_provider: Optional[str]
    latency_ms: Optional[int]
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    cost_usd: Optional[float]
    cache_hit: bool
    error_message: Optional[str]
    executed_at: str
    completed_at: Optional[str]


class SkillInstallation(BaseModel):
    """Skill installation response."""
    id: UUID
    skill_id: UUID
    user_id: UUID
    version: str
    auto_update: bool
    enabled: bool
    installed_at: str
    last_used_at: Optional[str]
    use_count: int


class SkillReview(BaseModel):
    """Skill review response model."""
    id: UUID
    skill_id: UUID
    user_id: UUID
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str]
    review_text: Optional[str]
    created_at: str


class SkillReviewCreate(BaseModel):
    """Skill review creation request."""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    review_text: Optional[str] = None


class SkillAnalytics(BaseModel):
    """Skill analytics response."""
    skill_id: UUID
    start_date: Optional[str]
    end_date: Optional[str]
    executions: int
    installations: int
    downloads: int
    avg_rating: float
    review_count: int
    rating_breakdown: Dict[int, int]
    updated_at: str


# Endpoints

@router.get("", response_model=List[Skill])
@limiter.limit("100/minute")
async def list_skills(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    visibility: Optional[str] = Query(None, pattern="^(public|private|unlisted)$"),
    status: Optional[str] = Query("active", pattern="^(draft|active|deprecated|archived)$"),
    sort: Optional[str] = Query("updated_at", pattern="^(created_at|updated_at|download_count|avg_rating|execution_count)$"),
    order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[CurrentUser] = Depends(get_current_active_user),
    db_service: SkillsDatabaseService = Depends(get_skills_db_service),
):
    """
    List skills in the marketplace.
    
    Supports filtering, searching, and sorting.
    """
    try:
        skills = await db_service.list_skills(
            category=category,
            tags=tags,
            search=search,
            visibility=visibility,
            status=status or "active",
            sort=sort or "updated_at",
            order=order or "desc",
            limit=limit,
            offset=offset
        )
        
        # Convert to response models
        return [serialize_skill(skill) for skill in skills]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {str(e)}"
        )


@router.get("/{skill_id}", response_model=SkillDetail)
@limiter.limit("100/minute")
async def get_skill(
    skill_id: UUID,
    current_user: Optional[CurrentUser] = Depends(get_current_active_user),
    db_service: SkillsDatabaseService = Depends(get_skills_db_service),
):
    """Get skill details by ID."""
    try:
        skill_dict = await db_service.get_skill_by_id(skill_id)
        
        if not skill_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found"
            )
        
        # Parse JSON fields
        input_schema = skill_dict["input_schema"]
        if isinstance(input_schema, str):
            input_schema = json.loads(input_schema)
        
        output_schema = skill_dict["output_schema"]
        if isinstance(output_schema, str):
            output_schema = json.loads(output_schema)
        
        examples = skill_dict.get("examples")
        if examples and isinstance(examples, str):
            examples = json.loads(examples)
        
        model_preferences = skill_dict.get("model_preferences", {})
        if isinstance(model_preferences, str):
            model_preferences = json.loads(model_preferences)
        
        validation_rules = skill_dict.get("validation_rules")
        if validation_rules and isinstance(validation_rules, str):
            validation_rules = json.loads(validation_rules)
        
        base_skill = serialize_skill(skill_dict)
        return SkillDetail(
            **base_skill.model_dump(),
            prompt_template=skill_dict["prompt_template"],
            input_schema=input_schema,
            output_schema=output_schema,
            examples=examples,
            model_preferences=model_preferences,
            validation_rules=validation_rules,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill: {str(e)}"
        )


@router.post("", response_model=Skill, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_skill(
    skill_data: SkillCreate,
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsDatabaseService = Depends(get_skills_db_service),
):
    """Create a new skill."""
    try:
        # Check slug uniqueness
        existing = await db_service.get_skill_by_slug(skill_data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Skill with slug '{skill_data.slug}' already exists"
            )
        
        # Create skill
        skill_dict = await db_service.create_skill(
            skill_data=skill_data.dict(),
            author_id=current_user.id
        )
        
        return serialize_skill(skill_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(e)}"
        )


@router.put("/{skill_id}", response_model=Skill)
@limiter.limit("20/minute")
async def update_skill(
    skill_id: UUID,
    skill_data: SkillUpdate,
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsService = Depends(get_skills_db_service),
):
    """Update a skill (must be owner/editor)."""
    try:
        updates = skill_data.model_dump(exclude_unset=True)
        if not updates:
            skill_dict = await db_service.get_skill_by_id(skill_id)
            if not skill_dict:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Skill {skill_id} not found"
                )
            return serialize_skill(skill_dict)

        updated_skill = await db_service.update_skill(
            skill_id=skill_id,
            updates=updates,
            user_id=current_user.id,
        )

        if not updated_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found"
            )

        return serialize_skill(updated_skill)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(e)}"
        )


@router.post("/{skill_id}/execute", response_model=SkillExecutionResult)
@limiter.limit("30/minute")
async def execute_skill(
    skill_id: UUID,
    execution_request: SkillExecutionRequest = Body(...),
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsDatabaseService = Depends(get_skills_db_service),
    engine: SkillExecutionEngine = Depends(get_skills_engine),
):
    """
    Execute a skill.
    
    This endpoint:
    1. Validates inputs
    2. Executes skill via Skills Engine
    3. Returns results with performance metrics
    """
    try:
        # Load skill from database
        skill_dict = await db_service.get_skill_by_id(skill_id)
        if not skill_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found"
            )
        
        # Convert to Skill model
        skill = db_service.skill_dict_to_model(skill_dict)
        
        # Create execution context
        context = ExecutionContext(
            user_id=str(current_user.id),
            agent_id=execution_request.context.get("agent_id"),
            workflow_id=execution_request.context.get("workflow_id"),
            parent_execution_id=execution_request.context.get("parent_execution_id"),
            metadata=execution_request.context
        )
        
        # Execute skill
        result = await engine.execute_skill(
            skill=skill,
            inputs=execution_request.inputs,
            context=context
        )
        
        # Log execution to database
        execution_log = {
            "skill_id": skill_id,
            "skill_version": result.skill_version,
            "user_id": current_user.id,
            "inputs": result.inputs,
            "outputs": result.outputs,
            "rendered_prompt": result.rendered_prompt,
            "model_id": result.model_id,
            "model_provider": result.model_provider,
            "status": result.status.value,
            "error_message": result.error_message,
            "validation_passed": result.validation_passed,
            "validation_results": result.validation_result.dict() if result.validation_result else None,
            "latency_ms": result.latency_ms,
            "tokens_input": result.tokens_input,
            "tokens_output": result.tokens_output,
            "cost_usd": result.cost_usd,
            "agent_id": UUID(context.agent_id) if context.agent_id else None,
            "workflow_id": context.workflow_id,
            "cache_hit": result.cache_hit,
            "cache_key": result.cache_key,
            "executed_at": result.executed_at,
            "completed_at": result.completed_at,
        }
        
        execution_id = await db_service.log_execution(execution_log)
        
        # Return result
        return SkillExecutionResult(
            execution_id=str(execution_id),
            skill_id=UUID(result.skill_id),
            skill_version=result.skill_version,
            status=result.status.value,
            inputs=result.inputs,
            outputs=result.outputs,
            validation_passed=result.validation_passed,
            validation_result=result.validation_result.dict() if result.validation_result else None,
            model_id=result.model_id,
            model_provider=result.model_provider,
            latency_ms=result.latency_ms,
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            cost_usd=result.cost_usd,
            cache_hit=result.cache_hit,
            error_message=result.error_message,
            executed_at=result.executed_at.isoformat() if result.executed_at else None,
            completed_at=result.completed_at.isoformat() if result.completed_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute skill: {str(e)}"
        )


@router.post("/{skill_id}/install", response_model=SkillInstallation, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def install_skill(
    skill_id: UUID,
    version: Optional[str] = Query(None, description="Specific version to install"),
    auto_update: bool = Query(True, description="Enable auto-updates"),
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsDatabaseService = Depends(get_skills_db_service),
):
    """Install a skill for the current user."""
    try:
        installation = await db_service.install_skill(
            skill_id=skill_id,
            user_id=current_user.id,
            version=version,
            auto_update=auto_update
        )
        
        return SkillInstallation(
            id=installation["id"],
            skill_id=installation["skill_id"],
            user_id=installation["user_id"],
            version=installation["version"],
            auto_update=installation["auto_update"],
            enabled=installation["enabled"],
            installed_at=installation["installed_at"].isoformat() if installation.get("installed_at") else None,
            last_used_at=installation["last_used_at"].isoformat() if installation.get("last_used_at") else None,
            use_count=installation.get("use_count", 0),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install skill: {str(e)}"
        )


@router.delete("/{skill_id}/install", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def uninstall_skill(
    skill_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsDatabaseService = Depends(get_skills_db_service),
):
    """Uninstall a skill for the current user."""
    try:
        success = await db_service.uninstall_skill(
            skill_id=skill_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill installation not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall skill: {str(e)}"
        )


@router.get("/installed", response_model=List[SkillInstallation])
@limiter.limit("100/minute")
async def list_installed_skills(
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsDatabaseService = Depends(get_skills_db_service),
):
    """List skills installed by the current user."""
    try:
        installations = await db_service.list_installed_skills(current_user.id)
        
        return [
            SkillInstallation(
                id=inst["id"],
                skill_id=inst["skill_id"],
                user_id=inst["user_id"],
                version=inst["version"],
                auto_update=inst["auto_update"],
                enabled=inst["enabled"],
                installed_at=inst["installed_at"].isoformat() if inst.get("installed_at") else None,
                last_used_at=inst["last_used_at"].isoformat() if inst.get("last_used_at") else None,
                use_count=inst.get("use_count", 0),
            )
            for inst in installations
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list installed skills: {str(e)}"
        )


@router.get("/{skill_id}/reviews", response_model=List[SkillReview])
@limiter.limit("100/minute")
async def get_skill_reviews(
    skill_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[CurrentUser] = Depends(get_current_active_user),
    db_service: SkillsService = Depends(get_skills_db_service),
):
    """Get reviews for a skill."""
    try:
        reviews = await db_service.list_skill_reviews(skill_id, limit=limit, offset=offset)
        return [serialize_review(review) for review in reviews]
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Skill reviews not yet available for this backend",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reviews: {str(e)}",
        )


@router.post("/{skill_id}/reviews", response_model=SkillReview, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_skill_review(
    skill_id: UUID,
    review: SkillReviewCreate,
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsService = Depends(get_skills_db_service),
):
    """Create a review for a skill."""
    try:
        review_dict = await db_service.create_skill_review(
            skill_id=skill_id,
            user_id=current_user.id,
            rating=review.rating,
            title=review.title,
            review_text=review.review_text,
        )
        return serialize_review(review_dict)
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Review creation not yet available for this backend",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review: {str(e)}",
        )


@router.get("/{skill_id}/analytics", response_model=SkillAnalytics)
@limiter.limit("100/minute")
async def get_skill_analytics(
    skill_id: UUID,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(require_user),
    db_service: SkillsService = Depends(get_skills_db_service),
):
    """Get analytics for a skill (owner only)."""
    try:
        analytics = await db_service.get_skill_analytics(
            skill_id=skill_id,
            start_date=start_date,
            end_date=end_date,
        )
        return serialize_analytics(analytics)
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Analytics not yet available for this backend",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}",
        )
