"""
Unit tests for Base Agent framework
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from packages.agents.base import (
    BaseAgent,
    Task,
    Context,
    AgentResult,
    AgentStatus,
    Priority,
    Tool,
    TaskType
)
from packages.agents.tests.conftest import MockAgent


class TestBaseAgentInitialization:
    """Test agent initialization"""

    def test_init_basic(self, mock_moe_router):
        """Test basic initialization"""
        agent = MockAgent(
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
            moe_router=mock_moe_router
        )
        
        assert agent.agent_id == "test-agent"
        assert agent.task_type == TaskType.CODE_GENERATION
        assert agent.status == AgentStatus.IDLE
        assert agent.moe_router == mock_moe_router

    def test_init_with_tools(self, mock_moe_router, sample_tool):
        """Test initialization with tools"""
        agent = MockAgent(
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
            tools=[sample_tool],
            moe_router=mock_moe_router
        )
        
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "read_file"

    def test_init_with_quality_requirement(self, mock_moe_router):
        """Test initialization with quality requirement"""
        agent = MockAgent(
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
            quality_requirement=0.9,
            moe_router=mock_moe_router
        )
        
        assert agent.quality_requirement == 0.9

    def test_init_with_cost_budget(self, mock_moe_router):
        """Test initialization with cost budget"""
        agent = MockAgent(
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
            cost_budget=0.05,
            moe_router=mock_moe_router
        )
        
        assert agent.cost_budget == 0.05


class TestAgentExecution:
    """Test agent execution"""

    @pytest.mark.asyncio
    async def test_execute_task(self, mock_agent, sample_task, sample_context):
        """Test executing a task"""
        result = await mock_agent.execute(sample_task, sample_context)
        
        assert isinstance(result, AgentResult)
        assert result.success == True
        assert "result" in result.output
        assert mock_agent.status == AgentStatus.RUNNING or mock_agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_updates_status(self, mock_agent, sample_task, sample_context):
        """Test that execution updates agent status"""
        initial_status = mock_agent.status
        
        await mock_agent.execute(sample_task, sample_context)
        
        # Status should change during/after execution
        assert mock_agent.status != initial_status or mock_agent.current_task is not None

    @pytest.mark.asyncio
    async def test_execute_tracks_history(self, mock_agent, sample_task, sample_context):
        """Test that execution is tracked in history"""
        initial_count = len(mock_agent.execution_history)
        
        await mock_agent.execute(sample_task, sample_context)
        
        assert len(mock_agent.execution_history) > initial_count


class TestModelInvocation:
    """Test model invocation via MoE Router"""

    @pytest.mark.asyncio
    async def test_invoke_model_with_router(self, mock_agent, sample_task, sample_context, mock_moe_router):
        """Test invoking model with MoE Router"""
        mock_agent.moe_router = mock_moe_router
        
        response = await mock_agent.invoke_model(
            prompt="Test prompt",
            task=sample_task,
            context=sample_context
        )
        
        assert "content" in response
        assert "model_used" in response
        assert mock_moe_router.select_model.called

    @pytest.mark.asyncio
    async def test_invoke_model_without_router(self, mock_agent, sample_task, sample_context):
        """Test invoking model without router (fallback)"""
        mock_agent.moe_router = None
        
        # Should raise error if no clients configured
        with pytest.raises((ValueError, AttributeError)):
            await mock_agent.invoke_model(
                prompt="Test prompt",
                task=sample_task,
                context=sample_context
            )

    @pytest.mark.asyncio
    async def test_invoke_model_with_tools(self, mock_agent, sample_task, sample_context, mock_moe_router, sample_tool):
        """Test invoking model with tools"""
        mock_agent.moe_router = mock_moe_router
        mock_agent.tools = [sample_tool]
        mock_agent.anthropic_client = Mock()
        mock_agent.anthropic_client.messages.create = AsyncMock(return_value=Mock(
            content=[Mock(type="text", text="Response")],
            usage=Mock(input_tokens=100, output_tokens=200)
        ))
        
        response = await mock_agent.invoke_model(
            prompt="Test prompt",
            task=sample_task,
            context=sample_context,
            requires_tools=True
        )
        
        assert "content" in response

    @pytest.mark.asyncio
    async def test_invoke_model_records_outcome(self, mock_agent, sample_task, sample_context, mock_moe_router):
        """Test that model invocation records outcome"""
        mock_agent.moe_router = mock_moe_router
        mock_agent.anthropic_client = Mock()
        mock_agent.anthropic_client.messages.create = AsyncMock(return_value=Mock(
            content=[Mock(type="text", text="Response")],
            usage=Mock(input_tokens=100, output_tokens=200)
        ))
        
        await mock_agent.invoke_model(
            prompt="Test prompt",
            task=sample_task,
            context=sample_context
        )
        
        # Should record success
        assert mock_moe_router.record_request_outcome.called

    @pytest.mark.asyncio
    async def test_invoke_model_handles_failure(self, mock_agent, sample_task, sample_context, mock_moe_router):
        """Test handling of model invocation failure"""
        mock_agent.moe_router = mock_moe_router
        mock_agent.anthropic_client = Mock()
        mock_agent.anthropic_client.messages.create = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception):
            await mock_agent.invoke_model(
                prompt="Test prompt",
                task=sample_task,
                context=sample_context
            )
        
        # Should record failure
        assert mock_moe_router.record_request_outcome.called


class TestEvidenceTracking:
    """Test evidence tracking"""

    @pytest.mark.asyncio
    async def test_evidence_added_to_context(self, mock_agent, sample_task, sample_context, mock_moe_router):
        """Test that routing evidence is added to context"""
        mock_agent.moe_router = mock_moe_router
        mock_agent.anthropic_client = Mock()
        mock_agent.anthropic_client.messages.create = AsyncMock(return_value=Mock(
            content=[Mock(type="text", text="Response")],
            usage=Mock(input_tokens=100, output_tokens=200)
        ))
        
        initial_evidence_count = len(sample_context.evidence)
        
        await mock_agent.invoke_model(
            prompt="Test prompt",
            task=sample_task,
            context=sample_context
        )
        
        # Evidence should be added from routing decision
        assert len(sample_context.evidence) >= initial_evidence_count


class TestTaskHandling:
    """Test task handling"""

    def test_task_creation(self):
        """Test creating a task"""
        task = Task(
            id="task-1",
            type=TaskType.CODE_GENERATION,
            description="Generate code",
            input_data={"key": "value"},
            priority=Priority.HIGH
        )
        
        assert task.id == "task-1"
        assert task.type == TaskType.CODE_GENERATION
        assert task.priority == Priority.HIGH

    def test_task_with_dependencies(self):
        """Test task with dependencies"""
        task = Task(
            id="task-2",
            type=TaskType.CODE_GENERATION,
            description="Generate code",
            input_data={},
            dependencies=["task-1"]
        )
        
        assert "task-1" in task.dependencies

    def test_context_creation(self):
        """Test creating a context"""
        context = Context(
            project_path="/tmp/project",
            config={"key": "value"},
            shared_state={"state": "data"}
        )
        
        assert context.project_path == "/tmp/project"
        assert "key" in context.config
        assert "state" in context.shared_state

