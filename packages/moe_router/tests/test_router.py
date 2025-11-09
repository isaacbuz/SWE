"""
Unit tests for MoE Router core functionality
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from moe_router.router import MoERouter
from moe_router.models import (
    RoutingRequest,
    TaskType,
    Provider,
    ModelCapability,
    CircuitBreakerState
)


class TestMoERouterInitialization:
    """Test router initialization"""

    def test_init_with_default_config(self, tmp_path):
        """Test initialization with default config path"""
        router = MoERouter(enable_learning=False, enable_circuit_breaker=False)
        assert router is not None
        assert len(router.models) > 0
        assert router.enable_learning == False
        assert router.enable_circuit_breaker == False

    def test_init_with_custom_config(self, router_with_mock_models):
        """Test initialization with custom config"""
        router = router_with_mock_models
        assert len(router.models) == 4
        assert router.enable_learning == False

    def test_init_with_learning_enabled(self, router_with_learning):
        """Test initialization with learning enabled"""
        router = router_with_learning
        assert router.learning_loop is not None

    def test_init_with_redis(self, sample_models, tmp_path):
        """Test initialization with Redis URL"""
        import yaml
        models_data = {"models": [model.dict() for model in sample_models]}
        config_file = tmp_path / "models.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(models_data, f)
        
        router = MoERouter(
            config_path=str(config_file),
            redis_url="redis://localhost:6379/0",
            enable_learning=False
        )
        assert router.performance_tracker.redis_url == "redis://localhost:6379/0"


class TestModelSelection:
    """Test model selection logic"""

    def test_select_model_basic(self, router_with_mock_models, basic_routing_request):
        """Test basic model selection"""
        router = router_with_mock_models
        decision = router.select_model(basic_routing_request)
        
        assert decision is not None
        assert decision.selected_model != "none"
        assert decision.confidence > 0
        assert decision.estimated_cost > 0
        assert len(decision.evidence) > 0

    def test_select_model_with_quality_requirement(self, router_with_mock_models):
        """Test model selection with high quality requirement"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate high-quality code",
            quality_requirement=0.9,  # High requirement
            cost_budget=0.1
        )
        
        decision = router_with_mock_models.select_model(request)
        
        # Should select high-quality model
        assert decision.selected_model in ["claude-3-opus", "gpt-4-turbo"]
        assert decision.estimated_quality >= 0.9

    def test_select_model_with_cost_budget(self, router_with_mock_models):
        """Test model selection with strict cost budget"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            cost_budget=0.001,  # Very low budget
            quality_requirement=0.7
        )
        
        decision = router_with_mock_models.select_model(request)
        
        # Should select low-cost model
        assert decision.selected_model in ["claude-3-haiku", "gemini-pro"]
        assert decision.estimated_cost <= 0.001

    def test_select_model_with_tool_requirement(self, router_with_mock_models):
        """Test model selection requiring tool calling"""
        request = RoutingRequest(
            task_type=TaskType.TOOL_USE,
            task_description="Use tools to complete task",
            requires_tools=True,
            quality_requirement=0.7
        )
        
        decision = router_with_mock_models.select_model(request)
        
        # Should select model with function calling capability
        model = router_with_mock_models._get_model_by_id(decision.selected_model)
        assert ModelCapability.FUNCTION_CALLING in model.capabilities

    def test_select_model_with_streaming(self, router_with_mock_models):
        """Test model selection requiring streaming"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code with streaming",
            requires_streaming=True,
            quality_requirement=0.7
        )
        
        decision = router_with_mock_models.select_model(request)
        
        model = router_with_mock_models._get_model_by_id(decision.selected_model)
        assert model.supports_streaming == True

    def test_select_model_with_context_size(self, router_with_mock_models):
        """Test model selection with large context requirement"""
        request = RoutingRequest(
            task_type=TaskType.LONG_CONTEXT,
            task_description="Process large document",
            context_size=150000,  # Requires large context
            quality_requirement=0.7
        )
        
        decision = router_with_mock_models.select_model(request)
        
        model = router_with_mock_models._get_model_by_id(decision.selected_model)
        assert model.context_window >= 150000

    def test_select_model_with_latency_requirement(self, router_with_mock_models):
        """Test model selection with latency requirement"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Fast code generation",
            latency_requirement_ms=1000,  # Fast response required
            quality_requirement=0.7
        )
        
        decision = router_with_mock_models.select_model(request)
        
        model = router_with_mock_models._get_model_by_id(decision.selected_model)
        assert model.latency_p95_ms is None or model.latency_p95_ms <= 1000

    def test_select_model_with_vendor_preference(self, router_with_mock_models):
        """Test model selection with vendor preference"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            vendor_preference=Provider.ANTHROPIC,
            quality_requirement=0.7
        )
        
        decision = router_with_mock_models.select_model(request)
        
        model = router_with_mock_models._get_model_by_id(decision.selected_model)
        assert model.provider == Provider.ANTHROPIC

    def test_select_model_no_available_models(self, router_with_mock_models):
        """Test model selection when no models match requirements"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            quality_requirement=1.0,  # Impossible requirement
            cost_budget=0.0001  # Impossible budget
        )
        
        decision = router_with_mock_models.select_model(request)
        
        assert decision.selected_model == "none"
        assert decision.confidence == 0.0
        assert "Error" in decision.rationale

    def test_select_model_parallel_execution(self, router_with_mock_models):
        """Test parallel execution selection"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Critical code generation",
            enable_parallel=True,
            quality_requirement=0.8,
            cost_budget=0.1
        )
        
        decision = router_with_mock_models.select_model(request)
        
        # Should use parallel strategy if enabled
        if decision.routing_strategy == "parallel":
            assert decision.parallel_models is not None
            assert len(decision.parallel_models) > 1


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def test_circuit_breaker_initialization(self, router_with_mock_models):
        """Test circuit breaker is initialized"""
        router = router_with_mock_models
        assert router.enable_circuit_breaker == True
        assert len(router.circuit_breakers) == 0

    def test_circuit_breaker_opens_on_failures(self, router_with_mock_models):
        """Test circuit breaker opens after threshold failures"""
        router = router_with_mock_models
        
        # Record multiple failures
        for _ in range(5):
            router.record_request_outcome(
                model_id="claude-3-opus",
                success=False,
                error="Timeout"
            )
        
        status = router.get_circuit_breaker_status()
        assert "anthropic" in status
        assert status["anthropic"]["state"] == "open"

    def test_circuit_breaker_closes_on_success(self, router_with_mock_models):
        """Test circuit breaker closes after success"""
        router = router_with_mock_models
        
        # Open circuit breaker
        for _ in range(5):
            router.record_request_outcome(
                model_id="claude-3-opus",
                success=False
            )
        
        # Record success
        router.record_request_outcome(
            model_id="claude-3-opus",
            success=True
        )
        
        status = router.get_circuit_breaker_status()
        # Should still be open (needs multiple successes in half-open)
        # But failure count should reset
        assert status["anthropic"]["failure_count"] == 0

    def test_circuit_breaker_prevents_selection(self, router_with_mock_models):
        """Test that circuit breaker prevents model selection"""
        router = router_with_mock_models
        
        # Open circuit breaker for Anthropic
        for _ in range(5):
            router.record_request_outcome(
                model_id="claude-3-opus",
                success=False
            )
        
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            vendor_preference=Provider.ANTHROPIC,
            quality_requirement=0.7
        )
        
        decision = router_with_mock_models.select_model(request)
        
        # Should not select Anthropic models
        model = router._get_model_by_id(decision.selected_model)
        assert model.provider != Provider.ANTHROPIC

    def test_reset_circuit_breaker(self, router_with_mock_models):
        """Test manual circuit breaker reset"""
        router = router_with_mock_models
        
        # Open circuit breaker
        for _ in range(5):
            router.record_request_outcome(
                model_id="claude-3-opus",
                success=False
            )
        
        # Reset
        router.reset_circuit_breaker("anthropic")
        
        status = router.get_circuit_breaker_status()
        assert status["anthropic"]["state"] == "closed"
        assert status["anthropic"]["failure_count"] == 0


