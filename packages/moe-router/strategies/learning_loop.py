"""
Learning Loop Strategy

Implements feedback collection, A/B testing, and continuous improvement
of routing decisions based on outcomes.
"""
import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

from ..models import (
    ModelDefinition,
    TaskType,
    FeedbackData,
    PerformanceMetrics,
    RoutingDecision
)


class ABTestConfig:
    """Configuration for A/B testing"""
    def __init__(
        self,
        test_id: str,
        model_a: str,
        model_b: str,
        task_type: TaskType,
        traffic_split: float = 0.5,
        min_samples: int = 30,
        duration_days: int = 7
    ):
        self.test_id = test_id
        self.model_a = model_a
        self.model_b = model_b
        self.task_type = task_type
        self.traffic_split = traffic_split  # % to model_a
        self.min_samples = min_samples
        self.duration_days = duration_days
        self.start_time = datetime.utcnow()
        self.results_a: List[FeedbackData] = []
        self.results_b: List[FeedbackData] = []


class LearningLoop:
    """Manages feedback collection and continuous learning"""

    # Weight decay for older feedback
    FEEDBACK_DECAY_DAYS = 30

    # Minimum feedback samples for model weight updates
    MIN_FEEDBACK_SAMPLES = 10

    # Quality score weights
    OUTCOME_WEIGHTS = {
        "success": 1.0,
        "partial": 0.5,
        "failure": 0.0
    }

    # PR outcome weights
    PR_MERGED_BONUS = 0.2
    PR_REVERTED_PENALTY = -0.5

    def __init__(self, performance_tracker=None):
        """
        Initialize learning loop

        Args:
            performance_tracker: Optional PerformanceTracker instance
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.performance_tracker = performance_tracker
        self.ab_tests: Dict[str, ABTestConfig] = {}
        self.model_weights: Dict[Tuple[str, TaskType], float] = defaultdict(lambda: 0.5)

    def collect_feedback(
        self,
        feedback: FeedbackData,
        routing_decision: Optional[RoutingDecision] = None
    ):
        """
        Collect feedback from a completed request

        Args:
            feedback: Feedback data
            routing_decision: Original routing decision (optional)
        """
        self.logger.info(
            f"Collecting feedback for {feedback.model_id} on {feedback.task_type}: "
            f"{feedback.outcome}"
        )

        # Record in performance tracker if available
        if self.performance_tracker:
            self.performance_tracker.record_feedback(feedback)

        # Update A/B test if applicable
        self._update_ab_test(feedback)

        # Update model weights
        self._update_model_weights(feedback)

        # Log insights
        self._log_insights(feedback, routing_decision)

    def _update_model_weights(self, feedback: FeedbackData):
        """Update model weights based on feedback"""
        key = (feedback.model_id, feedback.task_type)

        # Calculate feedback score
        score = self._calculate_feedback_score(feedback)

        # Update weight with exponential moving average
        current_weight = self.model_weights[key]
        alpha = 0.1  # Learning rate
        new_weight = alpha * score + (1 - alpha) * current_weight

        # Clamp to [0, 1]
        new_weight = max(0.0, min(1.0, new_weight))

        self.model_weights[key] = new_weight

        self.logger.debug(
            f"Updated weight for {feedback.model_id} on {feedback.task_type}: "
            f"{current_weight:.4f} -> {new_weight:.4f}"
        )

    def _calculate_feedback_score(self, feedback: FeedbackData) -> float:
        """Calculate normalized score from feedback"""
        # Base score from outcome
        score = self.OUTCOME_WEIGHTS.get(feedback.outcome, 0.5)

        # Adjust by quality score if available
        if feedback.quality_score is not None:
            score = (score + feedback.quality_score) / 2

        # Adjust by PR outcomes
        if feedback.pr_merged:
            score += self.PR_MERGED_BONUS
        if feedback.pr_reverted:
            score += self.PR_REVERTED_PENALTY

        # Adjust by user rating if available
        if feedback.user_rating is not None:
            # Normalize rating to 0-1
            rating_score = (feedback.user_rating - 1) / 4  # 1-5 -> 0-1
            score = (score + rating_score) / 2

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))

    def get_model_weight(self, model_id: str, task_type: TaskType) -> float:
        """
        Get learned weight for model+task combination

        Args:
            model_id: Model identifier
            task_type: Task type

        Returns:
            Weight (0-1), higher means better historical performance
        """
        key = (model_id, task_type)
        return self.model_weights.get(key, 0.5)  # Default to neutral

    def _update_ab_test(self, feedback: FeedbackData):
        """Update A/B test results if feedback belongs to a test"""
        for test in self.ab_tests.values():
            if feedback.task_type != test.task_type:
                continue

            if feedback.model_id == test.model_a:
                test.results_a.append(feedback)
            elif feedback.model_id == test.model_b:
                test.results_b.append(feedback)

    def _log_insights(
        self,
        feedback: FeedbackData,
        routing_decision: Optional[RoutingDecision]
    ):
        """Log insights from feedback"""
        insights = []

        # Check for cost overruns
        if routing_decision and feedback.actual_cost:
            if feedback.actual_cost > routing_decision.estimated_cost * 1.5:
                insights.append(
                    f"Cost overrun: actual ${feedback.actual_cost:.6f} vs "
                    f"estimated ${routing_decision.estimated_cost:.6f}"
                )

        # Check for quality issues
        if feedback.quality_score and feedback.quality_score < 0.5:
            insights.append(f"Low quality score: {feedback.quality_score:.2f}")

        # Check for reverted PRs
        if feedback.pr_reverted:
            insights.append("PR was reverted - investigate failure mode")

        if insights:
            self.logger.warning(
                f"Insights for {feedback.model_id}: {'; '.join(insights)}"
            )

    # A/B Testing Methods

    def start_ab_test(
        self,
        model_a: str,
        model_b: str,
        task_type: TaskType,
        traffic_split: float = 0.5,
        min_samples: int = 30,
        duration_days: int = 7
    ) -> str:
        """
        Start an A/B test comparing two models

        Args:
            model_a: First model ID
            model_b: Second model ID
            task_type: Task type to test
            traffic_split: Fraction of traffic to model_a (0-1)
            min_samples: Minimum samples before analysis
            duration_days: Test duration in days

        Returns:
            Test ID
        """
        test_id = f"ab_{model_a}_vs_{model_b}_{task_type.value}_{datetime.utcnow().isoformat()}"

        config = ABTestConfig(
            test_id=test_id,
            model_a=model_a,
            model_b=model_b,
            task_type=task_type,
            traffic_split=traffic_split,
            min_samples=min_samples,
            duration_days=duration_days
        )

        self.ab_tests[test_id] = config

        self.logger.info(
            f"Started A/B test {test_id}: {model_a} vs {model_b} "
            f"for {task_type} (split: {traffic_split:.0%})"
        )

        return test_id

    def get_ab_test_model(
        self,
        task_type: TaskType,
        default_model: str
    ) -> str:
        """
        Get model for request based on active A/B tests

        Args:
            task_type: Task type
            default_model: Default model if no test applies

        Returns:
            Model ID to use
        """
        # Find active test for task type
        active_tests = [
            test for test in self.ab_tests.values()
            if test.task_type == task_type and self._is_test_active(test)
        ]

        if not active_tests:
            return default_model

        # Use first active test (could be extended for multiple concurrent tests)
        test = active_tests[0]

        # Random assignment based on traffic split
        if random.random() < test.traffic_split:
            return test.model_a
        else:
            return test.model_b

    def _is_test_active(self, test: ABTestConfig) -> bool:
        """Check if A/B test is still active"""
        elapsed = datetime.utcnow() - test.start_time
        return elapsed.days < test.duration_days

    def analyze_ab_test(self, test_id: str) -> Dict[str, Any]:
        """
        Analyze A/B test results

        Args:
            test_id: Test identifier

        Returns:
            Analysis results
        """
        if test_id not in self.ab_tests:
            return {"error": "Test not found"}

        test = self.ab_tests[test_id]

        # Calculate statistics for each variant
        stats_a = self._calculate_variant_stats(test.results_a)
        stats_b = self._calculate_variant_stats(test.results_b)

        # Determine winner
        winner = None
        confidence = 0.0

        if len(test.results_a) >= test.min_samples and len(test.results_b) >= test.min_samples:
            # Statistical comparison
            if stats_a["avg_score"] > stats_b["avg_score"] * 1.05:  # 5% threshold
                winner = test.model_a
                confidence = (stats_a["avg_score"] - stats_b["avg_score"]) / stats_b["avg_score"]
            elif stats_b["avg_score"] > stats_a["avg_score"] * 1.05:
                winner = test.model_b
                confidence = (stats_b["avg_score"] - stats_a["avg_score"]) / stats_a["avg_score"]

        return {
            "test_id": test_id,
            "model_a": test.model_a,
            "model_b": test.model_b,
            "task_type": test.task_type.value,
            "status": "active" if self._is_test_active(test) else "completed",
            "duration_days": (datetime.utcnow() - test.start_time).days,
            "variant_a": {
                "model": test.model_a,
                "samples": len(test.results_a),
                **stats_a
            },
            "variant_b": {
                "model": test.model_b,
                "samples": len(test.results_b),
                **stats_b
            },
            "winner": winner,
            "confidence": round(confidence, 4) if winner else None,
            "recommendation": self._get_ab_recommendation(test, stats_a, stats_b, winner)
        }

    def _calculate_variant_stats(self, results: List[FeedbackData]) -> Dict[str, float]:
        """Calculate statistics for A/B test variant"""
        if not results:
            return {
                "avg_score": 0.0,
                "success_rate": 0.0,
                "avg_cost": 0.0,
                "avg_quality": 0.0
            }

        scores = [self._calculate_feedback_score(r) for r in results]
        successes = sum(1 for r in results if r.outcome == "success")
        costs = [r.actual_cost for r in results if r.actual_cost is not None]
        qualities = [r.quality_score for r in results if r.quality_score is not None]

        return {
            "avg_score": round(np.mean(scores), 4),
            "success_rate": round(successes / len(results), 4),
            "avg_cost": round(np.mean(costs), 6) if costs else 0.0,
            "avg_quality": round(np.mean(qualities), 4) if qualities else 0.0
        }

    def _get_ab_recommendation(
        self,
        test: ABTestConfig,
        stats_a: Dict,
        stats_b: Dict,
        winner: Optional[str]
    ) -> str:
        """Generate recommendation from A/B test"""
        if not winner:
            if len(test.results_a) < test.min_samples or len(test.results_b) < test.min_samples:
                return "Insufficient data - continue test"
            else:
                return "No clear winner - results are statistically similar"

        winner_stats = stats_a if winner == test.model_a else stats_b
        loser_stats = stats_b if winner == test.model_a else stats_a

        improvement = (winner_stats["avg_score"] - loser_stats["avg_score"]) / loser_stats["avg_score"]

        return (
            f"Use {winner} - shows {improvement:.1%} improvement "
            f"(score: {winner_stats['avg_score']:.4f} vs {loser_stats['avg_score']:.4f})"
        )

    # Analytics and Reporting

    def get_model_performance_report(
        self,
        model_id: str,
        task_type: Optional[TaskType] = None
    ) -> Dict[str, Any]:
        """
        Generate performance report for a model

        Args:
            model_id: Model identifier
            task_type: Optional task type filter

        Returns:
            Performance report
        """
        if not self.performance_tracker:
            return {"error": "Performance tracker not available"}

        feedback_history = self.performance_tracker.get_feedback_history(
            model_id=model_id,
            task_type=task_type,
            limit=1000
        )

        if not feedback_history:
            return {
                "model_id": model_id,
                "task_type": task_type.value if task_type else "all",
                "message": "No feedback data available"
            }

        # Calculate aggregate metrics
        total = len(feedback_history)
        successes = sum(1 for f in feedback_history if f.outcome == "success")
        failures = sum(1 for f in feedback_history if f.outcome == "failure")
        pr_merged = sum(1 for f in feedback_history if f.pr_merged)
        pr_reverted = sum(1 for f in feedback_history if f.pr_reverted)

        costs = [f.actual_cost for f in feedback_history if f.actual_cost]
        latencies = [f.actual_latency_ms for f in feedback_history if f.actual_latency_ms]
        qualities = [f.quality_score for f in feedback_history if f.quality_score]
        ratings = [f.user_rating for f in feedback_history if f.user_rating]

        return {
            "model_id": model_id,
            "task_type": task_type.value if task_type else "all",
            "total_requests": total,
            "success_rate": round(successes / total, 4) if total > 0 else 0.0,
            "failure_rate": round(failures / total, 4) if total > 0 else 0.0,
            "pr_merge_rate": round(pr_merged / total, 4) if total > 0 else 0.0,
            "pr_revert_rate": round(pr_reverted / total, 4) if total > 0 else 0.0,
            "avg_cost": round(np.mean(costs), 6) if costs else None,
            "avg_latency_ms": round(np.mean(latencies), 2) if latencies else None,
            "avg_quality": round(np.mean(qualities), 4) if qualities else None,
            "avg_rating": round(np.mean(ratings), 2) if ratings else None,
            "learned_weight": self.get_model_weight(
                model_id,
                task_type or TaskType.CODE_GENERATION
            )
        }

    def export_metrics(self, format: str = "json") -> Any:
        """
        Export learning metrics for analytics

        Args:
            format: Export format (json, csv)

        Returns:
            Exported metrics
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_weights": {
                f"{model_id}:{task_type.value}": weight
                for (model_id, task_type), weight in self.model_weights.items()
            },
            "active_ab_tests": [
                {
                    "test_id": test.test_id,
                    "model_a": test.model_a,
                    "model_b": test.model_b,
                    "task_type": test.task_type.value,
                    "samples_a": len(test.results_a),
                    "samples_b": len(test.results_b)
                }
                for test in self.ab_tests.values()
                if self._is_test_active(test)
            ]
        }

        if format == "json":
            return metrics
        else:
            # Could implement CSV export
            return metrics

    def reset_learning(self, model_id: Optional[str] = None, task_type: Optional[TaskType] = None):
        """
        Reset learned weights (for testing or manual intervention)

        Args:
            model_id: Optional model ID filter
            task_type: Optional task type filter
        """
        if model_id is None and task_type is None:
            # Reset all
            self.model_weights.clear()
            self.logger.info("Reset all learned weights")
        else:
            # Reset filtered
            keys_to_reset = [
                key for key in self.model_weights.keys()
                if (model_id is None or key[0] == model_id) and
                   (task_type is None or key[1] == task_type)
            ]
            for key in keys_to_reset:
                self.model_weights[key] = 0.5

            self.logger.info(f"Reset {len(keys_to_reset)} weights")
