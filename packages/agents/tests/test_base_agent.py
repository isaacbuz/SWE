"""
Tests for Base Agent Framework
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from agents.base import (
    BaseAgent,
    Task,
    Context,
    AgentResult,
    TaskType,
    Priority,
    AgentStatus,
)
from moe_router.models import RoutingRequest, Provider


class MockAgent(BaseAgent):
    """Mock agent for testing"""

    def get_system_prompt(self) -> str:
        return "You are a test agent."

    async def execute(self, task: Task, context: Context) -> AgentResult:
        return AgentResult(
            success=True,
            output={"result": "test"},
            evidence=[],
        )


class TestBaseAgent:
    """Test suite for BaseAgent"""

    @pytest.fixture
    def agent(self):
        """Create a mock agent instance"""
        return MockAgent(
            agent_id="test-agent",
            name="Test Agent",
            description="Test agent for unit tests"
        )

    @pytest.fixture
    def task(self):
        """Create a test task"""
        return Task(
            id="task-1",
            type=TaskType.CODE_GENERATION,
            description="Generate a test function",
            input_data={"language": "python"},
            priority=Priority.MEDIUM
        )

    @pytest.fixture
    def context(self):
        """Create a test context"""
        return Context(
            project_path="/test/project",
            config={},
            shared_state={}
        )

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.agent_id == "test-agent"
        assert agent.name == "Test Agent"
        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_execute_task(self, agent, task, context):
        """Test task execution"""
        result = await agent.execute(task, context)

        assert result is not None
        assert result.success is True
        assert "result" in result.output

    def test_get_system_prompt(self, agent):
        """Test system prompt retrieval"""
        prompt = agent.get_system_prompt()
        assert prompt is not None
        assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_invoke_model_with_moe_router(self, agent, task, context):
        """Test model invocation with MoE router"""
        # Mock the MoE router
        with patch('agents.base.MoERouter') as mock_router_class:
            mock_router = Mock()
            mock_router.select_model = Mock(return_value=Mock(
                selected_model="claude-3-5-sonnet",
                confidence=0.9,
                estimated_cost=0.001,
                evidence=[]
            ))
            mock_router_class.return_value = mock_router

            # Mock Anthropic client
            with patch('agents.base.AsyncAnthropic') as mock_anthropic:
                mock_client = AsyncMock()
                mock_response = Mock()
                mock_response.content = [Mock(type="text", text="Test response")]
                mock_response.usage = Mock(input_tokens=100, output_tokens=50)
                mock_client.messages.create = AsyncMock(return_value=mock_response)
                mock_anthropic.return_value = mock_client

                agent.moe_router = mock_router
                agent.anthropic_client = mock_client

                response = await agent.invoke_model(
                    prompt="Test prompt",
                    task=task,
                    context=context,
                    requires_tools=False,
                    max_tokens=1000
                )

                assert response is not None
                assert "content" in response
                assert "usage" in response

    def test_create_evidence(self, agent):
        """Test evidence creation"""
        evidence = agent.create_evidence(
            source="test_source",
            description="Test evidence",
            weight=0.8
        )

        assert evidence is not None
        assert evidence.source == "test_source"
        assert evidence.description == "Test evidence"
        assert evidence.weight == 0.8

    def test_agent_status_transitions(self, agent, task, context):
        """Test agent status transitions"""
        assert agent.status == AgentStatus.IDLE

        # Simulate execution
        async def run():
            agent.status = AgentStatus.RUNNING
            result = await agent.execute(task, context)
            agent.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
            return result

        result = asyncio.run(run())
        assert agent.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]

    @pytest.mark.asyncio
    async def test_error_handling(self, agent, task, context):
        """Test error handling in agent execution"""
        # Create an agent that raises an error
        class ErrorAgent(MockAgent):
            async def execute(self, task: Task, context: Context) -> AgentResult:
                raise ValueError("Test error")

        error_agent = ErrorAgent(
            agent_id="error-agent",
            name="Error Agent",
            description="Agent that raises errors"
        )

        result = await error_agent.execute(task, context)
        
        # Base agent should handle errors gracefully
        # This depends on implementation, but should not crash
        assert result is not None

    def test_tool_registration(self, agent):
        """Test tool registration"""
        tool = Mock(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
            handler=Mock()
        )

        agent.tools = [tool]

        assert len(agent.tools) == 1
        assert agent.tools[0].name == "test_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

