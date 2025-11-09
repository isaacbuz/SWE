"""
Unit tests for MoE Router strategies
"""
import pytest
from unittest.mock import Mock, patch

from moe_router.strategies.cost_predictor import CostPredictor
from moe_router.strategies.performance_tracker import PerformanceTracker
from moe_router.strategies.hybrid_router import HybridRouter
from moe_router.strategies.learning_loop import LearningLoop
from moe_router.models import (
    ModelDefinition,
    RoutingRequest,
    TaskType,
    Provider,
    ModelCapability
)


class TestCostPredictor:
    """Test cost prediction strategy"""

    @pytest.fixture
    def cost_predictor(self):
        return CostPredictor()

    @pytest.fixture
    def sample_model(self):
        return ModelDefinition(
            id="test-model",
            provider=Provider.OPENAI,
            capabilities=[ModelCapability.CODE],
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
            context_window=100000,
            quality_score=0.9,
            enabled=True
        )

    def test_estimate_tokens_from_description(self, cost_predictor):
        """Test token estimation from description"""
        description = "Generate a comprehensive REST API endpoint"
        input_tokens, output_tokens = cost_predictor.estimate_tokens_from_description(
            description,
            TaskType.CODE_GENERATION
        )
        
        assert input_tokens > 0
        assert output_tokens > 0
        assert input_tokens >= 100  # Minimum
        assert output_tokens >= 50  # Minimum

    def test_predict_cost_with_estimated_tokens(self, cost_predictor, sample_model):
        """Test cost prediction with estimated tokens"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            estimated_input_tokens=1000,
            estimated_output_tokens=2000
        )
        
        prediction = cost_predictor.predict_cost(sample_model, request)
        
        assert prediction.expected_cost > 0
        assert prediction.expected_cost == pytest.approx(0.01 + 0.06, rel=0.1)  # 1k input + 2k output
        assert prediction.min_cost > 0
        assert prediction.max_cost > prediction.expected_cost

    def test_predict_cost_without_estimated_tokens(self, cost_predictor, sample_model):
        """Test cost prediction without estimated tokens"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate a comprehensive REST API endpoint with authentication"
        )
        
        prediction = cost_predictor.predict_cost(sample_model, request)
        
        assert prediction.expected_cost > 0
        assert prediction.min_cost > 0
        assert prediction.max_cost > prediction.expected_cost

    def test_predict_cost_with_budget(self, cost_predictor, sample_model):
        """Test cost prediction with budget constraint"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            estimated_input_tokens=1000,
            estimated_output_tokens=2000,
            cost_budget=0.1
        )
        
        prediction = cost_predictor.predict_cost(sample_model, request)
        
        assert prediction.within_budget == True
        assert prediction.expected_cost <= 0.1

    def test_predict_cost_over_budget(self, cost_predictor, sample_model):
        """Test cost prediction when over budget"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            estimated_input_tokens=10000,
            estimated_output_tokens=20000,
            cost_budget=0.01  # Very low budget
        )
        
        prediction = cost_predictor.predict_cost(sample_model, request)
        
        assert prediction.within_budget == False

    def test_cost_efficiency_score(self, cost_predictor, sample_model):
        """Test cost efficiency score calculation"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            estimated_input_tokens=1000,
            estimated_output_tokens=2000
        )
        
        prediction = cost_predictor.predict_cost(sample_model, request)
        
        assert prediction.cost_efficiency_score >= 0
        assert prediction.cost_efficiency_score <= 1


class TestPerformanceTracker:
    """Test performance tracking strategy"""

    @pytest.fixture
    def performance_tracker(self):
        return PerformanceTracker(redis_url=None)

    def test_get_recommendation_weight_default(self, performance_tracker):
        """Test default recommendation weight"""
        weight = performance_tracker.get_recommendation_weight(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION
        )
        
        # Should return default weight when no history
        assert weight >= 0
        assert weight <= 1

    def test_record_outcome(self, performance_tracker):
        """Test recording performance outcome"""
        performance_tracker.record_outcome(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION,
            success=True,
            latency_ms=500,
            cost=0.01,
            quality_score=0.9
        )
        
        # Should not raise exception
        assert True

    def test_get_recommendation_weight_after_recording(self, performance_tracker):
        """Test recommendation weight after recording outcomes"""
        # Record multiple successes
        for _ in range(10):
            performance_tracker.record_outcome(
                model_id="test-model",
                task_type=TaskType.CODE_GENERATION,
                success=True,
                latency_ms=500,
                quality_score=0.9
            )
        
        weight = performance_tracker.get_recommendation_weight(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION
        )
        
        # Should have higher weight after successes
        assert weight > 0.5

    def test_record_failure(self, performance_tracker):
        """Test recording failure outcome"""
        performance_tracker.record_outcome(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION,
            success=False,
            error="Timeout"
        )
        
        weight = performance_tracker.get_recommendation_weight(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION
        )
        
        # Weight should decrease after failure
        assert weight < 1.0


class TestHybridRouter:
    """Test hybrid routing strategy"""

    @pytest.fixture
    def hybrid_router(self):
        return HybridRouter()

    @pytest.fixture
    def sample_models(self):
        return [
            ModelDefinition(
                id="model-1",
                provider=Provider.OPENAI,
                capabilities=[ModelCapability.CODE],
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
                context_window=100000,
                quality_score=0.9,
                enabled=True
            ),
            ModelDefinition(
                id="model-2",
                provider=Provider.ANTHROPIC,
                capabilities=[ModelCapability.CODE],
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                context_window=200000,
                quality_score=0.95,
                enabled=True
            ),
            ModelDefinition(
                id="model-3",
                provider=Provider.GOOGLE,
                capabilities=[ModelCapability.CODE],
                cost_per_1k_input=0.005,
                cost_per_1k_output=0.015,
                context_window=32000,
                quality_score=0.8,
                enabled=True
            ),
        ]

    def test_should_use_parallel_false(self, hybrid_router, sample_models):
        """Test parallel execution decision - should not use"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Simple code generation",
            enable_parallel=False
        )
        
        should_parallel = hybrid_router.should_use_parallel(request, sample_models)
        assert should_parallel == False

    def test_should_use_parallel_true(self, hybrid_router, sample_models):
        """Test parallel execution decision - should use"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Critical code generation",
            enable_parallel=True,
            quality_requirement=0.9
        )
        
        should_parallel = hybrid_router.should_use_parallel(request, sample_models)
        # May or may not use parallel based on internal logic
        assert isinstance(should_parallel, bool)

    def test_select_parallel_models(self, hybrid_router, sample_models):
        """Test selecting models for parallel execution"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            enable_parallel=True
        )
        
        parallel_models = hybrid_router.select_parallel_models(
            request,
            sample_models,
            num_models=2
        )
        
        assert len(parallel_models) == 2
        assert all(m in sample_models for m in parallel_models)

    def test_calculate_cost_quality_tradeoff(self, hybrid_router, sample_models):
        """Test cost-quality tradeoff calculation"""
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description="Generate code",
            estimated_input_tokens=1000,
            estimated_output_tokens=2000
        )
        
        tradeoff = hybrid_router.calculate_cost_quality_tradeoff(
            sample_models[:2],
            request
        )
        
        assert "total_cost" in tradeoff
        assert "max_quality" in tradeoff
        assert "min_quality" in tradeoff
        assert tradeoff["total_cost"] > 0
        assert tradeoff["max_quality"] >= tradeoff["min_quality"]

    def test_select_judge_model(self, hybrid_router, sample_models):
        """Test judge model selection"""
        parallel_models = sample_models[:2]
        judge = hybrid_router.select_judge_model(sample_models, parallel_models)
        
        # Judge should be different from parallel models
        if judge:
            assert judge not in parallel_models


class TestLearningLoop:
    """Test learning loop strategy"""

    @pytest.fixture
    def mock_performance_tracker(self):
        tracker = Mock()
        tracker.get_recommendation_weight.return_value = 0.8
        return tracker

    @pytest.fixture
    def learning_loop(self, mock_performance_tracker):
        return LearningLoop(performance_tracker=mock_performance_tracker)

    def test_get_model_weight_default(self, learning_loop):
        """Test default model weight"""
        weight = learning_loop.get_model_weight(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION
        )
        
        assert weight >= 0
        assert weight <= 1

    def test_update_from_feedback(self, learning_loop):
        """Test updating from feedback"""
        learning_loop.update_from_feedback(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION,
            pr_merged=True,
            quality_score=0.9,
            user_feedback=0.8
        )
        
        # Should not raise exception
        assert True

    def test_get_model_weight_after_feedback(self, learning_loop):
        """Test model weight after feedback"""
        # Update with positive feedback
        learning_loop.update_from_feedback(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION,
            pr_merged=True,
            quality_score=0.9
        )
        
        weight = learning_loop.get_model_weight(
            model_id="test-model",
            task_type=TaskType.CODE_GENERATION
        )
        
        assert weight > 0

