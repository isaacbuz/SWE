"""
Provider Performance Metrics

Comprehensive tracking of LLM provider performance, costs, and quality metrics.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg not available - using in-memory storage")

logger = logging.getLogger(__name__)


class TimeRange(Enum):
    """Time range for metrics queries"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


@dataclass
class ProviderExecutionMetric:
    """Single provider execution metric"""
    provider_id: str
    model: str
    task_type: str
    tokens_in: int
    tokens_out: int
    cost: float
    latency_ms: int
    success: bool
    tool_calls_count: int = 0
    error_type: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ProviderStats:
    """Aggregated provider statistics"""
    provider_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_cost: float
    avg_cost_per_request: float
    total_tokens_in: int
    total_tokens_out: int
    tool_calls_count: int
    error_breakdown: Dict[str, int]


@dataclass
class CostAnalysis:
    """Cost analysis across providers"""
    total_cost: float
    cost_by_provider: Dict[str, float]
    cost_by_task_type: Dict[str, float]
    avg_cost_per_request: float
    cost_efficiency: Dict[str, float]  # quality / cost ratio


class ProviderMetricsCollector:
    """
    Comprehensive provider metrics collection system.
    
    Tracks:
    - Per-provider metrics (tokens, cost, latency, success rate)
    - Per-task-type breakdowns
    - Win-rate tracking
    - Cost/performance curves
    - Anomaly detection
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        enable_persistence: bool = True
    ):
        """
        Initialize provider metrics collector.
        
        Args:
            db_url: Database URL for persistence (optional)
            enable_persistence: Whether to persist metrics to database
        """
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.enable_persistence = enable_persistence and ASYNCPG_AVAILABLE and self.db_url
        
        # In-memory storage (fallback or primary)
        self.metrics: List[ProviderExecutionMetric] = []
        self.max_memory_metrics = 10000  # Keep last 10k in memory
        
        # Aggregated stats cache
        self._stats_cache: Dict[str, ProviderStats] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._cache_timestamps: Dict[str, datetime] = {}
        
        if self.enable_persistence:
            self._init_database()
        else:
            logger.info("Using in-memory storage for provider metrics")

    def _init_database(self):
        """Initialize database tables for metrics storage"""
        # This would create tables if they don't exist
        # For now, we'll use in-memory storage
        logger.info("Database persistence enabled (tables should be created separately)")

    async def record_execution(self, metric: ProviderExecutionMetric) -> None:
        """
        Record a provider execution metric.
        
        Args:
            metric: Execution metric to record
        """
        # Add to in-memory storage
        self.metrics.append(metric)
        
        # Keep only recent metrics in memory
        if len(self.metrics) > self.max_memory_metrics:
            self.metrics = self.metrics[-self.max_memory_metrics:]
        
        # Invalidate cache
        cache_key = f"{metric.provider_id}:{metric.task_type}"
        if cache_key in self._stats_cache:
            del self._stats_cache[cache_key]
        
        # Persist to database if enabled
        if self.enable_persistence:
            await self._persist_metric(metric)

    async def _persist_metric(self, metric: ProviderExecutionMetric) -> None:
        """Persist metric to database"""
        # This would insert into database
        # For now, just log
        logger.debug(f"Persisting metric: {metric.provider_id}")

    def _get_time_range_filter(self, time_range: TimeRange) -> datetime:
        """Get start time for time range filter"""
        now = datetime.utcnow()
        
        if time_range == TimeRange.HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            return now - timedelta(days=30)
        else:  # ALL
            return datetime.min

    def _filter_metrics(
        self,
        provider_id: Optional[str] = None,
        task_type: Optional[str] = None,
        time_range: TimeRange = TimeRange.ALL
    ) -> List[ProviderExecutionMetric]:
        """Filter metrics by criteria"""
        filtered = self.metrics
        
        # Time range filter
        start_time = self._get_time_range_filter(time_range)
        filtered = [m for m in filtered if m.timestamp >= start_time]
        
        # Provider filter
        if provider_id:
            filtered = [m for m in filtered if m.provider_id == provider_id]
        
        # Task type filter
        if task_type:
            filtered = [m for m in filtered if m.task_type == task_type]
        
        return filtered

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    async def get_provider_stats(
        self,
        provider_id: str,
        time_range: TimeRange = TimeRange.ALL
    ) -> ProviderStats:
        """
        Get aggregated statistics for a provider.
        
        Args:
            provider_id: Provider identifier
            time_range: Time range for statistics
            
        Returns:
            Provider statistics
        """
        cache_key = f"{provider_id}:{time_range.value}"
        
        # Check cache
        if cache_key in self._stats_cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time and datetime.utcnow() - cache_time < self._cache_ttl:
                return self._stats_cache[cache_key]
        
        # Filter metrics
        metrics = self._filter_metrics(provider_id=provider_id, time_range=time_range)
        
        if not metrics:
            return ProviderStats(
                provider_id=provider_id,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                success_rate=0.0,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                total_cost=0.0,
                avg_cost_per_request=0.0,
                total_tokens_in=0,
                total_tokens_out=0,
                tool_calls_count=0,
                error_breakdown={}
            )
        
        # Calculate statistics
        total_requests = len(metrics)
        successful_requests = sum(1 for m in metrics if m.success)
        failed_requests = total_requests - successful_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        latencies = [m.latency_ms for m in metrics]
        avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
        p50_latency_ms = self._calculate_percentile(latencies, 50)
        p95_latency_ms = self._calculate_percentile(latencies, 95)
        p99_latency_ms = self._calculate_percentile(latencies, 99)
        
        total_cost = sum(m.cost for m in metrics)
        avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0
        
        total_tokens_in = sum(m.tokens_in for m in metrics)
        total_tokens_out = sum(m.tokens_out for m in metrics)
        tool_calls_count = sum(m.tool_calls_count for m in metrics)
        
        # Error breakdown
        error_breakdown = defaultdict(int)
        for m in metrics:
            if not m.success and m.error_type:
                error_breakdown[m.error_type] += 1
        
        stats = ProviderStats(
            provider_id=provider_id,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            avg_latency_ms=avg_latency_ms,
            p50_latency_ms=p50_latency_ms,
            p95_latency_ms=p95_latency_ms,
            p99_latency_ms=p99_latency_ms,
            total_cost=total_cost,
            avg_cost_per_request=avg_cost_per_request,
            total_tokens_in=total_tokens_in,
            total_tokens_out=total_tokens_out,
            tool_calls_count=tool_calls_count,
            error_breakdown=dict(error_breakdown)
        )
        
        # Cache result
        self._stats_cache[cache_key] = stats
        self._cache_timestamps[cache_key] = datetime.utcnow()
        
        return stats

    async def get_win_rates(self, task_type: str) -> Dict[str, float]:
        """
        Get win rates (success rates) for all providers on a task type.
        
        Args:
            task_type: Task type to analyze
            
        Returns:
            Dictionary mapping provider_id to win rate (0-1)
        """
        metrics = self._filter_metrics(task_type=task_type)
        
        if not metrics:
            return {}
        
        # Group by provider
        provider_metrics: Dict[str, List[ProviderExecutionMetric]] = defaultdict(list)
        for m in metrics:
            provider_metrics[m.provider_id].append(m)
        
        # Calculate win rates
        win_rates = {}
        for provider_id, provider_metrics_list in provider_metrics.items():
            total = len(provider_metrics_list)
            successful = sum(1 for m in provider_metrics_list if m.success)
            win_rates[provider_id] = successful / total if total > 0 else 0.0
        
        return win_rates

    async def get_cost_analysis(
        self,
        time_range: TimeRange = TimeRange.ALL
    ) -> CostAnalysis:
        """
        Get cost analysis across all providers.
        
        Args:
            time_range: Time range for analysis
            
        Returns:
            Cost analysis
        """
        metrics = self._filter_metrics(time_range=time_range)
        
        if not metrics:
            return CostAnalysis(
                total_cost=0.0,
                cost_by_provider={},
                cost_by_task_type={},
                avg_cost_per_request=0.0,
                cost_efficiency={}
            )
        
        # Calculate costs
        total_cost = sum(m.cost for m in metrics)
        avg_cost_per_request = total_cost / len(metrics) if metrics else 0.0
        
        # Cost by provider
        cost_by_provider: Dict[str, float] = defaultdict(float)
        for m in metrics:
            cost_by_provider[m.provider_id] += m.cost
        
        # Cost by task type
        cost_by_task_type: Dict[str, float] = defaultdict(float)
        for m in metrics:
            cost_by_task_type[m.task_type] += m.cost
        
        # Cost efficiency (success rate / cost per request)
        cost_efficiency: Dict[str, float] = {}
        provider_stats: Dict[str, ProviderStats] = {}
        
        for provider_id in cost_by_provider.keys():
            stats = await self.get_provider_stats(provider_id, time_range)
            provider_stats[provider_id] = stats
            
            if stats.avg_cost_per_request > 0:
                # Higher success rate and lower cost = higher efficiency
                efficiency = stats.success_rate / stats.avg_cost_per_request
                cost_efficiency[provider_id] = efficiency
        
        return CostAnalysis(
            total_cost=total_cost,
            cost_by_provider=dict(cost_by_provider),
            cost_by_task_type=dict(cost_by_task_type),
            avg_cost_per_request=avg_cost_per_request,
            cost_efficiency=cost_efficiency
        )

    def export_metrics(
        self,
        format: str = "json",
        time_range: TimeRange = TimeRange.ALL
    ) -> str:
        """
        Export metrics in specified format.
        
        Args:
            format: Export format ("json" or "prometheus")
            time_range: Time range for export
            
        Returns:
            Exported metrics as string
        """
        metrics = self._filter_metrics(time_range=time_range)
        
        if format == "json":
            return json.dumps(
                [asdict(m) for m in metrics],
                default=str,
                indent=2
            )
        
        elif format == "prometheus":
            # Prometheus format
            lines = []
            
            # Provider stats
            provider_ids = set(m.provider_id for m in metrics)
            for provider_id in provider_ids:
                provider_metrics = [m for m in metrics if m.provider_id == provider_id]
                
                total = len(provider_metrics)
                successful = sum(1 for m in provider_metrics if m.success)
                total_cost = sum(m.cost for m in provider_metrics)
                total_tokens_in = sum(m.tokens_in for m in provider_metrics)
                total_tokens_out = sum(m.tokens_out for m in provider_metrics)
                
                lines.append(
                    f'provider_requests_total{{provider="{provider_id}"}} {total}'
                )
                lines.append(
                    f'provider_requests_successful{{provider="{provider_id}"}} {successful}'
                )
                lines.append(
                    f'provider_cost_total{{provider="{provider_id}"}} {total_cost}'
                )
                lines.append(
                    f'provider_tokens_in_total{{provider="{provider_id}"}} {total_tokens_in}'
                )
                lines.append(
                    f'provider_tokens_out_total{{provider="{provider_id}"}} {total_tokens_out}'
                )
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def detect_anomalies(
        self,
        provider_id: Optional[str] = None,
        threshold_multiplier: float = 2.0
    ) -> List[Dict[str, any]]:
        """
        Detect anomalies in provider metrics.
        
        Args:
            provider_id: Optional provider to check (all if None)
            threshold_multiplier: Multiplier for anomaly detection threshold
            
        Returns:
            List of detected anomalies
        """
        metrics = self._filter_metrics(provider_id=provider_id, time_range=TimeRange.DAY)
        
        if len(metrics) < 10:
            return []  # Not enough data
        
        anomalies = []
        
        # Calculate baseline statistics
        latencies = [m.latency_ms for m in metrics]
        costs = [m.cost for m in metrics]
        
        avg_latency = sum(latencies) / len(latencies)
        avg_cost = sum(costs) / len(costs)
        
        latency_threshold = avg_latency * threshold_multiplier
        cost_threshold = avg_cost * threshold_multiplier
        
        # Check for anomalies
        for m in metrics:
            if m.latency_ms > latency_threshold:
                anomalies.append({
                    "type": "high_latency",
                    "provider_id": m.provider_id,
                    "timestamp": m.timestamp,
                    "value": m.latency_ms,
                    "threshold": latency_threshold,
                    "message": f"High latency detected: {m.latency_ms}ms (threshold: {latency_threshold}ms)"
                })
            
            if m.cost > cost_threshold:
                anomalies.append({
                    "type": "high_cost",
                    "provider_id": m.provider_id,
                    "timestamp": m.timestamp,
                    "value": m.cost,
                    "threshold": cost_threshold,
                    "message": f"High cost detected: ${m.cost:.4f} (threshold: ${cost_threshold:.4f})"
                })
        
        return anomalies

