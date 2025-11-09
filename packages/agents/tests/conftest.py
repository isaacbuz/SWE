"""
Pytest configuration and fixtures for Agent tests
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
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
from packages.agents.registry import AgentRegistry, AgentCapability


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    async def execute(self, task: Task, context: Context) -> AgentResult:
        return AgentResult(
            success=True,
            output={"result": "mock output"},
            evidence=[],
            metadata={"agent_id": self.agent_id}
        )
    
    def get_system_prompt(self) -> str:
        return "You are a mock agent for testing."


@pytest.fixture
def mock_moe_router():
    """Mock MoE Router"""
    router = Mock()
    router.select_model = Mock(return_value=Mock(
        selected_model="claude-3-opus",
        confidence=0.9,
        estimated_cost=0.01,
        evidence=[],
        fallback_models=[]
    ))
    router.record_request_outcome = Mock()
    return router


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    client = AsyncMock()
    response = Mock()
    response.content = [Mock(type="text", text="Mock response")]
    response.usage = Mock(input_tokens=100, output_tokens=200)
    client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = AsyncMock()
    response = Mock()
    response.choices = [Mock(
        message=Mock(content="Mock response"),
        finish_reason="stop"
    )]
    response.usage = Mock(prompt_tokens=100, completion_tokens=200)
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


@pytest.fixture
def sample_task():
    """Create a sample task"""
    return Task(
        id="task-1",
        type=TaskType.CODE_GENERATION,
        description="Generate a REST API endpoint",
        input_data={"endpoint": "/users", "method": "GET"},
        priority=Priority.HIGH
    )


@pytest.fixture
def sample_context():
    """Create a sample context"""
    return Context(
        project_path="/tmp/test-project",
        config={"env": "test"},
        shared_state={},
        evidence=[],
        metadata={"user_id": "user-123"}
    )


@pytest.fixture
def sample_tool():
    """Create a sample tool"""
    return Tool(
        name="read_file",
        description="Read a file from the filesystem",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        },
        handler=lambda path: f"Content of {path}"
    )


@pytest.fixture
def agent_registry(mock_moe_router, mock_anthropic_client, mock_openai_client):
    """Create agent registry with mocks"""
    return AgentRegistry(
        moe_router=mock_moe_router,
        anthropic_client=mock_anthropic_client,
        openai_client=mock_openai_client
    )


@pytest.fixture
def mock_agent(mock_moe_router, mock_anthropic_client, mock_openai_client):
    """Create a mock agent"""
    return MockAgent(
        agent_id="test-agent",
        task_type=TaskType.CODE_GENERATION,
        moe_router=mock_moe_router,
        anthropic_client=mock_anthropic_client,
        openai_client=mock_openai_client
    )

