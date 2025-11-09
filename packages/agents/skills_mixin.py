"""
Skills Mixin for Agents

Adds Skills capabilities to agents.
"""
import logging
from typing import List, Optional, Dict, Any

from packages.agents.base import BaseAgent, AgentResult, Context
from packages.agents.protocol import Task, TaskType
from packages.agents.skills_integration import SkillsManager, SkillTool


logger = logging.getLogger(__name__)


class SkillsMixin:
    """
    Mixin to add Skills capabilities to agents.
    
    Usage:
        class MyAgent(SkillsMixin, BaseAgent):
            ...
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize Skills mixin"""
        super().__init__(*args, **kwargs)
        self._skills_manager: Optional[SkillsManager] = None
        self._skill_tools: List[SkillTool] = []
        self._skills_initialized = False
    
    @property
    def skills_manager(self) -> SkillsManager:
        """Get or create Skills manager"""
        if self._skills_manager is None:
            from packages.agents.skills_integration import get_skills_manager
            self._skills_manager = get_skills_manager()
        return self._skills_manager
    
    async def initialize_skills(self, force: bool = False):
        """
        Initialize Skills for this agent
        
        Args:
            force: Force re-initialization
        """
        if self._skills_initialized and not force:
            return
        
        try:
            # Get relevant Skills for this agent's task type
            tools = await self.skills_manager.get_tools_for_task(
                task_type=self.task_type
            )
            
            self._skill_tools = tools
            
            # Add Skills to agent's tools
            if hasattr(self, 'tools'):
                self.tools.extend(tools)
            
            self._skills_initialized = True
            
            self.logger.info(
                f"Initialized {len(tools)} Skills for agent {self.agent_id} "
                f"(task_type={self.task_type.value})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Skills: {e}", exc_info=True)
            self._skill_tools = []
    
    async def discover_skills(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available Skills
        
        Args:
            category: Filter by category
            tags: Filter by tags
            search: Search query
            
        Returns:
            List of Skill metadata
        """
        skills = await self.skills_manager.discover_skills(
            category=category,
            tags=tags,
            search=search
        )
        
        return [
            {
                "id": skill.id,
                "name": skill.name,
                "slug": skill.slug,
                "description": skill.description,
                "category": skill.category,
                "tags": skill.tags,
            }
            for skill in skills
        ]
    
    async def execute_skill(
        self,
        skill_id: str,
        inputs: Dict[str, Any],
        context: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Execute a Skill
        
        Args:
            skill_id: Skill ID or slug
            inputs: Skill inputs
            context: Execution context
            
        Returns:
            Execution results
        """
        # Get skill
        skill = await self.skills_manager.get_skill_by_id(skill_id)
        if not skill:
            skill = await self.skills_manager.get_skill_by_slug(skill_id)
        
        if not skill:
            return {
                "success": False,
                "error": f"Skill not found: {skill_id}",
                "outputs": {}
            }
        
        # Create tool and execute
        tool = self.skills_manager.create_skill_tool(skill)
        
        result = await tool.execute(
            inputs=inputs,
            context=context,
            user_id=context.user_id if context else None
        )
        
        return result
    
    async def install_skill(self, skill_id: str) -> bool:
        """
        Install a Skill for this agent
        
        Args:
            skill_id: Skill ID
            
        Returns:
            True if installed successfully
        """
        return await self.skills_manager.install_skill_for_agent(
            skill_id=skill_id,
            agent_id=self.agent_id
        )
    
    async def get_installed_skills(self) -> List[Dict[str, Any]]:
        """
        Get Skills installed for this agent
        
        Returns:
            List of installed Skill metadata
        """
        skills = await self.skills_manager.get_installed_skills(
            agent_id=self.agent_id
        )
        
        return [
            {
                "id": skill.id,
                "name": skill.name,
                "slug": skill.slug,
                "description": skill.description,
                "category": skill.category,
            }
            for skill in skills
        ]
    
    def get_available_skill_tools(self) -> List[SkillTool]:
        """
        Get available Skill tools for this agent
        
        Returns:
            List of SkillTools
        """
        return self._skill_tools.copy()
    
    async def execute_with_skills(
        self,
        task: Task,
        context: Context
    ) -> AgentResult:
        """
        Execute task with Skills support
        
        This can be called from agent's execute method to add Skills capabilities.
        
        Args:
            task: Task to execute
            context: Execution context
            
        Returns:
            AgentResult (should be extended by agent)
        """
        # Initialize Skills if not already done
        if not self._skills_initialized:
            await self.initialize_skills()
        
        # Base implementation - agents should override
        # This provides Skills access but agents implement their own logic
        return AgentResult(
            success=False,
            output={},
            evidence=[],
            error="execute_with_skills should be overridden by agent"
        )

