"""
Performance Tracking Strategy

Tracks success rates, latency, and quality metrics for model+task combinations.
Uses Redis for persistent storage with time-based decay.
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - using in-memory fallback")

from ..models import (
    ModelDefinition,
    TaskType,
    PerformanceMetrics,
    FeedbackData
)


class PerformanceTracker:
    """Tracks and analyzes model performance metrics"""

    # Time decay constants
    DECAY_HALF_LIFE_HOURS = 168  # 1 week
    MIN_REQUESTS_FOR_CONFIDENCE = 10
    CONFIDENCE_WEIGHT_SCALE = 100

    def __init__(
        self,
        redis_url: Optional[str] = None,
        namespace: str = "moe:perf"
    ):
        """
        Initialize performance tracker

        Args:
            redis_url: Redis connection URL
            namespace: Redis key namespace
        """
        self.namespace = namespace
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize Redis or fallback to in-memory
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
                self.use_redis = True
                self.logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}, using in-memory fallback")
                self.use_redis = False
                self._init_memory_store()
        else:
            self.use_redis = False
            self._init_memory_store()

    def _init_memory_store(self):
        """Initialize in-memory storage"""
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._feedback_history: List[FeedbackData] = []

    def _get_key(self, model_id: str, task_type: TaskType) -> str:
        """Generate Redis key for model+task combination"""
        return f"{self.namespace}:{model_id}:{task_type.value}"

    def _get_feedback_key(self, request_id: str) -> str:
        """Generate Redis key for feedback data"""
        return f"{self.namespace}:feedback:{request_id}"

    def record_request(
        self,
        model_id: str,
        task_type: TaskType,
        success: bool,
        latency_ms: Optional[int] = None,
        cost: Optional[float] = None,
        quality_score: Optional[float] = None
    ):
        """
        Record a model request and its outcome

        Args:
            model_id: Model identifier
            task_type: Task type
            success: Whether request succeeded
            latency_ms: Latency in milliseconds
            cost: Actual cost
            quality_score: Quality score (0-1)
        """
        key = self._get_key(model_id, task_type)

        if self.use_redis:
            self._record_request_redis(
                key, model_id, task_type, success,
                latency_ms, cost, quality_score
            )
        else:
            self._record_request_memory(
                key, model_id, task_type, success,
                latency_ms, cost, quality_score
            )

        self.logger.debug(
            f"Recorded {'successful' if success else 'failed'} request for "
            f"{model_id} on {task_type}"
        )

    def _record_request_redis(
        self,
        key: str,
        model_id: str,
        task_type: TaskType,
        success: bool,
        latency_ms: Optional[int],
        cost: Optional[float],
        quality_score: Optional[float]
    ):
        """Record request in Redis"""
        try:
            # Get existing metrics or create new
            data = self.redis.get(key)
            if data:
                metrics = PerformanceMetrics.parse_raw(data)
            else:
                metrics = PerformanceMetrics(
                    model_id=model_id,
                    task_type=task_type
                )

            # Update counts
            metrics.total_requests += 1
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

            # Update running averages
            if latency_ms is not None:
                if metrics.avg_latency_ms is None:
                    metrics.avg_latency_ms = float(latency_ms)
                else:
                    # Exponential moving average
                    alpha = 0.1
                    metrics.avg_latency_ms = (
                        alpha * latency_ms +
                        (1 - alpha) * metrics.avg_latency_ms
                    )

            if cost is not None:
                if metrics.avg_cost is None:
                    metrics.avg_cost = cost
                else:
                    alpha = 0.1
                    metrics.avg_cost = (
                        alpha * cost +
                        (1 - alpha) * metrics.avg_cost
                    )

            if quality_score is not None:
                if metrics.avg_quality is None:
                    metrics.avg_quality = quality_score
                else:
                    alpha = 0.1
                    metrics.avg_quality = (
                        alpha * quality_score +
                        (1 - alpha) * metrics.avg_quality
                    )

            # Update timestamp
            metrics.last_updated = datetime.utcnow()

            # Save back to Redis with TTL
            self.redis.setex(
                key,
                timedelta(days=30),  # 30 day TTL
                metrics.json()
            )

        except Exception as e:
            self.logger.error(f"Error recording request in Redis: {e}")

    def _record_request_memory(
        self,
        key: str,
        model_id: str,
        task_type: TaskType,
        success: bool,
        latency_ms: Optional[int],
        cost: Optional[float],
        quality_score: Optional[float]
    ):
        """Record request in memory"""
        if key not in self._metrics:
            self._metrics[key] = PerformanceMetrics(
                model_id=model_id,
                task_type=task_type
            )

        metrics = self._metrics[key]

        # Update counts
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # Update running averages
        if latency_ms is not None:
            if metrics.avg_latency_ms is None:
                metrics.avg_latency_ms = float(latency_ms)
            else:
                alpha = 0.1
                metrics.avg_latency_ms = (
                    alpha * latency_ms +
                    (1 - alpha) * metrics.avg_latency_ms
                )

        if cost is not None:
            if metrics.avg_cost is None:
                metrics.avg_cost = cost
            else:
                alpha = 0.1
                metrics.avg_cost = alpha * cost + (1 - alpha) * metrics.avg_cost

        if quality_score is not None:
            if metrics.avg_quality is None:
                metrics.avg_quality = quality_score
            else:
                alpha = 0.1
                metrics.avg_quality = (
                    alpha * quality_score +
                    (1 - alpha) * metrics.avg_quality
                )

        metrics.last_updated = datetime.utcnow()

    def get_metrics(
        self,
        model_id: str,
        task_type: TaskType
    ) -> Optional[PerformanceMetrics]:
        """
        Get performance metrics for model+task combination

        Args:
            model_id: Model identifier
            task_type: Task type

        Returns:
            Performance metrics or None if no data
        """
        key = self._get_key(model_id, task_type)

        if self.use_redis:
            try:
                data = self.redis.get(key)
                if data:
                    return PerformanceMetrics.parse_raw(data)
            except Exception as e:
                self.logger.error(f"Error retrieving metrics from Redis: {e}")
        else:
            return self._metrics.get(key)

        return None

    def calculate_confidence_score(
        self,
        metrics: PerformanceMetrics
    ) -> float:
        """
        Calculate confidence score based on sample size and recency

        Args:
            metrics: Performance metrics

        Returns:
            Confidence score (0-1)
        """
        # Sample size component
        sample_confidence = min(
            1.0,
            metrics.total_requests / self.CONFIDENCE_WEIGHT_SCALE
        )

        # Recency component with exponential decay
        age_hours = (datetime.utcnow() - metrics.last_updated).total_seconds() / 3600
        decay_factor = 0.5 ** (age_hours / self.DECAY_HALF_LIFE_HOURS)

        # Combined confidence
        confidence = sample_confidence * decay_factor

        return round(confidence, 4)

    def get_recommendation_weight(
        self,
        model_id: str,
        task_type: TaskType
    ) -> float:
        """
        Get recommendation weight for model+task combination

        Args:
            model_id: Model identifier
            task_type: Task type

        Returns:
            Recommendation weight (0-1), higher means more recommended
        """
        metrics = self.get_metrics(model_id, task_type)

        if not metrics or metrics.total_requests < self.MIN_REQUESTS_FOR_CONFIDENCE:
            # Not enough data - return neutral weight
            return 0.5

        # Calculate components
        confidence = self.calculate_confidence_score(metrics)
        success_rate = metrics.success_rate

        # Combine success rate and confidence
        # High success rate + high confidence = high weight
        weight = (success_rate * 0.7 + confidence * 0.3)

        return round(weight, 4)

    def get_top_models(
        self,
        task_type: TaskType,
        models: List[ModelDefinition],
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get top performing models for a task type

        Args:
            task_type: Task type
            models: List of available models
            top_n: Number of top models to return

        Returns:
            List of (model_id, weight) tuples sorted by weight
        """
        weights = []

        for model in models:
            weight = self.get_recommendation_weight(model.id, task_type)
            weights.append((model.id, weight))

        # Sort by weight descending
        weights.sort(key=lambda x: x[1], reverse=True)

        return weights[:top_n]

    def record_feedback(self, feedback: FeedbackData):
        """
        Record feedback data for learning loop

        Args:
            feedback: Feedback data
        """
        if self.use_redis:
            try:
                key = self._get_feedback_key(feedback.request_id)
                self.redis.setex(
                    key,
                    timedelta(days=90),  # 90 day TTL
                    feedback.json()
                )
            except Exception as e:
                self.logger.error(f"Error recording feedback in Redis: {e}")
        else:
            self._feedback_history.append(feedback)

        # Update metrics based on feedback
        success = feedback.outcome == "success"
        self.record_request(
            model_id=feedback.model_id,
            task_type=feedback.task_type,
            success=success,
            latency_ms=feedback.actual_latency_ms,
            cost=feedback.actual_cost,
            quality_score=feedback.quality_score
        )

    def get_feedback_history(
        self,
        model_id: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 100
    ) -> List[FeedbackData]:
        """
        Get feedback history with optional filtering

        Args:
            model_id: Filter by model ID
            task_type: Filter by task type
            limit: Maximum number of records

        Returns:
            List of feedback data
        """
        if self.use_redis:
            # Query Redis for feedback
            pattern = f"{self.namespace}:feedback:*"
            feedback_list = []

            try:
                for key in self.redis.scan_iter(match=pattern, count=1000):
                    data = self.redis.get(key)
                    if data:
                        feedback = FeedbackData.parse_raw(data)

                        # Apply filters
                        if model_id and feedback.model_id != model_id:
                            continue
                        if task_type and feedback.task_type != task_type:
                            continue

                        feedback_list.append(feedback)

                        if len(feedback_list) >= limit:
                            break

            except Exception as e:
                self.logger.error(f"Error retrieving feedback from Redis: {e}")

            return feedback_list
        else:
            # Filter in-memory feedback
            filtered = self._feedback_history

            if model_id:
                filtered = [f for f in filtered if f.model_id == model_id]
            if task_type:
                filtered = [f for f in filtered if f.task_type == task_type]

            return filtered[-limit:]

    def get_aggregate_stats(self, task_type: Optional[TaskType] = None) -> Dict:
        """
        Get aggregate statistics across all models

        Args:
            task_type: Optional task type filter

        Returns:
            Dictionary with aggregate statistics
        """
        stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_success_rate": 0.0,
            "models": []
        }

        if self.use_redis:
            pattern = f"{self.namespace}:*:*"
            metrics_list = []

            try:
                for key in self.redis.scan_iter(match=pattern, count=1000):
                    if ":feedback:" in key:
                        continue

                    data = self.redis.get(key)
                    if data:
                        metrics = PerformanceMetrics.parse_raw(data)

                        if task_type and metrics.task_type != task_type:
                            continue

                        metrics_list.append(metrics)

            except Exception as e:
                self.logger.error(f"Error retrieving stats from Redis: {e}")

        else:
            metrics_list = list(self._metrics.values())
            if task_type:
                metrics_list = [m for m in metrics_list if m.task_type == task_type]

        # Calculate aggregates
        if metrics_list:
            stats["total_requests"] = sum(m.total_requests for m in metrics_list)
            stats["successful_requests"] = sum(m.successful_requests for m in metrics_list)
            stats["failed_requests"] = sum(m.failed_requests for m in metrics_list)

            if stats["total_requests"] > 0:
                stats["avg_success_rate"] = (
                    stats["successful_requests"] / stats["total_requests"]
                )

            stats["models"] = [
                {
                    "model_id": m.model_id,
                    "task_type": m.task_type.value,
                    "total_requests": m.total_requests,
                    "success_rate": m.success_rate,
                    "avg_latency_ms": m.avg_latency_ms,
                    "avg_cost": m.avg_cost
                }
                for m in metrics_list
            ]

        return stats

    def reset_metrics(self, model_id: Optional[str] = None, task_type: Optional[TaskType] = None):
        """
        Reset metrics (for testing or manual intervention)

        Args:
            model_id: Optional model ID filter
            task_type: Optional task type filter
        """
        if self.use_redis:
            pattern = f"{self.namespace}:"
            if model_id:
                pattern += f"{model_id}:"
            else:
                pattern += "*:"

            if task_type:
                pattern += task_type.value
            else:
                pattern += "*"

            try:
                for key in self.redis.scan_iter(match=pattern):
                    self.redis.delete(key)
                self.logger.info(f"Reset metrics matching pattern: {pattern}")
            except Exception as e:
                self.logger.error(f"Error resetting metrics in Redis: {e}")
        else:
            keys_to_delete = []
            for key in self._metrics.keys():
                parts = key.split(":")
                if len(parts) >= 3:
                    key_model = parts[1]
                    key_task = parts[2]

                    if model_id and key_model != model_id:
                        continue
                    if task_type and key_task != task_type.value:
                        continue

                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._metrics[key]

            self.logger.info(f"Reset {len(keys_to_delete)} metrics from memory")
