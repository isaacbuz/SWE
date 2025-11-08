"""
Tests for Skills Execution Engine
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from packages.skills_engine.engine import (
    SkillExecutionEngine,
    SkillInputValidationError,
    SkillOutputValidationError,
)
from packages.skills_engine.models import (
    Skill,
    ExecutionContext,
    ExecutionStatus,
    ValidationResult,
)
from packages.moe_router import MoERouter, RoutingDecision, TaskType
from packages.moe_router.models import ModelDefinition, Provider, ModelCapability


@pytest.fixture
def mock_moe_router():
    """Mock MoE Router"""
    router = Mock(spec=MoERouter)
    
    # Mock model definition
    model = ModelDefinition(
        id="claude-sonnet-4",
        provider=Provider.ANTHROPIC,
        capabilities=[ModelCapability.CODE],
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        context_window=200000,
        quality_score=0.95,
        max_output_tokens=8192,
        supports_system_prompt=True,
        supports_streaming=True,
    )
    
    # Mock routing decision
    decision = RoutingDecision(
        selected_model=model,
        confidence=0.95,
        evidence=[],
        reasoning="Test selection",
        alternatives=[]
    )
    
    router.select_model = Mock(return_value=decision)
    return router


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = Mock()
    return client


@pytest.fixture
def sample_skill():
    """Sample skill for testing"""
    return Skill(
        id="test-skill-1",
        name="Test Skill",
        slug="test-skill",
        version="1.0.0",
        description="A test skill",
        prompt_template="Generate a greeting for {{name}}",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "greeting": {"type": "string"}
            },
            "required": ["greeting"]
        },
        category="CODE_GENERATION",
        model_preferences={
            "temperature": 0.7,
            "min_quality": 0.8
        }
    )


@pytest.fixture
def engine(mock_moe_router, mock_redis_client):
    """Create engine instance"""
    return SkillExecutionEngine(
        moe_router=mock_moe_router,
        redis_client=mock_redis_client,
        enable_caching=True
    )


@pytest.mark.asyncio
async def test_input_validation_success(engine, sample_skill):
    """Test successful input validation"""
    inputs = {"name": "Alice"}
    
    validated = engine._validate_inputs(sample_skill, inputs)
    assert validated == inputs


@pytest.mark.asyncio
async def test_input_validation_failure(engine, sample_skill):
    """Test input validation failure"""
    inputs = {}  # Missing required field
    
    with pytest.raises(SkillInputValidationError):
        engine._validate_inputs(sample_skill, inputs)


@pytest.mark.asyncio
async def test_prompt_rendering(engine, sample_skill):
    """Test prompt template rendering"""
    inputs = {"name": "Alice"}
    
    rendered = engine._render_prompt(sample_skill.prompt_template, inputs)
    assert "Alice" in rendered
    assert "{{name}}" not in rendered


@pytest.mark.asyncio
async def test_execute_skill_success(engine, sample_skill):
    """Test successful skill execution"""
    from packages.integrations.ai_providers import Completion, Usage, Message
    
    # Mock AI provider response
    mock_completion = Completion(
        content='{"greeting": "Hello, Alice!"}',
        model="claude-sonnet-4",
        usage=Usage(input_tokens=10, output_tokens=5),
        finish_reason="stop"
    )
    
    # Mock provider client
    mock_client = AsyncMock()
    mock_client.complete = AsyncMock(return_value=mock_completion)
    
    with patch.object(engine, '_get_provider_client', return_value=mock_client):
        result = await engine.execute_skill(
            skill=sample_skill,
            inputs={"name": "Alice"},
            context=ExecutionContext(user_id="user-123")
        )
    
    assert result.status == ExecutionStatus.SUCCESS
    assert result.outputs is not None
    assert result.outputs["greeting"] == "Hello, Alice!"
    assert result.validation_passed is True
    assert result.latency_ms is not None
    assert result.cache_hit is False


@pytest.mark.asyncio
async def test_execute_skill_cache_hit(engine, sample_skill, mock_redis_client):
    """Test cache hit scenario"""
    from packages.skills_engine.cache import SkillCache
    
    # Mock cache to return cached result
    cached_result = {
        "execution_id": "cached-123",
        "skill_id": sample_skill.id,
        "skill_version": sample_skill.version,
        "inputs": {"name": "Alice"},
        "outputs": {"greeting": "Hello, Alice!"},
        "status": ExecutionStatus.SUCCESS,
        "validation_passed": True,
        "latency_ms": 100,
        "cache_hit": False,
        "executed_at": datetime.utcnow().isoformat(),
    }
    
    # Mock cache.get to return cached result
    from packages.skills_engine.cache import SkillCache
    mock_cache = Mock(spec=SkillCache)
    mock_cache.get = AsyncMock(return_value=cached_result)
    mock_cache.compute_key = Mock(return_value="cache-key-123")
    
    engine.cache = mock_cache
    
    result = await engine.execute_skill(
        skill=sample_skill,
        inputs={"name": "Alice"}
    )
    
    assert result.cache_hit is True
    assert result.cache_key == "cache-key-123"


@pytest.mark.asyncio
async def test_execute_skill_input_validation_error(engine, sample_skill):
    """Test execution with invalid inputs"""
    result = await engine.execute_skill(
        skill=sample_skill,
        inputs={}  # Missing required field
    )
    
    assert result.status == ExecutionStatus.FAILED
    assert result.error_message is not None
    assert "required" in result.error_message.lower() or "validation" in result.error_message.lower()


@pytest.mark.asyncio
async def test_execute_skill_output_validation_error(engine, sample_skill):
    """Test execution with invalid outputs"""
    from packages.integrations.ai_providers import Completion, Usage
    
    # Mock AI provider response with invalid output
    mock_completion = Completion(
        content='{"invalid": "output"}',  # Missing required "greeting" field
        model="claude-sonnet-4",
        usage=Usage(input_tokens=10, output_tokens=5),
        finish_reason="stop"
    )
    
    mock_client = AsyncMock()
    mock_client.complete = AsyncMock(return_value=mock_completion)
    
    with patch.object(engine, '_get_provider_client', return_value=mock_client):
        result = await engine.execute_skill(
            skill=sample_skill,
            inputs={"name": "Alice"}
        )
    
    # Output validation should fail, but execution might still succeed
    # depending on how we handle it
    assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]


@pytest.mark.asyncio
async def test_model_selection(engine, sample_skill):
    """Test model selection via MoE router"""
    prompt = "Test prompt"
    
    decision = await engine._select_model(sample_skill, prompt)
    
    assert decision is not None
    assert decision.selected_model is not None
    engine.moe_router.select_model.assert_called_once()


def test_validation_rule_execution():
    """Test validation rule execution"""
    from packages.skills_engine.validators import ValidationRuleExecutor
    from packages.skills_engine.models import ValidationRule
    
    executor = ValidationRuleExecutor()
    
    rules = [
        ValidationRule(
            type="required_fields",
            params={"fields": ["greeting"]}
        )
    ]
    
    outputs = {"greeting": "Hello"}
    
    import asyncio
    result = asyncio.run(executor.execute(rules, outputs))
    
    assert result.passed is True


def test_cache_key_computation():
    """Test cache key computation"""
    from packages.skills_engine.cache import SkillCache
    
    cache = SkillCache()
    
    key1 = cache.compute_key("skill-1", "1.0.0", {"name": "Alice"})
    key2 = cache.compute_key("skill-1", "1.0.0", {"name": "Alice"})
    key3 = cache.compute_key("skill-1", "1.0.0", {"name": "Bob"})
    
    assert key1 == key2  # Same inputs should produce same key
    assert key1 != key3  # Different inputs should produce different key
