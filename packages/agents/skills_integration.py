"""
Agent-Skill Integration

Allows agents to discover, install, and execute Skills from the Skills marketplace.
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid5, NAMESPACE_DNS

from packages.skills_engine import (
    SkillExecutionEngine,
    Skill,
    ExecutionContext,
    SkillsDatabaseService,
    InMemorySkillsService,
    get_db_pool,
)
from packages.skills_engine.models import ExecutionStatus
from packages.agents.base import BaseAgent, AgentResult, Context
from packages.agents.protocol import Task, TaskType


logger = logging.getLogger(__name__)


SkillsService = Union[SkillsDatabaseService, InMemorySkillsService]
_skills_manager_singleton: Optional["SkillsManager"] = None
_skills_service_singleton: Optional[SkillsService] = None


class SkillTool:
    """
    Wrapper to make Skills available as tools for agents.
    
    This allows agents to discover and execute Skills seamlessly.
    """
    
    def __init__(
        self,
        skill: Skill,
        execution_engine: SkillExecutionEngine,
        db_service: Optional[SkillsDatabaseService] = None
    ):
        """
        Initialize Skill tool
        
        Args:
            skill: Skill definition
            execution_engine: Skills execution engine
            db_service: Database service for logging
        """
        self.skill = skill
        self.execution_engine = execution_engine
        self.db_service = db_service
        self.logger = logging.getLogger(f"SkillTool.{skill.slug}")
    
    @property
    def name(self) -> str:
        """Tool name"""
        return f"skill_{self.skill.slug}"
    
    @property
    def description(self) -> str:
        """Tool description"""
        return f"{self.skill.description}. Category: {self.skill.category}"
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Context] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the skill
        
        Args:
            inputs: Skill inputs
            context: Agent execution context
            user_id: User ID for execution logging
            
        Returns:
            Skill execution results
        """
        try:
            context_metadata = getattr(context, "metadata", {}) or {}
            derived_user_id = user_id or getattr(context, "user_id", None) or context_metadata.get("user_id")
            derived_agent_id = getattr(context, "agent_id", None) or context_metadata.get("agent_id")
            derived_task_id = getattr(context, "task_id", None) or context_metadata.get("task_id")
            workflow_id = context_metadata.get("workflow_id")

            # Create execution context
            exec_context = ExecutionContext(
                user_id=derived_user_id,
                agent_id=derived_agent_id,
                workflow_id=workflow_id,
                parent_execution_id=getattr(context, "parent_task_id", None),
                metadata={
                    "executed_by_agent": True,
                    "task_id": derived_task_id,
                    "agent_context": context_metadata,
                }
            )
            
            # Execute skill
            result = await self.execution_engine.execute_skill(
                skill=self.skill,
                inputs=inputs,
                context=exec_context
            )

            is_success = result.status == ExecutionStatus.SUCCESS
            
            # Log execution if db service available
            if self.db_service and is_success:
                try:
                    await self.db_service.log_execution({
                        "skill_id": self.skill.id,
                        "skill_version": self.skill.version,
                        "user_id": derived_user_id,
                        "inputs": inputs,
                        "outputs": result.outputs or {},
                        "status": result.status.value,
                        "latency_ms": result.latency_ms,
                        "cost_usd": result.cost_usd,
                        "model_id": result.model_id,
                        "tokens_input": result.tokens_input,
                        "tokens_output": result.tokens_output,
                        "agent_id": derived_agent_id,
                        "workflow_id": workflow_id,
                        "parent_execution_id": getattr(context, "parent_task_id", None),
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to log execution: {e}")
            
            # Return results in agent-friendly format
            return {
                "success": is_success,
                "outputs": result.outputs or {},
                "error": result.error_message,
                "validation_passed": result.validation_passed,
                "latency_ms": result.latency_ms,
                "cost_usd": result.cost_usd,
                "cache_hit": result.cache_hit,
                "model_used": result.model_id,
            }
            
        except Exception as e:
            self.logger.error(f"Skill execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "outputs": {}
            }


class SkillsManager:
    """
    Manages Skills for agents.
    
    Provides discovery, installation, and execution of Skills.
    """
    
    def __init__(
        self,
        execution_engine: SkillExecutionEngine,
        skills_service: Optional[SkillsService] = None
    ):
        """
        Initialize Skills manager
        
        Args:
            execution_engine: Skills execution engine
            db_service: Database service for Skills lookup
        """
        self.execution_engine = execution_engine
        self.skills_service = skills_service
        self.logger = logging.getLogger("SkillsManager")
        self._skill_cache: Dict[str, Skill] = {}
    
    async def discover_skills(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[Skill]:
        """
        Discover available Skills
        
        Args:
            category: Filter by category
            tags: Filter by tags
            search: Search query
            limit: Maximum results
            
        Returns:
            List of available Skills
        """
        if not self.skills_service:
            self.logger.warning("No database service, returning empty list")
            return []
        
        try:
            skills = await self.skills_service.list_skills(
                category=category,
                tags=tags,
                search=search,
                limit=limit,
                offset=0
            )
            
            # Convert to Skill models
            result = []
            for skill_dict in skills:
                try:
                    skill = self.skills_service.skill_dict_to_model(skill_dict)
                    result.append(skill)
                    # Cache for quick access
                    self._skill_cache[skill.id] = skill
                except Exception as e:
                    self.logger.warning(f"Failed to convert skill {skill_dict.get('id')}: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to discover skills: {e}", exc_info=True)
            return []
    
    async def get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        """
        Get skill by ID
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Skill or None
        """
        # Check cache first
        if skill_id in self._skill_cache:
            return self._skill_cache[skill_id]
        
        if not self.skills_service:
            return None
        
        try:
            skill_dict = await self.skills_service.get_skill_by_id(UUID(skill_id))
            if skill_dict:
                skill = self.skills_service.skill_dict_to_model(skill_dict)
                self._skill_cache[skill_id] = skill
                return skill
        except Exception as e:
            self.logger.error(f"Failed to get skill {skill_id}: {e}", exc_info=True)
        
        return None
    
    async def get_skill_by_slug(self, slug: str) -> Optional[Skill]:
        """
        Get skill by slug
        
        Args:
            slug: Skill slug
            
        Returns:
            Skill or None
        """
        if not self.skills_service:
            return None
        
        try:
            skill_dict = await self.skills_service.get_skill_by_slug(slug)
            if skill_dict:
                skill = self.skills_service.skill_dict_to_model(skill_dict)
                self._skill_cache[skill.id] = skill
                return skill
        except Exception as e:
            self.logger.error(f"Failed to get skill by slug {slug}: {e}", exc_info=True)
        
        return None
    
    def create_skill_tool(self, skill: Skill) -> SkillTool:
        """
        Create a SkillTool from a Skill
        
        Args:
            skill: Skill definition
            
        Returns:
            SkillTool instance
        """
        return SkillTool(
            skill=skill,
            execution_engine=self.execution_engine,
            db_service=self.skills_service
        )
    
    async def get_tools_for_task(
        self,
        task_type: TaskType,
        task_description: Optional[str] = None
    ) -> List[SkillTool]:
        """
        Get relevant Skills as tools for a task
        
        Args:
            task_type: Type of task
            task_description: Optional task description for better matching
            
        Returns:
            List of SkillTools
        """
        # Map task types to skill categories
        category_map = {
            TaskType.CODE_GENERATION: "CODE_GENERATION",
            TaskType.CODE_REVIEW: "CODE_REVIEW",
            TaskType.TESTING: "TESTING",
            TaskType.DOCUMENTATION: "DOCUMENTATION",
            TaskType.ARCHITECTURE: "ARCHITECTURE",
        }
        
        category = category_map.get(task_type)
        
        # Discover relevant skills
        skills = await self.discover_skills(
            category=category,
            limit=20
        )
        
        # Convert to tools
        tools = [self.create_skill_tool(skill) for skill in skills]
        
        self.logger.info(f"Found {len(tools)} Skills for task type {task_type.value}")
        
        return tools
    
    async def install_skill_for_agent(
        self,
        skill_id: str,
        agent_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Install a skill for an agent
        
        Args:
            skill_id: Skill ID
            agent_id: Agent ID
            user_id: User ID (optional)
            
        Returns:
            True if installed successfully
        """
        if not self.skills_service:
            self.logger.warning("No database service, cannot install skill")
            return False
        
        try:
            install_user_id = user_id or agent_id
            skill_uuid = _coerce_uuid(skill_id)
            install_user_uuid = _coerce_uuid(install_user_id)
            
            if not skill_uuid or not install_user_uuid:
                self.logger.error("Valid skill_id and user_id are required to install a skill")
                return False
            
            installation = await self.skills_service.install_skill(
                skill_id=skill_uuid,
                user_id=install_user_uuid
            )
            
            if installation:
                self.logger.info(f"Installed skill {skill_id} for agent {agent_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to install skill {skill_id}: {e}", exc_info=True)
            return False
    
    async def get_installed_skills(
        self,
        agent_id: str,
        user_id: Optional[str] = None
    ) -> List[Skill]:
        """
        Get skills installed for an agent
        
        Args:
            agent_id: Agent ID
            user_id: User ID (optional)
            
        Returns:
            List of installed Skills
        """
        if not self.skills_service:
            return []
        
        try:
            lookup_user_id = user_id or agent_id
            lookup_uuid = _coerce_uuid(lookup_user_id)
            
            if not lookup_uuid:
                return []
            
            installations = await self.skills_service.list_installed_skills(
                user_id=lookup_uuid
            )
            
            skills = []
            for installation in installations:
                skill_id = installation.get("skill_id")
                if skill_id:
                    skill = await self.get_skill_by_id(str(skill_id))
                    if skill:
                        skills.append(skill)
            
            return skills
            
        except Exception as e:
            self.logger.error(f"Failed to get installed skills: {e}", exc_info=True)
            return []


def _coerce_uuid(value: Optional[str]) -> Optional[UUID]:
    """Convert arbitrary identifiers to UUIDs deterministically."""
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return uuid5(NAMESPACE_DNS, str(value))


def _get_or_create_service(
    provided_service: Optional[SkillsService] = None
) -> SkillsService:
    """Return shared skills service with database fallback."""
    global _skills_service_singleton

    if provided_service is not None:
        _skills_service_singleton = provided_service
        return provided_service

    if _skills_service_singleton is not None:
        return _skills_service_singleton

    db_service: Optional[SkillsDatabaseService] = None
    try:
        pool = asyncio.run(get_db_pool())
        db_service = SkillsDatabaseService(pool)
        logger.info("Initialized SkillsDatabaseService for SkillsManager")
    except RuntimeError as exc:
        logger.info(
            "Cannot initialize database Skills service inside running loop (%s); "
            "using in-memory fallback",
            exc,
        )
    except Exception as exc:
        logger.warning("Failed to initialize database service (%s); using in-memory fallback", exc)

    if db_service is None:
        _skills_service_singleton = InMemorySkillsService()
    else:
        _skills_service_singleton = db_service

    return _skills_service_singleton


def get_skills_manager(
    execution_engine: Optional[SkillExecutionEngine] = None,
    db_service: Optional[SkillsService] = None
) -> SkillsManager:
    """
    Get or create Skills manager instance.
    """
    global _skills_manager_singleton

    cache_manager = execution_engine is None and db_service is None

    if _skills_manager_singleton and cache_manager:
        return _skills_manager_singleton

    if execution_engine is None:
        from packages.moe_router import MoERouter
        from packages.db.redis import RedisClient

        moe_router = MoERouter()
        redis_client = RedisClient()
        execution_engine = SkillExecutionEngine(moe_router, redis_client)

    service = _get_or_create_service(db_service)
    manager = SkillsManager(execution_engine, service)

    if cache_manager:
        _skills_manager_singleton = manager

    return manager


def reset_skills_manager_cache():
    """Reset cached Skills manager/service (useful for tests)."""
    global _skills_manager_singleton, _skills_service_singleton
    _skills_manager_singleton = None
    _skills_service_singleton = None
