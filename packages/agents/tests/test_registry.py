"""
Tests for Agent Registry
"""
import pytest
import asyncio
from unittest.mock import Mock, patch

from agents.registry import AgentRegistry
from agents.base import Task, Context, TaskType, Priority
from agents.executive.chief_architect import ChiefArchitectAgent
from agents.development.codegen import CodegenAgent


class TestAgentRegistry:
    """Test suite for AgentRegistry"""

    @pytest.fixture
    def registry(self):
        """Create a registry instance"""
        return AgentRegistry()

    @pytest.fixture
    def task(self):
        """Create a test task"""
        return Task(
            id="task-1",
            type=TaskType.CODE_GENERATION,
            description="Generate code",
            input_data={},
            priority=Priority.MEDIUM
        )

    @pytest.fixture
    def context(self):
        """Create a test context"""
        return Context(
            project_path="/test/project",
            config={}
        )

    def test_registry_initialization(self, registry):
        """Test registry initializes correctly"""
        assert registry is not None

    def test_register_agent(self, registry):
        """Test agent registration"""
        registry.register(
            agent_id="test-agent",
            agent_class=Mock,
            task_types=[TaskType.CODE_GENERATION],
            description="Test agent",
            priority=80
        )

        # Verify agent is registered
        assert registry.has_agent("test-agent")

    def test_get_agent_by_id(self, registry):
        """Test retrieving agent by ID"""
        registry.register(
            agent_id="test-agent",
            agent_class=Mock,
            task_types=[TaskType.CODE_GENERATION],
            description="Test agent"
        )

        agent_info = registry.get_agent("test-agent")
        assert agent_info is not None
        assert agent_info["agent_id"] == "test-agent"

    def test_get_agents_by_task_type(self, registry):
        """Test retrieving agents by task type"""
        registry.register(
            agent_id="codegen",
            agent_class=Mock,
            task_types=[TaskType.CODE_GENERATION],
            description="Code generation agent"
        )

        agents = registry.get_agents_for_task_type(TaskType.CODE_GENERATION)
        assert len(agents) > 0
        assert any(a["agent_id"] == "codegen" for a in agents)

    @pytest.mark.asyncio
    async def test_execute_task(self, registry, task, context):
        """Test task execution through registry"""
        # Register a mock agent
        mock_agent_class = Mock()
        mock_agent_instance = Mock()
        mock_agent_instance.execute = AsyncMock(return_value=Mock(
            success=True,
            output={},
            evidence=[]
        ))
        mock_agent_class.return_value = mock_agent_instance

        registry.register(
            agent_id="test-agent",
            agent_class=mock_agent_class,
            task_types=[TaskType.CODE_GENERATION],
            description="Test agent"
        )

        result = await registry.execute_task(task, context)

        assert result is not None
        assert result.success is True

    def test_get_registry_stats(self, registry):
        """Test registry statistics"""
        registry.register(
            agent_id="agent-1",
            agent_class=Mock,
            task_types=[TaskType.CODE_GENERATION],
            description="Agent 1"
        )

        stats = registry.get_registry_stats()
        assert stats is not None
        assert "total_agents" in stats or "registered_agents" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

