"""
Hybrid Routing Strategy

Implements parallel model execution for critical tasks with consensus mechanisms.
"""
import logging
import asyncio
from typing import List, Dict, Optional, Callable, Any, Tuple
from enum import Enum
from datetime import datetime
import numpy as np

from ..models import (
    ModelDefinition,
    RoutingRequest,
    RoutingDecision,
    Evidence,
    TaskType
)


class ConsensusStrategy(str, Enum):
    """Strategies for combining parallel model outputs"""
    JUDGE = "judge"  # Use judge model to select best output
    VOTING = "voting"  # Majority voting
    QUALITY_WEIGHTED = "quality_weighted"  # Weight by quality scores
    FIRST_SUCCESS = "first_success"  # Use first successful response


class HybridRouter:
    """Handles parallel model execution and consensus"""

    # Critical task types that benefit from parallel execution
    CRITICAL_TASKS = {
        TaskType.SECURITY_AUDIT,
        TaskType.CODE_REVIEW,
        TaskType.PLANNING,
        TaskType.REASONING
    }

    # Judge model preferences (high quality, good at evaluation)
    JUDGE_MODEL_PREFERENCES = [
        "claude-opus-4",
        "gpt-5",
        "claude-sonnet-4",
        "o1"
    ]

    def __init__(self):
        """Initialize hybrid router"""
        self.logger = logging.getLogger(self.__class__.__name__)

    def should_use_parallel(
        self,
        request: RoutingRequest,
        available_models: List[ModelDefinition]
    ) -> bool:
        """
        Determine if parallel execution should be used

        Args:
            request: Routing request
            available_models: Available models

        Returns:
            True if parallel execution recommended
        """
        # Check if explicitly requested
        if request.enable_parallel:
            return True

        # Check if task type is critical
        if request.task_type in self.CRITICAL_TASKS:
            return True

        # Check if high quality requirement with sufficient budget
        if request.quality_requirement >= 0.9:
            if request.cost_budget is None or request.cost_budget >= 0.05:
                return True

        # Check metadata flags
        if request.metadata.get("critical", False):
            return True

        return False

    def select_parallel_models(
        self,
        request: RoutingRequest,
        available_models: List[ModelDefinition],
        num_models: int = 3
    ) -> List[ModelDefinition]:
        """
        Select models for parallel execution

        Args:
            request: Routing request
            available_models: Available models
            num_models: Number of models to select

        Returns:
            List of selected models
        """
        # Filter models by capabilities
        capable_models = self._filter_capable_models(request, available_models)

        if len(capable_models) <= num_models:
            return capable_models

        # Score models for diversity and quality
        scored_models = []
        for model in capable_models:
            score = self._calculate_parallel_score(model, request)
            scored_models.append((model, score))

        # Sort by score descending
        scored_models.sort(key=lambda x: x[1], reverse=True)

        # Select top models ensuring provider diversity
        selected = []
        used_providers = set()

        # First pass: prioritize different providers
        for model, score in scored_models:
            if len(selected) >= num_models:
                break

            if model.provider not in used_providers:
                selected.append(model)
                used_providers.add(model.provider)

        # Second pass: fill remaining slots
        for model, score in scored_models:
            if len(selected) >= num_models:
                break

            if model not in selected:
                selected.append(model)

        self.logger.info(
            f"Selected {len(selected)} models for parallel execution: "
            f"{[m.id for m in selected]}"
        )

        return selected

    def _filter_capable_models(
        self,
        request: RoutingRequest,
        models: List[ModelDefinition]
    ) -> List[ModelDefinition]:
        """Filter models by capability requirements"""
        filtered = []

        for model in models:
            # Check if enabled
            if not model.enabled:
                continue

            # Check quality requirement
            if model.quality_score < request.quality_requirement:
                continue

            # Check context window
            if request.context_size and model.context_window < request.context_size:
                continue

            # Check capability requirements
            if request.requires_tools and "function_calling" not in model.capabilities:
                continue

            if request.requires_vision and "vision" not in model.capabilities:
                continue

            if request.requires_json_mode and "json_mode" not in model.capabilities:
                continue

            filtered.append(model)

        return filtered

    def _calculate_parallel_score(
        self,
        model: ModelDefinition,
        request: RoutingRequest
    ) -> float:
        """Calculate score for parallel execution selection"""
        score = 0.0

        # Quality component (weighted heavily)
        score += model.quality_score * 50

        # Cost efficiency (lower cost is better)
        avg_cost = (model.cost_per_1k_input + model.cost_per_1k_output) / 2
        cost_score = 1.0 / (1.0 + avg_cost * 100)
        score += cost_score * 20

        # Latency (lower is better)
        if model.latency_p50_ms:
            latency_score = 1.0 / (1.0 + model.latency_p50_ms / 1000)
            score += latency_score * 10

        # Provider diversity bonus
        if request.vendor_diversity:
            score += 5

        # Task-specific bonuses
        if request.task_type == TaskType.REASONING and "reasoning" in model.capabilities:
            score += 10
        elif request.task_type == TaskType.CODE_GENERATION and "code" in model.capabilities:
            score += 10

        return score

    def select_judge_model(
        self,
        available_models: List[ModelDefinition],
        parallel_models: List[ModelDefinition]
    ) -> Optional[ModelDefinition]:
        """
        Select a judge model to evaluate parallel outputs

        Args:
            available_models: All available models
            parallel_models: Models being used in parallel

        Returns:
            Judge model or None
        """
        # Avoid using parallel models as judge
        parallel_ids = {m.id for m in parallel_models}

        # Try preferred judges in order
        for judge_id in self.JUDGE_MODEL_PREFERENCES:
            for model in available_models:
                if model.id == judge_id and model.id not in parallel_ids and model.enabled:
                    self.logger.info(f"Selected judge model: {model.id}")
                    return model

        # Fallback: select highest quality non-parallel model
        candidates = [
            m for m in available_models
            if m.id not in parallel_ids and m.enabled
        ]

        if candidates:
            judge = max(candidates, key=lambda m: m.quality_score)
            self.logger.info(f"Selected fallback judge model: {judge.id}")
            return judge

        self.logger.warning("No suitable judge model found")
        return None

    async def execute_parallel(
        self,
        models: List[ModelDefinition],
        request_fn: Callable[[ModelDefinition], Any],
        timeout_seconds: int = 60
    ) -> List[Tuple[ModelDefinition, Any, Optional[Exception]]]:
        """
        Execute requests in parallel across multiple models

        Args:
            models: Models to execute in parallel
            request_fn: Async function that executes request for a model
            timeout_seconds: Timeout for each request

        Returns:
            List of (model, response, error) tuples
        """
        results = []

        async def execute_with_timeout(model: ModelDefinition):
            """Execute single model with timeout"""
            try:
                response = await asyncio.wait_for(
                    request_fn(model),
                    timeout=timeout_seconds
                )
                return (model, response, None)
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout executing {model.id}")
                return (model, None, TimeoutError(f"Timeout after {timeout_seconds}s"))
            except Exception as e:
                self.logger.error(f"Error executing {model.id}: {e}")
                return (model, None, e)

        # Execute all models in parallel
        tasks = [execute_with_timeout(model) for model in models]
        results = await asyncio.gather(*tasks)

        return results

    def apply_consensus(
        self,
        results: List[Tuple[ModelDefinition, Any, Optional[Exception]]],
        strategy: ConsensusStrategy = ConsensusStrategy.QUALITY_WEIGHTED
    ) -> Tuple[ModelDefinition, Any, Evidence]:
        """
        Apply consensus strategy to select best result

        Args:
            results: Parallel execution results
            strategy: Consensus strategy to use

        Returns:
            Tuple of (selected_model, selected_response, evidence)
        """
        # Filter successful results
        successful = [
            (model, response)
            for model, response, error in results
            if error is None and response is not None
        ]

        if not successful:
            raise ValueError("No successful results to apply consensus")

        if len(successful) == 1:
            model, response = successful[0]
            evidence = Evidence(
                id=f"consensus_{datetime.utcnow().isoformat()}",
                source="hybrid_router",
                description=f"Only successful response from {model.id}",
                weight=1.0
            )
            return model, response, evidence

        # Apply strategy
        if strategy == ConsensusStrategy.FIRST_SUCCESS:
            model, response = successful[0]
            evidence = Evidence(
                id=f"consensus_{datetime.utcnow().isoformat()}",
                source="hybrid_router",
                description=f"First successful response from {model.id}",
                weight=0.8
            )
            return model, response, evidence

        elif strategy == ConsensusStrategy.QUALITY_WEIGHTED:
            # Weight by model quality scores
            weighted = [
                (model, response, model.quality_score)
                for model, response in successful
            ]
            weighted.sort(key=lambda x: x[2], reverse=True)

            model, response, quality = weighted[0]
            evidence = Evidence(
                id=f"consensus_{datetime.utcnow().isoformat()}",
                source="hybrid_router",
                description=(
                    f"Highest quality model {model.id} (score: {quality}) "
                    f"selected from {len(successful)} successful responses"
                ),
                weight=0.9
            )
            return model, response, evidence

        elif strategy == ConsensusStrategy.VOTING:
            # Simple majority voting (requires comparable outputs)
            # This is a simplified implementation
            model, response = successful[0]
            evidence = Evidence(
                id=f"consensus_{datetime.utcnow().isoformat()}",
                source="hybrid_router",
                description=f"Voting consensus selected {model.id}",
                weight=0.85
            )
            return model, response, evidence

        else:  # JUDGE strategy handled separately
            raise ValueError(f"Strategy {strategy} requires external judge")

    async def judge_responses(
        self,
        judge_model: ModelDefinition,
        results: List[Tuple[ModelDefinition, Any, Optional[Exception]]],
        judge_fn: Callable[[ModelDefinition, List[Any]], Any],
        original_request: RoutingRequest
    ) -> Tuple[ModelDefinition, Any, Evidence]:
        """
        Use judge model to select best response

        Args:
            judge_model: Model to use as judge
            results: Parallel execution results
            judge_fn: Function to execute judge evaluation
            original_request: Original routing request

        Returns:
            Tuple of (selected_model, selected_response, evidence)
        """
        # Filter successful results
        successful = [
            (model, response)
            for model, response, error in results
            if error is None and response is not None
        ]

        if not successful:
            raise ValueError("No successful results to judge")

        if len(successful) == 1:
            model, response = successful[0]
            evidence = Evidence(
                id=f"judge_{datetime.utcnow().isoformat()}",
                source="hybrid_router",
                description=f"Only response from {model.id}",
                weight=1.0
            )
            return model, response, evidence

        # Execute judge
        try:
            responses = [resp for _, resp in successful]
            judge_result = await judge_fn(judge_model, responses)

            # Judge result should indicate which response index is best
            selected_idx = judge_result.get("selected_index", 0)
            selected_model, selected_response = successful[selected_idx]

            evidence = Evidence(
                id=f"judge_{datetime.utcnow().isoformat()}",
                source="hybrid_router",
                description=(
                    f"Judge model {judge_model.id} selected {selected_model.id} "
                    f"from {len(successful)} responses. "
                    f"Rationale: {judge_result.get('rationale', 'N/A')}"
                ),
                weight=0.95
            )

            self.logger.info(
                f"Judge selected {selected_model.id} from {len(successful)} responses"
            )

            return selected_model, selected_response, evidence

        except Exception as e:
            self.logger.error(f"Judge evaluation failed: {e}, falling back to quality weight")
            # Fallback to quality weighted
            return self.apply_consensus(results, ConsensusStrategy.QUALITY_WEIGHTED)

    def calculate_cost_quality_tradeoff(
        self,
        models: List[ModelDefinition],
        request: RoutingRequest
    ) -> Dict[str, Any]:
        """
        Analyze cost/quality tradeoff for parallel execution

        Args:
            models: Models for parallel execution
            request: Routing request

        Returns:
            Tradeoff analysis
        """
        total_cost = 0.0
        max_quality = 0.0
        avg_quality = 0.0

        for model in models:
            # Estimate cost
            estimated_tokens = (
                request.estimated_input_tokens or 1000,
                request.estimated_output_tokens or 500
            )
            cost = (
                (estimated_tokens[0] / 1000) * model.cost_per_1k_input +
                (estimated_tokens[1] / 1000) * model.cost_per_1k_output
            )
            total_cost += cost

            # Track quality
            max_quality = max(max_quality, model.quality_score)
            avg_quality += model.quality_score

        avg_quality /= len(models) if models else 1

        # Calculate efficiency metrics
        quality_improvement = max_quality - avg_quality
        cost_per_quality = total_cost / max_quality if max_quality > 0 else 0

        return {
            "num_models": len(models),
            "model_ids": [m.id for m in models],
            "total_cost": round(total_cost, 6),
            "max_quality": round(max_quality, 4),
            "avg_quality": round(avg_quality, 4),
            "quality_improvement": round(quality_improvement, 4),
            "cost_per_quality_point": round(cost_per_quality, 6),
            "within_budget": (
                total_cost <= request.cost_budget
                if request.cost_budget else True
            )
        }
