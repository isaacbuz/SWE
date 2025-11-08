"""
Agent Package

Provides base agent framework, registry, and specialized agents for software development.
"""
from .base import (
    BaseAgent,
    Task,
    Context,
    AgentResult,
    Tool,
    AgentStatus,
    Priority
)
from .registry import AgentRegistry, AgentRegistration

# Import executive agents
from .executive.chief_architect import ChiefArchitectAgent
from .executive.planner import PlannerAgent
from .executive.technical_director import TechnicalDirectorAgent

# Import development agents
from .development.codegen import CodegenAgent
from .development.refactor import RefactorAgent
from .development.migration_specialist import MigrationSpecialistAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "Task",
    "Context",
    "AgentResult",
    "Tool",
    "AgentStatus",
    "Priority",
    # Registry
    "AgentRegistry",
    "AgentRegistration",
    # Executive agents
    "ChiefArchitectAgent",
    "PlannerAgent",
    "TechnicalDirectorAgent",
    # Development agents
    "CodegenAgent",
    "RefactorAgent",
    "MigrationSpecialistAgent",
]

__version__ = "1.0.0"
