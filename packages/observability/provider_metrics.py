"""
Provider Performance Metrics Collection
Tracks per-provider metrics, win rates, and cost/performance analytics
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import statistics
import logging

from .metrics import MetricsCollector


class TimeRange(Enum):
    """Time range for metrics queries"""
    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"


@dataclass
class ProviderExecutionMetric:
    """Single provider execution metric"""
    provider_id: str
    task_type: str
    tokens_in: int
    tokens_out: int
    cost: float
    latency_ms: int
    success: bool
    tool_calls_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProviderStats:
    """Aggregated provider statistics"""
    provider_id: str
    task_type: Optional[str] = None
    
    # Request counts
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Token usage
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    avg_tokens_in: float = 0.0
    avg_tokens_out: float = 0.0
    
    # Cost metrics
    total_cost: float = 0.0
    avg_cost_per_request: float = 0.0
    
    # Latency metrics (in milliseconds)
    p50_latency_ms: Optional[int] = None
    p95_latency_ms: Optional[int] = None
    p99_latency_ms: Optional[int] = None
    avg_latency_ms: float = 0.0
    
    # Success rate
    success_rate: float = 0.0
    
    # Tool calling metrics
    total_tool_calls: int = 0
    avg_tool_calls_per_request: float = 0.0
    tool_call_success_rate: float = 0.0
    
    # Time range
    time_range: TimeRange = TimeRange.DAY


class ProviderMetricsCollector:
    """
    Collects and analyzes provider-specific performance metrics
    
    Features:
    - Per-provider metrics tracking
    - Per-task-type breakdowns
    - Win-rate tracking (which provider performs best)
    - Cost/performance curves
    - Anomaly detection
    """
    
    def __init__(self, base_collector: Optional[MetricsCollector] = None):
        """
        Initialize provider metrics collector
        
        Args:
            base_collector: Base metrics collector for OpenTelemetry integration
        """
        self.base_collector = base_collector
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # In-memory storage (in production, this would use Redis or a database)
        self._metrics: List[ProviderExecutionMetric] = []
        self._max_metrics = 10000  # Keep last 10k metrics
        
        # Win-rate tracking: task_type -> provider_id -> win_count
        self._win_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
    def record_execution(self, metric: ProviderExecutionMetric) -> None:
        """
        Record a provider execution metric
        
        Args:
            metric: Execution metric to record
        """
        # Add to in-memory storage
        self._metrics.append(metric)
        
        # Trim if too many metrics
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics:]
        
        # Also record in base collector if available
        if self.base_collector:
            self.base_collector.record_llm_request(
                provider=metric.provider_id,
                model="",  # Model info not in ProviderExecutionMetric
                duration_seconds=metric.latency_ms / 1000.0,
                prompt_tokens=metric.tokens_in,
                completion_tokens=metric.tokens_out,
                cost=metric.cost,
                status="success" if metric.success else "failure"
            )
        
        self.logger.debug(
            f"Recorded execution: {metric.provider_id} on {metric.task_type} "
            f"(cost=${metric.cost:.4f}, latency={metric.latency_ms}ms, success={metric.success})"
        )
    
    def get_provider_stats(
        self,
        provider_id: str,
        time_range: TimeRange = TimeRange.DAY,
        task_type: Optional[str] = None
    ) -> ProviderStats:
        """
        Get aggregated statistics for a provider
        
        Args:
            provider_id: Provider identifier
            time_range: Time range to analyze
            task_type: Optional task type filter
            
        Returns:
            Aggregated provider statistics
        """
        cutoff_time = self._get_cutoff_time(time_range)
        
        # Filter metrics
        filtered = [
            m for m in self._metrics
            if m.provider_id == provider_id
            and m.timestamp >= cutoff_time
            and (task_type is None or m.task_type == task_type)
        ]
        
        if not filtered:
            return ProviderStats(
                provider_id=provider_id,
                task_type=task_type,
                time_range=time_range
            )
        
        # Calculate statistics
        successful = [m for m in filtered if m.success]
        latencies = [m.latency_ms for m in filtered]
        
        # Percentiles
        latencies_sorted = sorted(latencies)
        p50_idx = int(len(latencies_sorted) * 0.5)
        p95_idx = int(len(latencies_sorted) * 0.95)
        p99_idx = int(len(latencies_sorted) * 0.99)
        
        return ProviderStats(
            provider_id=provider_id,
            task_type=task_type,
            total_requests=len(filtered),
            successful_requests=len(successful),
            failed_requests=len(filtered) - len(successful),
            total_tokens_in=sum(m.tokens_in for m in filtered),
            total_tokens_out=sum(m.tokens_out for m in filtered),
            avg_tokens_in=statistics.mean([m.tokens_in for m in filtered]) if filtered else 0.0,
            avg_tokens_out=statistics.mean([m.tokens_out for m in filtered]) if filtered else 0.0,
            total_cost=sum(m.cost for m in filtered),
            avg_cost_per_request=statistics.mean([m.cost for m in filtered]) if filtered else 0.0,
            p50_latency_ms=latencies_sorted[p50_idx] if latencies_sorted else None,
            p95_latency_ms=latencies_sorted[p95_idx] if p95_idx < len(latencies_sorted) else None,
            p99_latency_ms=latencies_sorted[p99_idx] if p99_idx < len(latencies_sorted) else None,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0.0,
            success_rate=len(successful) / len(filtered) if filtered else 0.0,
            total_tool_calls=sum(m.tool_calls_count for m in filtered),
            avg_tool_calls_per_request=statistics.mean([m.tool_calls_count for m in filtered]) if filtered else 0.0,
            tool_call_success_rate=len([m for m in successful if m.tool_calls_count > 0]) / len([m for m in filtered if m.tool_calls_count > 0]) if any(m.tool_calls_count > 0 for m in filtered) else 0.0,
            time_range=time_range
        )
    
    def get_win_rates(self, task_type: str, time_range: TimeRange = TimeRange.DAY) -> Dict[str, float]:
        """
        Get win rates for providers on a specific task type
        
        Win rate is calculated as: (successful requests) / (total requests)
        Higher win rate = better performance
        
        Args:
            task_type: Task type to analyze
            time_range: Time range to analyze
            
        Returns:
            Dictionary mapping provider_id -> win_rate (0.0 to 1.0)
        """
        cutoff_time = self._get_cutoff_time(time_range)
        
        # Filter metrics by task type and time range
        filtered = [
            m for m in self._metrics
            if m.task_type == task_type
            and m.timestamp >= cutoff_time
        ]
        
        if not filtered:
            return {}
        
        # Group by provider
        provider_metrics: Dict[str, List[ProviderExecutionMetric]] = defaultdict(list)
        for metric in filtered:
            provider_metrics[metric.provider_id].append(metric)
        
        # Calculate win rates
        win_rates: Dict[str, float] = {}
        for provider_id, metrics in provider_metrics.items():
            successful = sum(1 for m in metrics if m.success)
            win_rates[provider_id] = successful / len(metrics) if metrics else 0.0
        
        return win_rates
    
    def get_cost_performance_curve(
        self,
        task_type: str,
        time_range: TimeRange = TimeRange.DAY
    ) -> List[Tuple[str, float, float]]:
        """
        Get cost/performance curve data
        
        Returns list of (provider_id, avg_cost, success_rate) tuples
        sorted by cost ascending
        
        Args:
            task_type: Task type to analyze
            time_range: Time range to analyze
            
        Returns:
            List of tuples: (provider_id, avg_cost, success_rate)
        """
        cutoff_time = self._get_cutoff_time(time_range)
        
        # Filter metrics
        filtered = [
            m for m in self._metrics
            if m.task_type == task_type
            and m.timestamp >= cutoff_time
        ]
        
        if not filtered:
            return []
        
        # Group by provider
        provider_metrics: Dict[str, List[ProviderExecutionMetric]] = defaultdict(list)
        for metric in filtered:
            provider_metrics[metric.provider_id].append(metric)
        
        # Calculate cost/performance
        curve_data: List[Tuple[str, float, float]] = []
        for provider_id, metrics in provider_metrics.items():
            avg_cost = statistics.mean([m.cost for m in metrics])
            successful = sum(1 for m in metrics if m.success)
            success_rate = successful / len(metrics) if metrics else 0.0
            curve_data.append((provider_id, avg_cost, success_rate))
        
        # Sort by cost ascending
        curve_data.sort(key=lambda x: x[1])
        
        return curve_data
    
    def detect_anomalies(
        self,
        provider_id: str,
        task_type: Optional[str] = None,
        time_range: TimeRange = TimeRange.DAY
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in provider performance
        
        Anomalies include:
        - High cost spikes
        - High latency spikes
        - Low success rates
        
        Args:
            provider_id: Provider to analyze
            task_type: Optional task type filter
            time_range: Time range to analyze
            
        Returns:
            List of anomaly descriptions
        """
        stats = self.get_provider_stats(provider_id, time_range, task_type)
        anomalies: List[Dict[str, Any]] = []
        
        if stats.total_requests < 10:
            return anomalies  # Not enough data
        
        # Get baseline from all providers for comparison
        all_providers = set(m.provider_id for m in self._metrics)
        baseline_stats = [
            self.get_provider_stats(pid, time_range, task_type)
            for pid in all_providers
            if pid != provider_id
        ]
        
        if baseline_stats:
            avg_baseline_cost = statistics.mean([s.avg_cost_per_request for s in baseline_stats if s.total_requests > 0])
            avg_baseline_latency = statistics.mean([s.avg_latency_ms for s in baseline_stats if s.total_requests > 0])
            avg_baseline_success = statistics.mean([s.success_rate for s in baseline_stats if s.total_requests > 0])
            
            # Check for high cost
            if avg_baseline_cost > 0 and stats.avg_cost_per_request > avg_baseline_cost * 2:
                anomalies.append({
                    "type": "high_cost",
                    "severity": "warning",
                    "message": f"Cost is {stats.avg_cost_per_request / avg_baseline_cost:.2f}x higher than baseline",
                    "value": stats.avg_cost_per_request,
                    "baseline": avg_baseline_cost
                })
            
            # Check for high latency
            if avg_baseline_latency > 0 and stats.avg_latency_ms > avg_baseline_latency * 2:
                anomalies.append({
                    "type": "high_latency",
                    "severity": "warning",
                    "message": f"Latency is {stats.avg_latency_ms / avg_baseline_latency:.2f}x higher than baseline",
                    "value": stats.avg_latency_ms,
                    "baseline": avg_baseline_latency
                })
            
            # Check for low success rate
            if stats.success_rate < avg_baseline_success * 0.5:
                anomalies.append({
                    "type": "low_success_rate",
                    "severity": "error",
                    "message": f"Success rate ({stats.success_rate:.2%}) is significantly lower than baseline ({avg_baseline_success:.2%})",
                    "value": stats.success_rate,
                    "baseline": avg_baseline_success
                })
        
        return anomalies
    
    def _get_cutoff_time(self, time_range: TimeRange) -> datetime:
        """Get cutoff time for time range"""
        now = datetime.now()
        if time_range == TimeRange.HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return now - timedelta(days=7)
        elif time_range == TimeRange.MONTH:
            return now - timedelta(days=30)
        else:
            return now - timedelta(days=1)

