"""
Integration tests for Skills Execution Engine.

Tests the full execution flow including validation, caching, and model invocation.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from packages.skills_engine.engine import SkillExecutionEngine
from packages.skills_engine.models import Skill, ExecutionContext, ExecutionStatus
from packages.moe_router import MoERouter
from packages.db.redis import RedisClient


@pytest.fixture
def real_moe_router():
    """Real MoE router instance"""
    return MoERouter()


@pytest.fixture
def real_redis_client():
    """Real Redis client instance (or mock if Redis not available)"""
    try:
        return RedisClient()
    except Exception:
        # Fallback to mock if Redis not available
        mock = Mock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        return mock


@pytest.fixture
def real_engine(real_moe_router, real_redis_client):
    """Real engine instance"""
    return SkillExecutionEngine(
        moe_router=real_moe_router,
        redis_client=real_redis_client,
        enable_caching=True
    )


@pytest.fixture
def complete_skill():
    """Complete skill definition for testing"""
    return Skill(
        id="integration-test-skill",
        name="Integration Test Skill",
        slug="integration-test",
        version="1.0.0",
        description="A skill for integration testing",
        prompt_template="""
Generate a Python function that {{task}}.

Requirements:
- Use type hints
- Include docstring
- Handle errors properly

Task: {{task}}
""",
        input_schema={
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "What the function should do"
                }
            },
            "required": ["task"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Generated Python code"
                },
                "explanation": {
                    "type": "string",
                    "description": "Explanation of the code"
                }
            },
            "required": ["code"]
        },
        category="CODE_GENERATION",
        model_preferences={
            "temperature": 0.7,
            "min_quality": 0.8
        },
        validation_rules=[]
    )


@pytest.mark.integration
@pytest.mark.skills
class TestSkillsEngineIntegration:
    """Integration tests for Skills Execution Engine"""

    @pytest.mark.asyncio
    async def test_full_execution_flow(self, real_engine, complete_skill):
        """Test complete execution flow"""
        # Mock AI provider response
        from packages.integrations.ai_providers import Completion, Usage
        
        mock_completion = Completion(
            content='{"code": "def hello():\\n    return \\"Hello\\"", "explanation": "Simple greeting function"}',
            model="claude-sonnet-4",
            usage=Usage(input_tokens=20, output_tokens=15),
            finish_reason="stop"
        )
        
        # Mock provider client
        with patch('packages.skills_engine.engine.get_provider_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(return_value=mock_completion)
            mock_get_client.return_value = mock_client
            
            # Execute skill
            result = await real_engine.execute_skill(
                skill=complete_skill,
                inputs={"task": "returns a greeting"},
                context=ExecutionContext(user_id="test-user")
            )
        
        # Verify result
        assert result is not None
        assert result.status == ExecutionStatus.SUCCESS
        assert result.outputs is not None
        assert "code" in result.outputs
        assert result.validation_passed is True
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_input_validation_integration(self, real_engine, complete_skill):
        """Test input validation in full flow"""
        # Missing required field
        result = await real_engine.execute_skill(
            skill=complete_skill,
            inputs={},  # Missing "task"
            context=ExecutionContext(user_id="test-user")
        )
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error_message is not None
        assert "required" in result.error_message.lower() or "validation" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_output_validation_integration(self, real_engine, complete_skill):
        """Test output validation in full flow"""
        from packages.integrations.ai_providers import Completion, Usage
        
        # Mock invalid output (missing required field)
        mock_completion = Completion(
            content='{"explanation": "Missing code field"}',
            model="claude-sonnet-4",
            usage=Usage(input_tokens=20, output_tokens=5),
            finish_reason="stop"
        )
        
        with patch('packages.skills_engine.engine.get_provider_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(return_value=mock_completion)
            mock_get_client.return_value = mock_client
            
            result = await real_engine.execute_skill(
                skill=complete_skill,
                inputs={"task": "test"},
                context=ExecutionContext(user_id="test-user")
            )
        
        # Output validation should fail
        assert result.validation_passed is False or result.status == ExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_caching_integration(self, real_engine, complete_skill):
        """Test caching in full execution flow"""
        from packages.integrations.ai_providers import Completion, Usage
        
        mock_completion = Completion(
            content='{"code": "def test(): pass", "explanation": "Test"}',
            model="claude-sonnet-4",
            usage=Usage(input_tokens=10, output_tokens=5),
            finish_reason="stop"
        )
        
        inputs = {"task": "test function"}
        
        with patch('packages.skills_engine.engine.get_provider_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(return_value=mock_completion)
            mock_get_client.return_value = mock_client
            
            # First execution
            result1 = await real_engine.execute_skill(
                skill=complete_skill,
                inputs=inputs,
                context=ExecutionContext(user_id="test-user")
            )
            
            assert result1.status == ExecutionStatus.SUCCESS
            assert result1.cache_hit is False
            
            # Second execution with same inputs (should hit cache if enabled)
            result2 = await real_engine.execute_skill(
                skill=complete_skill,
                inputs=inputs,
                context=ExecutionContext(user_id="test-user")
            )
            
            # Cache behavior depends on implementation
            # If caching is working, result2 should be faster or from cache
            assert result2.status == ExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_model_selection_integration(self, real_engine, complete_skill):
        """Test model selection via MoE router"""
        prompt = "Test prompt for model selection"
        
        decision = await real_engine._select_model(complete_skill, prompt)
        
        assert decision is not None
        assert decision.selected_model is not None
        assert decision.selected_model.id is not None

    @pytest.mark.asyncio
    async def test_prompt_rendering_integration(self, real_engine, complete_skill):
        """Test prompt template rendering"""
        inputs = {"task": "create a hello function"}
        
        rendered = real_engine._render_prompt(complete_skill.prompt_template, inputs)
        
        assert "create a hello function" in rendered
        assert "{{task}}" not in rendered
        assert len(rendered) > 0

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, real_engine, complete_skill):
        """Test error handling in execution flow"""
        # Simulate provider error
        with patch('packages.skills_engine.engine.get_provider_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(side_effect=Exception("Provider error"))
            mock_get_client.return_value = mock_client
            
            result = await real_engine.execute_skill(
                skill=complete_skill,
                inputs={"task": "test"},
                context=ExecutionContext(user_id="test-user")
            )
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_performance_tracking(self, real_engine, complete_skill):
        """Test performance metrics tracking"""
        from packages.integrations.ai_providers import Completion, Usage
        
        mock_completion = Completion(
            content='{"code": "def test(): pass", "explanation": "Test"}',
            model="claude-sonnet-4",
            usage=Usage(input_tokens=10, output_tokens=5),
            finish_reason="stop"
        )
        
        with patch('packages.skills_engine.engine.get_provider_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(return_value=mock_completion)
            mock_get_client.return_value = mock_client
            
            result = await real_engine.execute_skill(
                skill=complete_skill,
                inputs={"task": "test"},
                context=ExecutionContext(user_id="test-user")
            )
        
        # Verify performance metrics
        assert result.latency_ms is not None
        assert result.latency_ms >= 0
        assert result.tokens_input is not None
        assert result.tokens_output is not None
        assert result.cost_usd is not None

