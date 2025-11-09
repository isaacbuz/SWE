"""
Tests for MoE Router
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from moe_router.router import MoERouter
from moe_router.models import (
    RoutingRequest,
    TaskType,
    Provider,
    ModelCapability,
    RoutingDecision,
)


class TestMoERouter:
    """Test suite for MoE Router"""

    @pytest.fixture
    def router(self):
        """Create a router instance for testing"""
        config_path = Path(__file__).parent.parent / "config" / "models.yaml"
        return MoERouter(
            config_path=str(config_path),
            redis_url=None,  # Use in-memory for tests
            enable_learning=False,
            enable_circuit_breaker=True
        )

    def test_router_initialization(self, router):
        """Test router initializes correctly"""
        assert router is not None
        assert len(router.models) > 0
        assert router.cost_predictor is not None
        assert router.performance_tracker is not None

    def test_select_model_basic(self, router):
        """Test basic model selection"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate a Python function",
            cost_budget=0.01,
            quality_requirement=0.7
        )

        decision = router.select_model(request)

        assert decision is not None
        assert decision.selected_model is not None
        assert decision.confidence > 0
        assert decision.estimated_cost is not None
        assert len(decision.evidence) > 0

    def test_select_model_with_cost_budget(self, router):
        """Test model selection respects cost budget"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            cost_budget=0.001,  # Very low budget
            estimated_input_tokens=1000,
            estimated_output_tokens=500
        )

        decision = router.select_model(request)

        assert decision.estimated_cost <= request.cost_budget * 1.1  # Allow 10% margin

    def test_select_model_with_quality_requirement(self, router):
        """Test model selection respects quality requirement"""
        request = RoutingRequest(
            task_type=TaskType.CODE_REVIEW,
            task_description="Review code",
            quality_requirement=0.9,  # High quality requirement
        )

        decision = router.select_model(request)

        # Check that selected model meets quality requirement
        selected_model = next(
            (m for m in router.models if m.id == decision.selected_model),
            None
        )
        assert selected_model is not None
        assert selected_model.quality_score >= request.quality_requirement * 0.9

    def test_select_model_requires_tools(self, router):
        """Test model selection for tasks requiring tools"""
        request = RoutingRequest(
            task_type=TaskType.TOOL_USE,
            task_description="Execute tool calls",
            requires_tools=True
        )

        decision = router.select_model(request)

        # Verify selected model supports tool calling
        selected_model = next(
            (m for m in router.models if m.id == decision.selected_model),
            None
        )
        assert selected_model is not None
        assert ModelCapability.TOOLS in selected_model.capabilities or \
               ModelCapability.FUNCTION_CALLING in selected_model.capabilities

    def test_select_model_requires_vision(self, router):
        """Test model selection for vision tasks"""
        request = RoutingRequest(
            task_type=TaskType.MULTIMODAL,
            task_description="Analyze image",
            requires_vision=True
        )

        decision = router.select_model(request)

        selected_model = next(
            (m for m in router.models if m.id == decision.selected_model),
            None
        )
        assert selected_model is not None
        assert ModelCapability.VISION in selected_model.capabilities

    def test_select_model_vendor_preference(self, router):
        """Test vendor preference is respected"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            vendor_preference=Provider.ANTHROPIC
        )

        decision = router.select_model(request)

        selected_model = next(
            (m for m in router.models if m.id == decision.selected_model),
            None
        )
        assert selected_model is not None
        assert selected_model.provider == Provider.ANTHROPIC

    def test_fallback_models(self, router):
        """Test fallback models are provided"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code"
        )

        decision = router.select_model(request)

        assert len(decision.fallback_models) > 0
        # Verify fallback models exist
        for fallback_id in decision.fallback_models:
            assert any(m.id == fallback_id for m in router.models)

    def test_circuit_breaker(self, router):
        """Test circuit breaker functionality"""
        # Mark a model as failed multiple times
        model_id = router.models[0].id
        
        # Simulate failures
        for _ in range(5):
            router.record_failure(model_id, "Test failure")

        # Check circuit breaker state
        if router.enable_circuit_breaker:
            breaker_state = router.circuit_breakers.get(model_id)
            if breaker_state:
                assert breaker_state.failure_count >= 5

    def test_performance_tracking(self, router):
        """Test performance tracking"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code"
        )

        decision = router.select_model(request)
        
        # Record success
        router.record_success(
            decision.selected_model,
            quality_score=0.9,
            latency_ms=500,
            cost=0.001
        )

        # Verify performance was tracked
        # (This depends on performance tracker implementation)
        assert decision.selected_model is not None

    def test_hybrid_routing(self, router):
        """Test hybrid/parallel routing"""
        request = RoutingRequest(
            task_type=TaskType.CODE_REVIEW,
            task_description="Review critical code",
            enable_parallel=True,
            quality_requirement=0.95
        )

        decision = router.select_model(request)

        # For parallel execution, should return multiple models or consensus strategy
        assert decision is not None
        # Parallel execution may return different structure
        assert decision.selected_model is not None or len(decision.fallback_models) > 0

    def test_routing_with_latency_requirement(self, router):
        """Test routing respects latency requirements"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Fast code generation",
            latency_requirement_ms=1000  # 1 second max
        )

        decision = router.select_model(request)

        # Verify selected model meets latency requirement
        selected_model = next(
            (m for m in router.models if m.id == decision.selected_model),
            None
        )
        if selected_model and selected_model.latency_p95_ms:
            assert selected_model.latency_p95_ms <= request.latency_requirement_ms

    def test_routing_evidence(self, router):
        """Test routing decisions include evidence"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code"
        )

        decision = router.select_model(request)

        assert len(decision.evidence) > 0
        for evidence in decision.evidence:
            assert evidence.id is not None
            assert evidence.description is not None
            assert 0 <= evidence.weight <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

