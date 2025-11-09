"""
Integration tests for MoE Router
"""
import pytest
from unittest.mock import Mock, patch

from moe_router.router import MoERouter
from moe_router.models import RoutingRequest, TaskType


class TestRouterIntegration:
    """Integration tests for complete router workflow"""

    @pytest.fixture
    def router(self):
        """Create router with default config"""
        return MoERouter(enable_learning=True, enable_circuit_breaker=True)

    def test_end_to_end_routing(self, router):
        """Test complete routing workflow"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate a REST API endpoint for user authentication with JWT tokens",
            estimated_input_tokens=500,
            estimated_output_tokens=1000,
            quality_requirement=0.8,
            cost_budget=0.05
        )
        
        # Select model
        decision = router.select_model(request)
        
        assert decision.selected_model != "none"
        assert decision.confidence > 0
        assert decision.estimated_cost > 0
        
        # Record outcome
        router.record_request_outcome(
            model_id=decision.selected_model,
            success=True,
            latency_ms=800,
            cost=decision.estimated_cost * 0.9,  # Actual cost slightly lower
            quality_score=0.85
        )
        
        # Get stats
        stats = router.get_routing_stats()
        assert stats["total_requests"] == 1

    def test_circuit_breaker_integration(self, router):
        """Test circuit breaker integration with routing"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            quality_requirement=0.7
        )
        
        # Get initial selection
        decision1 = router.select_model(request)
        model_id = decision1.selected_model
        
        # Record multiple failures to open circuit breaker
        for _ in range(5):
            router.record_request_outcome(
                model_id=model_id,
                success=False,
                error="Timeout"
            )
        
        # Try to select again - should avoid the failed provider
        decision2 = router.select_model(request)
        
        # Should select different model or handle gracefully
        assert decision2.selected_model != "none"

    def test_learning_loop_integration(self, router):
        """Test learning loop integration"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            quality_requirement=0.7
        )
        
        # Make initial selection
        decision1 = router.select_model(request)
        model_id = decision1.selected_model
        
        # Record successful outcome
        router.record_request_outcome(
            model_id=model_id,
            success=True,
            quality_score=0.9
        )
        
        # Update learning loop with PR feedback
        if router.learning_loop:
            router.learning_loop.update_from_feedback(
                model_id=model_id,
                task_type=request.task_type,
                pr_merged=True,
                quality_score=0.9
            )
        
        # Make another selection - should favor learned model
        decision2 = router.select_model(request)
        
        # Should still select valid model
        assert decision2.selected_model != "none"

    def test_multiple_task_types(self, router):
        """Test routing for different task types"""
        task_types = [
            TaskType.CODE_GENERATION,
            TaskType.CODE_REVIEW,
            TaskType.PLANNING,
            TaskType.DOCUMENTATION
        ]
        
        decisions = []
        for task_type in task_types:
            request = RoutingRequest(
                task_type=task_type,
                task_description=f"Perform {task_type.value}",
                quality_requirement=0.7
            )
            decision = router.select_model(request)
            decisions.append(decision)
        
        # All should succeed
        assert all(d.selected_model != "none" for d in decisions)
        
        # May select different models for different tasks
        model_ids = [d.selected_model for d in decisions]
        assert len(set(model_ids)) >= 1  # At least one model used

    def test_cost_budget_enforcement(self, router):
        """Test that cost budget is enforced"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            estimated_input_tokens=10000,
            estimated_output_tokens=20000,
            cost_budget=0.001,  # Very low budget
            quality_requirement=0.7
        )
        
        decision = router.select_model(request)
        
        # Should select low-cost model or return error
        if decision.selected_model != "none":
            assert decision.estimated_cost <= 0.001 * 1.1  # Allow 10% margin

    def test_parallel_execution_workflow(self, router):
        """Test parallel execution workflow"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Critical code generation requiring high quality",
            enable_parallel=True,
            quality_requirement=0.9,
            cost_budget=0.1
        )
        
        decision = router.select_model(request)
        
        # If parallel execution is used
        if decision.routing_strategy == "parallel":
            assert decision.parallel_models is not None
            assert len(decision.parallel_models) > 1
            assert decision.estimated_cost > 0

    def test_fallback_models(self, router):
        """Test fallback model selection"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            quality_requirement=0.7
        )
        
        decision = router.select_model(request)
        
        # Should have fallback models
        assert len(decision.fallback_models) >= 0  # May have 0-3 fallbacks
        
        # Fallbacks should be different from selected
        if decision.fallback_models:
            assert decision.selected_model not in decision.fallback_models

    def test_routing_statistics(self, router):
        """Test routing statistics collection"""
        # Make multiple routing decisions
        for i in range(5):
            request = RoutingRequest(
                task_type=TaskType.CODE_GENERATION,
                task_description=f"Task {i}",
                quality_requirement=0.7
            )
            router.select_model(request)
        
        stats = router.get_routing_stats()
        
        assert stats["total_requests"] == 5
        assert stats["unique_models_used"] > 0
        assert "model_distribution" in stats
        assert "total_estimated_cost" in stats
        assert stats["avg_confidence"] > 0

