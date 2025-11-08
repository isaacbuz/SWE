"""
Main MoE Router Class

Orchestrates intelligent model selection using cost prediction, performance tracking,
hybrid routing, and learning loops.
"""
import logging
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .models import (
    ModelDefinition,
    RoutingRequest,
    RoutingDecision,
    Evidence,
    TaskType,
    Provider,
    CircuitBreakerState,
    ModelCapability
)
from .strategies.cost_predictor import CostPredictor
from .strategies.performance_tracker import PerformanceTracker
from .strategies.hybrid_router import HybridRouter, ConsensusStrategy
from .strategies.learning_loop import LearningLoop


class MoERouter:
    """
    Mixture-of-Experts Router for intelligent model selection

    Features:
    - Multi-factor routing (cost, quality, latency, capabilities)
    - Performance-based learning
    - Circuit breaker for failed providers
    - Hybrid/parallel execution
    - A/B testing framework
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        redis_url: Optional[str] = None,
        enable_learning: bool = True,
        enable_circuit_breaker: bool = True
    ):
        """
        Initialize MoE Router

        Args:
            config_path: Path to models.yaml config file
            redis_url: Redis connection URL for performance tracking
            enable_learning: Enable learning loop
            enable_circuit_breaker: Enable circuit breaker for failed providers
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Load model registry
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "models.yaml"

        self.models = self._load_model_registry(config_path)
        self.task_preferences = self._load_task_preferences(config_path)

        # Initialize strategies
        self.cost_predictor = CostPredictor()
        self.performance_tracker = PerformanceTracker(redis_url=redis_url)
        self.hybrid_router = HybridRouter()

        self.learning_loop = None
        if enable_learning:
            self.learning_loop = LearningLoop(performance_tracker=self.performance_tracker)

        # Circuit breaker state
        self.enable_circuit_breaker = enable_circuit_breaker
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}

        # Request tracking
        self.request_history: List[RoutingDecision] = []

        self.logger.info(
            f"MoE Router initialized with {len(self.models)} models, "
            f"learning={'enabled' if enable_learning else 'disabled'}, "
            f"circuit_breaker={'enabled' if enable_circuit_breaker else 'disabled'}"
        )

    def _load_model_registry(self, config_path: Path) -> List[ModelDefinition]:
        """Load model definitions from YAML config"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            models = []
            for model_data in config.get('models', []):
                try:
                    model = ModelDefinition(**model_data)
                    models.append(model)
                except Exception as e:
                    self.logger.error(f"Error loading model {model_data.get('id')}: {e}")

            self.logger.info(f"Loaded {len(models)} models from {config_path}")
            return models

        except Exception as e:
            self.logger.error(f"Error loading model registry: {e}")
            return []

    def _load_task_preferences(self, config_path: Path) -> Dict[TaskType, Dict]:
        """Load task preferences from YAML config"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            preferences = {}
            for task_str, prefs in config.get('task_preferences', {}).items():
                try:
                    task_type = TaskType(task_str)
                    preferences[task_type] = prefs
                except ValueError:
                    self.logger.warning(f"Unknown task type in preferences: {task_str}")

            return preferences

        except Exception as e:
            self.logger.error(f"Error loading task preferences: {e}")
            return {}

    def select_model(self, request: RoutingRequest) -> RoutingDecision:
        """
        Select optimal model for a routing request

        Args:
            request: Routing request with requirements

        Returns:
            Routing decision with selected model and rationale
        """
        self.logger.info(
            f"Selecting model for {request.task_type} "
            f"(quality>={request.quality_requirement}, "
            f"budget=${request.cost_budget})"
        )

        evidence_list = []

        # Step 1: Filter available models
        available_models = self._filter_available_models(request, evidence_list)

        if not available_models:
            return self._create_error_decision("No models available matching requirements")

        # Step 2: Check for parallel execution
        if self.hybrid_router.should_use_parallel(request, available_models):
            return self._create_parallel_decision(request, available_models, evidence_list)

        # Step 3: Score and rank models
        scored_models = self._score_models(request, available_models, evidence_list)

        if not scored_models:
            return self._create_error_decision("No models passed scoring")

        # Step 4: Select top model
        selected_model, final_score = scored_models[0]

        # Step 5: Prepare fallbacks
        fallback_models = [m.id for m, _ in scored_models[1:4]]  # Top 3 fallbacks

        # Step 6: Calculate cost prediction
        cost_prediction = self.cost_predictor.predict_cost(selected_model, request)

        # Step 7: Build rationale
        rationale = self._build_rationale(
            selected_model,
            request,
            final_score,
            cost_prediction,
            evidence_list
        )

        decision = RoutingDecision(
            selected_model=selected_model.id,
            rationale=rationale,
            confidence=min(1.0, final_score / 100),  # Normalize score to confidence
            evidence_ids=[e.id for e in evidence_list],
            evidence=evidence_list,
            estimated_cost=cost_prediction.expected_cost,
            estimated_quality=selected_model.quality_score,
            fallback_models=fallback_models,
            routing_strategy="standard",
            metadata={
                "final_score": final_score,
                "cost_efficiency": cost_prediction.cost_efficiency_score,
                "num_candidates": len(available_models)
            }
        )

        # Track decision
        self.request_history.append(decision)

        self.logger.info(
            f"Selected {selected_model.id} with confidence {decision.confidence:.2f}"
        )

        return decision

    def _filter_available_models(
        self,
        request: RoutingRequest,
        evidence_list: List[Evidence]
    ) -> List[ModelDefinition]:
        """Filter models by availability and requirements"""
        available = []

        for model in self.models:
            # Check if enabled
            if not model.enabled:
                continue

            # Check circuit breaker
            if self.enable_circuit_breaker:
                if self._is_circuit_open(model.provider.value):
                    evidence_list.append(Evidence(
                        id=f"circuit_breaker_{model.id}",
                        source="circuit_breaker",
                        description=f"Circuit breaker open for {model.provider}",
                        weight=0.0
                    ))
                    continue

            # Check quality requirement
            if model.quality_score < request.quality_requirement:
                continue

            # Check context window
            if request.context_size and model.context_window < request.context_size:
                continue

            # Check capability requirements
            if request.requires_streaming and not model.supports_streaming:
                continue

            if request.requires_tools:
                if ModelCapability.FUNCTION_CALLING not in model.capabilities:
                    continue

            if request.requires_vision:
                if ModelCapability.VISION not in model.capabilities:
                    continue

            if request.requires_json_mode:
                if ModelCapability.JSON_MODE not in model.capabilities:
                    continue

            # Check latency requirement
            if request.latency_requirement_ms:
                if model.latency_p95_ms and model.latency_p95_ms > request.latency_requirement_ms:
                    continue

            available.append(model)

        evidence_list.append(Evidence(
            id="filter_available",
            source="router",
            description=f"Filtered to {len(available)} models matching requirements",
            weight=1.0
        ))

        return available

    def _score_models(
        self,
        request: RoutingRequest,
        models: List[ModelDefinition],
        evidence_list: List[Evidence]
    ) -> List[tuple[ModelDefinition, float]]:
        """Score and rank models"""
        scored = []

        for model in models:
            score = 0.0
            factors = []

            # Factor 1: Quality score (0-50 points)
            quality_points = model.quality_score * 50
            score += quality_points
            factors.append(f"quality={quality_points:.1f}")

            # Factor 2: Cost efficiency (0-20 points)
            cost_pred = self.cost_predictor.predict_cost(model, request)
            if not cost_pred.within_budget:
                continue  # Skip models over budget

            cost_points = cost_pred.cost_efficiency_score * 20
            score += cost_points
            factors.append(f"cost={cost_points:.1f}")

            # Factor 3: Performance history (0-15 points)
            perf_weight = self.performance_tracker.get_recommendation_weight(
                model.id,
                request.task_type
            )
            perf_points = perf_weight * 15
            score += perf_points
            factors.append(f"perf={perf_points:.1f}")

            # Factor 4: Learning loop weight (0-10 points)
            if self.learning_loop:
                learned_weight = self.learning_loop.get_model_weight(
                    model.id,
                    request.task_type
                )
                learned_points = learned_weight * 10
                score += learned_points
                factors.append(f"learned={learned_points:.1f}")

            # Factor 5: Task preference bonus (0-5 points)
            if request.task_type in self.task_preferences:
                prefs = self.task_preferences[request.task_type]
                if model.id in prefs.get('preferred', []):
                    score += 5
                    factors.append("preferred=5.0")

            # Factor 6: Vendor diversity bonus (0-3 points)
            if request.vendor_diversity:
                # Bonus if different from recently used provider
                recent_providers = [
                    self._get_model_by_id(d.selected_model).provider
                    for d in self.request_history[-5:]
                    if self._get_model_by_id(d.selected_model)
                ]
                if model.provider not in recent_providers:
                    score += 3
                    factors.append("diversity=3.0")

            # Factor 7: Vendor preference bonus (0-2 points)
            if request.vendor_preference and model.provider == request.vendor_preference:
                score += 2
                factors.append("vendor_pref=2.0")

            scored.append((model, score))

            evidence_list.append(Evidence(
                id=f"score_{model.id}",
                source="scoring",
                description=f"{model.id} score: {score:.1f} ({', '.join(factors)})",
                weight=min(1.0, score / 100)
            ))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored

    def _create_parallel_decision(
        self,
        request: RoutingRequest,
        available_models: List[ModelDefinition],
        evidence_list: List[Evidence]
    ) -> RoutingDecision:
        """Create decision for parallel execution"""
        parallel_models = self.hybrid_router.select_parallel_models(
            request,
            available_models,
            num_models=3
        )

        # Calculate cost/quality tradeoff
        tradeoff = self.hybrid_router.calculate_cost_quality_tradeoff(
            parallel_models,
            request
        )

        evidence_list.append(Evidence(
            id="parallel_selected",
            source="hybrid_router",
            description=(
                f"Selected {len(parallel_models)} models for parallel execution: "
                f"{[m.id for m in parallel_models]}"
            ),
            weight=0.9
        ))

        # Select judge model
        judge = self.hybrid_router.select_judge_model(available_models, parallel_models)
        if judge:
            evidence_list.append(Evidence(
                id="judge_selected",
                source="hybrid_router",
                description=f"Judge model: {judge.id}",
                weight=0.95
            ))

        rationale = (
            f"Parallel execution with {len(parallel_models)} models "
            f"({', '.join([m.id for m in parallel_models])}) "
            f"to maximize quality (expected: {tradeoff['max_quality']:.2f}) "
            f"at estimated cost ${tradeoff['total_cost']:.6f}. "
        )

        if judge:
            rationale += f"Judge model {judge.id} will select best output."

        return RoutingDecision(
            selected_model=parallel_models[0].id,  # Primary model
            rationale=rationale,
            confidence=0.95,
            evidence_ids=[e.id for e in evidence_list],
            evidence=evidence_list,
            estimated_cost=tradeoff['total_cost'],
            estimated_quality=tradeoff['max_quality'],
            fallback_models=[m.id for m in parallel_models[1:]],
            parallel_models=[m.id for m in parallel_models],
            routing_strategy="parallel",
            metadata={
                "judge_model": judge.id if judge else None,
                "tradeoff_analysis": tradeoff
            }
        )

    def _build_rationale(
        self,
        model: ModelDefinition,
        request: RoutingRequest,
        score: float,
        cost_prediction,
        evidence_list: List[Evidence]
    ) -> str:
        """Build human-readable rationale"""
        reasons = []

        # Quality
        reasons.append(
            f"quality score {model.quality_score:.2f}"
        )

        # Cost
        reasons.append(
            f"estimated cost ${cost_prediction.expected_cost:.6f}"
        )

        # Capabilities
        if request.requires_tools:
            reasons.append("supports function calling")
        if request.requires_vision:
            reasons.append("supports vision")

        # Performance history
        perf_weight = self.performance_tracker.get_recommendation_weight(
            model.id,
            request.task_type
        )
        if perf_weight > 0.7:
            reasons.append(f"strong historical performance (weight: {perf_weight:.2f})")

        # Task preference
        if request.task_type in self.task_preferences:
            prefs = self.task_preferences[request.task_type]
            if model.id in prefs.get('preferred', []):
                reasons.append(f"preferred for {request.task_type.value}")

        rationale = (
            f"Selected {model.id} for {request.task_type.value} based on: "
            f"{', '.join(reasons)}. "
            f"Overall score: {score:.1f}/100."
        )

        return rationale

    def _create_error_decision(self, error_message: str) -> RoutingDecision:
        """Create error decision when no models available"""
        return RoutingDecision(
            selected_model="none",
            rationale=f"Error: {error_message}",
            confidence=0.0,
            evidence_ids=[],
            evidence=[],
            estimated_cost=0.0,
            estimated_quality=0.0,
            fallback_models=[],
            routing_strategy="error"
        )

    def _get_model_by_id(self, model_id: str) -> Optional[ModelDefinition]:
        """Get model definition by ID"""
        for model in self.models:
            if model.id == model_id:
                return model
        return None

    # Circuit Breaker Methods

    def _is_circuit_open(self, identifier: str) -> bool:
        """Check if circuit breaker is open for provider/model"""
        if identifier not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[identifier]

        if breaker.state == "closed":
            return False

        if breaker.state == "open":
            # Check if retry timeout has elapsed
            if breaker.next_retry_at and datetime.utcnow() >= breaker.next_retry_at:
                # Move to half-open state
                breaker.state = "half_open"
                self.logger.info(f"Circuit breaker for {identifier} moved to half-open")
                return False
            return True

        # half_open state - allow some requests through
        return False

    def record_request_outcome(
        self,
        model_id: str,
        success: bool,
        latency_ms: Optional[int] = None,
        cost: Optional[float] = None,
        quality_score: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Record request outcome for circuit breaker and performance tracking

        Args:
            model_id: Model identifier
            success: Whether request succeeded
            latency_ms: Request latency in milliseconds
            cost: Actual cost
            quality_score: Quality score
            error: Error message if failed
        """
        model = self._get_model_by_id(model_id)
        if not model:
            return

        provider = model.provider.value

        # Update circuit breaker
        if self.enable_circuit_breaker:
            self._update_circuit_breaker(provider, success)

        # Record in performance tracker
        # Note: task_type should be passed but not available here
        # Would need to track request context
        # For now, skip performance tracking in this method

        self.logger.debug(
            f"Recorded {'success' if success else 'failure'} for {model_id}"
        )

    def _update_circuit_breaker(self, identifier: str, success: bool):
        """Update circuit breaker state"""
        if identifier not in self.circuit_breakers:
            self.circuit_breakers[identifier] = CircuitBreakerState(
                identifier=identifier
            )

        breaker = self.circuit_breakers[identifier]

        if success:
            breaker.failure_count = 0
            breaker.last_success = datetime.utcnow()

            if breaker.state == "half_open":
                breaker.state = "closed"
                self.logger.info(f"Circuit breaker for {identifier} closed")

        else:
            breaker.failure_count += 1
            breaker.last_failure = datetime.utcnow()

            if breaker.failure_count >= breaker.failure_threshold:
                if breaker.state != "open":
                    breaker.state = "open"
                    breaker.next_retry_at = (
                        datetime.utcnow() +
                        timedelta(seconds=breaker.retry_timeout_seconds)
                    )
                    self.logger.warning(
                        f"Circuit breaker opened for {identifier} "
                        f"after {breaker.failure_count} failures"
                    )

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return {
            identifier: {
                "state": breaker.state,
                "failure_count": breaker.failure_count,
                "last_failure": breaker.last_failure.isoformat() if breaker.last_failure else None,
                "last_success": breaker.last_success.isoformat() if breaker.last_success else None,
                "next_retry": breaker.next_retry_at.isoformat() if breaker.next_retry_at else None
            }
            for identifier, breaker in self.circuit_breakers.items()
        }

    def reset_circuit_breaker(self, identifier: str):
        """Manually reset a circuit breaker"""
        if identifier in self.circuit_breakers:
            self.circuit_breakers[identifier].state = "closed"
            self.circuit_breakers[identifier].failure_count = 0
            self.logger.info(f"Manually reset circuit breaker for {identifier}")

    # Analytics and Reporting

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        if not self.request_history:
            return {"message": "No routing history"}

        model_counts = defaultdict(int)
        strategy_counts = defaultdict(int)
        total_cost = 0.0
        avg_confidence = 0.0

        for decision in self.request_history:
            model_counts[decision.selected_model] += 1
            strategy_counts[decision.routing_strategy] += 1
            total_cost += decision.estimated_cost
            avg_confidence += decision.confidence

        return {
            "total_requests": len(self.request_history),
            "unique_models_used": len(model_counts),
            "model_distribution": dict(model_counts),
            "strategy_distribution": dict(strategy_counts),
            "total_estimated_cost": round(total_cost, 4),
            "avg_estimated_cost": round(total_cost / len(self.request_history), 6),
            "avg_confidence": round(avg_confidence / len(self.request_history), 4)
        }