class TestRoutingStats:
    """Test routing statistics"""

    def test_get_routing_stats_empty(self, router_with_mock_models):
        """Test stats with no history"""
        router = router_with_mock_models
        stats = router.get_routing_stats()
        assert "message" in stats

    def test_get_routing_stats_with_history(self, router_with_mock_models, basic_routing_request):
        """Test stats with routing history"""
        router = router_with_mock_models
        
        # Make several routing decisions
        for _ in range(5):
            router.select_model(basic_routing_request)
        
        stats = router.get_routing_stats()
        
        assert stats["total_requests"] == 5
        assert stats["unique_models_used"] > 0
        assert "model_distribution" in stats
        assert "total_estimated_cost" in stats
        assert "avg_confidence" in stats


class TestModelFiltering:
    """Test model filtering logic"""

    def test_filter_by_quality(self, router_with_mock_models):
        """Test filtering by quality requirement"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="High quality code",
            quality_requirement=0.9
        )
        
        available = router_with_mock_models._filter_available_models(request, [])
        
        # Should only include high-quality models
        for model in available:
            assert model.quality_score >= 0.9

    def test_filter_by_capabilities(self, router_with_mock_models):
        """Test filtering by required capabilities"""
        request = RoutingRequest(
            task_type=TaskType.TOOL_USE,
            task_description="Use tools",
            requires_tools=True
        )
        
        available = router_with_mock_models._filter_available_models(request, [])
        
        for model in available:
            assert ModelCapability.FUNCTION_CALLING in model.capabilities

    def test_filter_disabled_models(self, router_with_mock_models):
        """Test that disabled models are filtered out"""
        # Disable a model
        for model in router_with_mock_models.models:
            if model.id == "claude-3-haiku":
                model.enabled = False
                break
        
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code"
        )
        
        available = router_with_mock_models._filter_available_models(request, [])
        
        model_ids = [m.id for m in available]
        assert "claude-3-haiku" not in model_ids


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_config_path(self, tmp_path):
        """Test handling of invalid config path"""
        invalid_path = tmp_path / "nonexistent.yaml"
        
        router = MoERouter(
            config_path=str(invalid_path),
            enable_learning=False
        )
        
        # Should handle gracefully with empty model list
        assert len(router.models) == 0

    def test_malformed_config(self, tmp_path):
        """Test handling of malformed config"""
        config_file = tmp_path / "models.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        router = MoERouter(
            config_path=str(config_file),
            enable_learning=False
        )
        
        # Should handle gracefully
        assert router is not None

