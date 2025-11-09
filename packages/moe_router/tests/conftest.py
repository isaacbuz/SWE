"""
Pytest configuration and fixtures for MoE Router tests
"""
import pytest
from pathlib import Path
from typing import List
from unittest.mock import Mock, MagicMock

from moe_router.models import (
    ModelDefinition,
    RoutingRequest,
    TaskType,
    Provider,
    ModelCapability
)
from moe_router.router import MoERouter


@pytest.fixture
def sample_models() -> List[ModelDefinition]:
    """Create sample model definitions for testing"""
    return [
        ModelDefinition(
            id="claude-3-opus",
            provider=Provider.ANTHROPIC,
            capabilities=[
                ModelCapability.REASONING,
                ModelCapability.CODE,
                ModelCapability.TOOLS,
                ModelCapability.FUNCTION_CALLING
            ],
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
            context_window=200000,
            quality_score=0.95,
            max_output_tokens=4096,
            supports_system_prompt=True,
            supports_streaming=True,
            latency_p50_ms=1200,
            latency_p95_ms=2500,
            enabled=True
        ),
        ModelDefinition(
            id="gpt-4-turbo",
            provider=Provider.OPENAI,
            capabilities=[
                ModelCapability.REASONING,
                ModelCapability.CODE,
                ModelCapability.TOOLS,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE
            ],
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
            context_window=128000,
            quality_score=0.92,
            max_output_tokens=4096,
            supports_system_prompt=True,
            supports_streaming=True,
            latency_p50_ms=800,
            latency_p95_ms=1500,
            enabled=True
        ),
        ModelDefinition(
            id="claude-3-haiku",
            provider=Provider.ANTHROPIC,
            capabilities=[
                ModelCapability.CODE,
                ModelCapability.TOOLS
            ],
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            context_window=200000,
            quality_score=0.75,
            max_output_tokens=4096,
            supports_system_prompt=True,
            supports_streaming=True,
            latency_p50_ms=400,
            latency_p95_ms=800,
            enabled=True
        ),
        ModelDefinition(
            id="gemini-pro",
            provider=Provider.GOOGLE,
            capabilities=[
                ModelCapability.CODE,
                ModelCapability.TOOLS
            ],
            cost_per_1k_input=0.0005,
            cost_per_1k_output=0.0015,
            context_window=32000,
            quality_score=0.80,
            max_output_tokens=2048,
            supports_system_prompt=True,
            supports_streaming=True,
            latency_p50_ms=600,
            latency_p95_ms=1200,
            enabled=True
        ),
    ]


@pytest.fixture
def basic_routing_request() -> RoutingRequest:
    """Create a basic routing request"""
    return RoutingRequest(
        task_type=TaskType.CODE_GENERATION,
        task_description="Generate a REST API endpoint for user authentication",
        estimated_input_tokens=500,
        estimated_output_tokens=1000,
        quality_requirement=0.8,
        cost_budget=0.05
    )


@pytest.fixture
def router_with_mock_models(sample_models, tmp_path):
    """Create router with mock model registry"""
    # Create a temporary models.yaml file
    import yaml
    models_data = {
        "models": [model.dict() for model in sample_models],
        "task_preferences": {
            "code_generation": {
                "preferred": ["gpt-4-turbo", "claude-3-opus"]
            }
        }
    }
    
    config_file = tmp_path / "models.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(models_data, f)
    
    router = MoERouter(
        config_path=str(config_file),
        enable_learning=False,
        enable_circuit_breaker=True
    )
    return router


@pytest.fixture
def router_with_learning(sample_models, tmp_path):
    """Create router with learning enabled"""
    import yaml
    models_data = {
        "models": [model.dict() for model in sample_models],
        "task_preferences": {}
    }
    
    config_file = tmp_path / "models.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(models_data, f)
    
    router = MoERouter(
        config_path=str(config_file),
        enable_learning=True,
        enable_circuit_breaker=True
    )
    return router


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    return Mock()


@pytest.fixture
def mock_performance_tracker():
    """Mock performance tracker"""
    tracker = Mock()
    tracker.get_recommendation_weight.return_value = 0.8
    tracker.record_outcome = Mock()
    return tracker

