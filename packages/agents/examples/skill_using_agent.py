"""
Example: Agent using Skills

Demonstrates how to create an agent that uses Skills.
"""
import logging
from typing import Dict, Any

from packages.agents.base import BaseAgent, AgentResult, Context
from packages.agents.protocol import Task, TaskType
from packages.agents.skills_mixin import SkillsMixin


logger = logging.getLogger(__name__)


class SkillUsingAgent(SkillsMixin, BaseAgent):
    """
    Example agent that uses Skills.
    
    This agent can discover and execute Skills from the marketplace.
    """
    
    def __init__(self, agent_id: str = "skill-user", **kwargs):
        """Initialize agent with Skills support"""
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.CODE_GENERATION,
            **kwargs
        )
    
    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute task using Skills
        
        Args:
            task: Task to execute
            context: Execution context
            
        Returns:
            AgentResult with execution results
        """
        # Initialize Skills
        await self.initialize_skills()
        
        # Example: Use a Skill to generate code
        # First, discover available Skills
        skills = await self.discover_skills(category="CODE_GENERATION")
        
        if not skills:
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error="No Skills available for code generation"
            )
        
        # Use first available Skill (in practice, agent would select best one)
        skill = skills[0]
        
        # Prepare inputs based on task
        inputs = {
            "task": task.description,
            "requirements": task.metadata.get("requirements", ""),
        }
        
        # Execute Skill
        skill_result = await self.execute_skill(
            skill_id=skill["id"],
            inputs=inputs,
            context=context
        )
        
        if skill_result["success"]:
            return AgentResult(
                success=True,
                output={
                    "generated_code": skill_result["outputs"],
                    "skill_used": skill["name"],
                    "skill_id": skill["id"],
                },
                evidence=[
                    {
                        "type": "skill_execution",
                        "skill_id": skill["id"],
                        "skill_name": skill["name"],
                        "inputs": inputs,
                        "outputs": skill_result["outputs"],
                        "latency_ms": skill_result.get("latency_ms"),
                        "cost_usd": skill_result.get("cost_usd"),
                    }
                ],
                model_used=skill_result.get("model_used"),
                cost=skill_result.get("cost_usd"),
            )
        else:
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=f"Skill execution failed: {skill_result.get('error')}"
            )


class CodegenAgentWithSkills(SkillsMixin, BaseAgent):
    """
    Enhanced Codegen agent that can use Skills for code generation.
    
    Falls back to direct model calls if Skills are not available.
    """
    
    def __init__(self, agent_id: str = "codegen-with-skills", **kwargs):
        """Initialize agent"""
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.CODE_GENERATION,
            **kwargs
        )
    
    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute code generation task
        
        Tries to use Skills first, falls back to direct model calls.
        """
        # Initialize Skills
        await self.initialize_skills()
        
        # Try to find a relevant Skill
        skill_tools = self.get_available_skill_tools()
        
        if skill_tools:
            # Use first available Skill tool
            tool = skill_tools[0]
            
            # Prepare inputs
            inputs = {
                "task": task.description,
                "language": task.metadata.get("language", "python"),
                "requirements": task.metadata.get("requirements", ""),
            }
            
            # Execute Skill
            result = await tool.execute(
                inputs=inputs,
                context=context,
                user_id=context.user_id
            )
            
            if result["success"]:
                return AgentResult(
                    success=True,
                    output=result["outputs"],
                    evidence=[
                        {
                            "type": "skill_execution",
                            "skill_id": tool.skill.id,
                            "skill_name": tool.skill.name,
                        }
                    ],
                    model_used=result.get("model_used"),
                    cost=result.get("cost_usd"),
                )
        
        # Fallback to direct model call (would be implemented here)
        # For now, return error
        return AgentResult(
            success=False,
            output={},
            evidence=[],
            error="No Skills available and direct model call not implemented"
        )

