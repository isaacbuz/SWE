"""
Tests for the agent Skills integration helpers.
"""
import pytest
from unittest.mock import AsyncMock, Mock

from packages.agents.base import Context
from packages.agents.skills_integration import (
    SkillTool,
    SkillsManager,
)
from packages.skills_engine import Skill
from packages.skills_engine.models import ExecutionStatus, SkillResult
from packages.skills_engine.in_memory_service import InMemorySkillsService


def _sample_skill() -> Skill:
    return Skill(
        id="00000000-0000-0000-0000-000000000001",
        name="Sample Skill",
        slug="sample-skill",
        version="1.0.0",
        description="Example skill",
        prompt_template="Do {{thing}}",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        category="CODE_GENERATION",
    )


@pytest.mark.asyncio
async def test_discover_skills_with_in_memory_service():
    service = InMemorySkillsService()
    manager = SkillsManager(execution_engine=Mock(), skills_service=service)

    skills = await manager.discover_skills(category="CODE_GENERATION", limit=5)

    assert isinstance(skills, list)
    assert skills  # Built-in YAML skills should be available
    assert skills[0].name


@pytest.mark.asyncio
async def test_skill_tool_execute_uses_context_metadata():
    skill = _sample_skill()
    engine = Mock()
    engine.execute_skill = AsyncMock(
        return_value=SkillResult(
            skill_id=skill.id,
            skill_version=skill.version,
            inputs={"task": "test"},
            outputs={"result": "ok"},
            status=ExecutionStatus.SUCCESS,
            validation_passed=True,
        )
    )

    tool = SkillTool(skill=skill, execution_engine=engine, db_service=None)

    context = Context(
        project_path="/tmp/project",
        metadata={"user_id": "user-123", "agent_id": "agent-42", "task_id": "task-1"},
    )

    result = await tool.execute(inputs={"task": "test"}, context=context)

    assert result["success"] is True
    assert result["outputs"] == {"result": "ok"}
    engine.execute_skill.assert_awaited_once()
