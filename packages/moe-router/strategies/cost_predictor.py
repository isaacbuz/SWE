"""
Cost Prediction Strategy

Estimates costs for different models and validates against budget constraints.
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from ..models import (
    ModelDefinition,
    RoutingRequest,
    CostPrediction,
    TaskType
)

logger = logging.getLogger(__name__)


class CostPredictor:
    """Predicts and validates costs for model routing decisions"""

    # Token estimation multipliers by task type
    TASK_TOKEN_MULTIPLIERS = {
        TaskType.REASONING: {"input": 1.2, "output": 2.5},
        TaskType.CODE_GENERATION: {"input": 1.0, "output": 3.0},
        TaskType.CODE_REVIEW: {"input": 2.0, "output": 1.5},
        TaskType.PLANNING: {"input": 1.0, "output": 2.0},
        TaskType.ANALYSIS: {"input": 1.5, "output": 1.8},
        TaskType.DOCUMENTATION: {"input": 0.8, "output": 2.5},
        TaskType.TESTING: {"input": 1.0, "output": 2.0},
        TaskType.REFACTORING: {"input": 1.5, "output": 2.0},
        TaskType.SECURITY_AUDIT: {"input": 2.0, "output": 2.5},
        TaskType.TOOL_USE: {"input": 1.0, "output": 1.5},
        TaskType.MULTIMODAL: {"input": 1.5, "output": 1.2},
        TaskType.LONG_CONTEXT: {"input": 5.0, "output": 1.5},
    }

    # Base token estimation from description
    AVG_TOKENS_PER_WORD = 1.3
    AVG_TOKENS_PER_CHAR = 0.25

    def __init__(self):
        """Initialize cost predictor"""
        self.logger = logging.getLogger(self.__class__.__name__)

    def estimate_tokens_from_description(
        self,
        description: str,
        task_type: TaskType
    ) -> Tuple[int, int]:
        """
        Estimate input and output tokens from task description

        Args:
            description: Task description text
            task_type: Type of task

        Returns:
            Tuple of (estimated_input_tokens, estimated_output_tokens)
        """
        # Basic word count estimation
        word_count = len(description.split())
        base_input_tokens = int(word_count * self.AVG_TOKENS_PER_WORD)

        # Get multipliers for task type
        multipliers = self.TASK_TOKEN_MULTIPLIERS.get(
            task_type,
            {"input": 1.0, "output": 1.5}
        )

        # Apply task-specific multipliers
        estimated_input = int(base_input_tokens * multipliers["input"])

        # Estimate output based on task complexity
        base_output = 500  # Default baseline

        # Adjust based on task indicators in description
        if any(word in description.lower() for word in ["detailed", "comprehensive", "thorough"]):
            base_output = 1500
        elif any(word in description.lower() for word in ["simple", "brief", "quick"]):
            base_output = 300

        estimated_output = int(base_output * multipliers["output"])

        # Add some variance for uncertainty
        estimated_input = max(100, estimated_input)  # Minimum 100 tokens
        estimated_output = max(50, estimated_output)  # Minimum 50 tokens

        self.logger.debug(
            f"Token estimation for {task_type}: "
            f"input={estimated_input}, output={estimated_output}"
        )

        return estimated_input, estimated_output

    def predict_cost(
        self,
        model: ModelDefinition,
        request: RoutingRequest
    ) -> CostPrediction:
        """
        Predict cost for a specific model and request

        Args:
            model: Model definition
            request: Routing request

        Returns:
            Cost prediction with min/max/expected costs
        """
        # Get or estimate token counts
        if request.estimated_input_tokens:
            input_tokens = request.estimated_input_tokens
        else:
            input_tokens, _ = self.estimate_tokens_from_description(
                request.task_description,
                request.task_type
            )

        if request.estimated_output_tokens:
            output_tokens = request.estimated_output_tokens
        else:
            _, output_tokens = self.estimate_tokens_from_description(
                request.task_description,
                request.task_type
            )

        # Calculate costs (convert to per-token from per-1k)
        input_cost = (input_tokens / 1000) * model.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model.cost_per_1k_output
        expected_cost = input_cost + output_cost

        # Calculate min/max with variance
        variance = 0.3  # 30% variance
        min_cost = expected_cost * (1 - variance)
        max_cost = expected_cost * (1 + variance)

        # Check if within budget
        within_budget = True
        if request.cost_budget is not None:
            within_budget = max_cost <= request.cost_budget

        # Calculate cost efficiency score (inverse of cost, normalized)
        # Lower cost = higher efficiency
        cost_efficiency = 1.0 / (1.0 + expected_cost * 100)  # Scale for scoring

        prediction = CostPrediction(
            model_id=model.id,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            min_cost=round(min_cost, 6),
            max_cost=round(max_cost, 6),
            expected_cost=round(expected_cost, 6),
            within_budget=within_budget,
            cost_efficiency_score=round(cost_efficiency, 4)
        )

        self.logger.debug(
            f"Cost prediction for {model.id}: "
            f"${prediction.expected_cost:.6f} "
            f"(${prediction.min_cost:.6f} - ${prediction.max_cost:.6f})"
        )

        return prediction

    def predict_costs_for_models(
        self,
        models: List[ModelDefinition],
        request: RoutingRequest
    ) -> List[CostPrediction]:
        """
        Predict costs for multiple models

        Args:
            models: List of model definitions
            request: Routing request

        Returns:
            List of cost predictions
        """
        predictions = []
        for model in models:
            try:
                prediction = self.predict_cost(model, request)
                predictions.append(prediction)
            except Exception as e:
                self.logger.error(f"Error predicting cost for {model.id}: {e}")

        # Sort by expected cost
        predictions.sort(key=lambda p: p.expected_cost)
        return predictions

    def filter_by_budget(
        self,
        predictions: List[CostPrediction],
        budget: Optional[float]
    ) -> List[CostPrediction]:
        """
        Filter predictions by budget constraint

        Args:
            predictions: List of cost predictions
            budget: Budget constraint in USD

        Returns:
            Filtered list of predictions within budget
        """
        if budget is None:
            return predictions

        return [p for p in predictions if p.within_budget]

    def get_cost_projection(
        self,
        model: ModelDefinition,
        num_requests: int,
        avg_input_tokens: int = 1000,
        avg_output_tokens: int = 500
    ) -> Dict[str, float]:
        """
        Project costs for multiple requests

        Args:
            model: Model definition
            num_requests: Number of requests to project
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request

        Returns:
            Dictionary with cost projections
        """
        cost_per_request = (
            (avg_input_tokens / 1000) * model.cost_per_1k_input +
            (avg_output_tokens / 1000) * model.cost_per_1k_output
        )

        return {
            "model_id": model.id,
            "num_requests": num_requests,
            "cost_per_request": round(cost_per_request, 6),
            "total_cost": round(cost_per_request * num_requests, 2),
            "avg_input_tokens": avg_input_tokens,
            "avg_output_tokens": avg_output_tokens
        }

    def compare_model_costs(
        self,
        models: List[ModelDefinition],
        request: RoutingRequest
    ) -> Dict[str, any]:
        """
        Compare costs across models

        Args:
            models: List of models to compare
            request: Routing request

        Returns:
            Comparison analysis
        """
        predictions = self.predict_costs_for_models(models, request)

        if not predictions:
            return {"error": "No valid predictions"}

        costs = [p.expected_cost for p in predictions]

        return {
            "num_models": len(predictions),
            "cheapest_model": predictions[0].model_id,
            "cheapest_cost": predictions[0].expected_cost,
            "most_expensive_model": predictions[-1].model_id,
            "most_expensive_cost": predictions[-1].expected_cost,
            "avg_cost": round(np.mean(costs), 6),
            "median_cost": round(np.median(costs), 6),
            "cost_range": round(predictions[-1].expected_cost - predictions[0].expected_cost, 6),
            "predictions": predictions
        }

    def calculate_roi_score(
        self,
        cost: float,
        quality_score: float,
        latency_ms: Optional[int] = None
    ) -> float:
        """
        Calculate ROI score balancing cost, quality, and speed

        Args:
            cost: Estimated cost
            quality_score: Quality score (0-1)
            latency_ms: Latency in milliseconds

        Returns:
            ROI score (higher is better)
        """
        # Quality to cost ratio
        quality_per_dollar = quality_score / (cost + 0.00001)  # Avoid division by zero

        # Factor in latency if provided
        if latency_ms:
            # Penalize high latency (normalize to seconds)
            latency_penalty = 1.0 / (1.0 + (latency_ms / 10000))
            roi_score = quality_per_dollar * latency_penalty
        else:
            roi_score = quality_per_dollar

        # Normalize to 0-1 range
        return min(1.0, roi_score / 1000)
