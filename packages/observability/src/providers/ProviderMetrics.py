"""Provider Performance Tracking Module

This module provides comprehensive metrics collection and analysis for LLM providers.
Tracks execution metrics, costs, latency, and quality across all providers.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import statistics


class TaskType(Enum):
    """Types of tasks for provider selection"""
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    PLANNING = "planning"
    REVIEW = "review"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


@dataclass
class ProviderExecutionMetric:
    """Metrics for a single provider execution"""
    provider_id: str
    task_type: str
    tokens_in: int
    tokens_out: int
    cost: float
    latency_ms: float
    success: bool
    tool_calls_count: int
    error_type: Optional[str]
    timestamp: datetime


@dataclass
class ProviderStats:
    """Aggregated statistics for a provider"""
    total_requests: int
    success_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_cost: float
    avg_cost_per_request: float
    total_tokens_in: int
    total_tokens_out: int


@dataclass
class TimeRange:
    """Time range for metrics filtering"""
    start: datetime
    end: datetime


@dataclass
class CostAnalysis:
    """Cost analysis across providers"""
    total_cost: float
    cost_by_provider: Dict[str, float]
    cost_by_task_type: Dict[str, float]
    avg_cost_per_request: float


class ProviderMetricsCollector:
    """Collects and analyzes provider performance metrics"""
    
    def __init__(self):
        self.metrics: List[ProviderExecutionMetric] = []
    
    def record_execution(self, metric: ProviderExecutionMetric) -> None:
        """Record a provider execution metric"""
        self.metrics.append(metric)
    
    def get_provider_stats(
        self, 
        provider_id: str, 
        time_range: Optional[TimeRange] = None
    ) -> ProviderStats:
        """Get aggregated statistics for a provider"""
        filtered_metrics = self._filter_metrics(
            provider_id=provider_id,
            time_range=time_range
        )
        
        if not filtered_metrics:
            return ProviderStats(
                total_requests=0,
                success_rate=0.0,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                total_cost=0.0,
                avg_cost_per_request=0.0,
                total_tokens_in=0,
                total_tokens_out=0
            )
        
        total_requests = len(filtered_metrics)
        successful = sum(1 for m in filtered_metrics if m.success)
        latencies = [m.latency_ms for m in filtered_metrics]
        
        return ProviderStats(
            total_requests=total_requests,
            success_rate=successful / total_requests if total_requests > 0 else 0.0,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0.0,
            p50_latency_ms=statistics.median(latencies) if latencies else 0.0,
            p95_latency_ms=self._percentile(latencies, 0.95) if latencies else 0.0,
            p99_latency_ms=self._percentile(latencies, 0.99) if latencies else 0.0,
            total_cost=sum(m.cost for m in filtered_metrics),
            avg_cost_per_request=sum(m.cost for m in filtered_metrics) / total_requests,
            total_tokens_in=sum(m.tokens_in for m in filtered_metrics),
            total_tokens_out=sum(m.tokens_out for m in filtered_metrics)
        )
    
    def get_win_rates(self, task_type: str) -> Dict[str, float]:
        """Calculate which provider performs best for a task type"""
        task_metrics = [m for m in self.metrics if m.task_type == task_type]
        
        if not task_metrics:
            return {}
        
        provider_groups: Dict[str, List[ProviderExecutionMetric]] = {}
        for metric in task_metrics:
            if metric.provider_id not in provider_groups:
                provider_groups[metric.provider_id] = []
            provider_groups[metric.provider_id].append(metric)
        
        win_rates = {}
        for provider_id, metrics_list in provider_groups.items():
            successful = sum(1 for m in metrics_list if m.success)
            total = len(metrics_list)
            win_rates[provider_id] = successful / total if total > 0 else 0.0
        
        return win_rates
    
    def get_cost_analysis(
        self, 
        time_range: Optional[TimeRange] = None
    ) -> CostAnalysis:
        """Get cost breakdown analysis"""
        filtered_metrics = self._filter_metrics(time_range=time_range)
        
        if not filtered_metrics:
            return CostAnalysis(
                total_cost=0.0,
                cost_by_provider={},
                cost_by_task_type={},
                avg_cost_per_request=0.0
            )
        
        total_cost = sum(m.cost for m in filtered_metrics)
        
        cost_by_provider: Dict[str, float] = {}
        for metric in filtered_metrics:
            if metric.provider_id not in cost_by_provider:
                cost_by_provider[metric.provider_id] = 0.0
            cost_by_provider[metric.provider_id] += metric.cost
        
        cost_by_task_type: Dict[str, float] = {}
        for metric in filtered_metrics:
            if metric.task_type not in cost_by_task_type:
                cost_by_task_type[metric.task_type] = 0.0
            cost_by_task_type[metric.task_type] += metric.cost
        
        return CostAnalysis(
            total_cost=total_cost,
            cost_by_provider=cost_by_provider,
            cost_by_task_type=cost_by_task_type,
            avg_cost_per_request=total_cost / len(filtered_metrics)
        )
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format"""
        if format_type == "json":
            import json
            return json.dumps([
                {
                    "provider_id": m.provider_id,
                    "task_type": m.task_type,
                    "tokens_in": m.tokens_in,
                    "tokens_out": m.tokens_out,
                    "cost": m.cost,
                    "latency_ms": m.latency_ms,
                    "success": m.success,
                    "tool_calls_count": m.tool_calls_count,
                    "error_type": m.error_type,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.metrics
            ], indent=2)
        
        elif format_type == "prometheus":
            lines = []
            provider_counts: Dict[str, int] = {}
            for metric in self.metrics:
                provider_counts[metric.provider_id] = provider_counts.get(metric.provider_id, 0) + 1
            
            for provider_id, count in provider_counts.items():
                lines.append(f'provider_requests_total{{provider="{provider_id}"}} {count}')
            
            provider_costs: Dict[str, float] = {}
            for metric in self.metrics:
                provider_costs[metric.provider_id] = provider_costs.get(metric.provider_id, 0.0) + metric.cost
            
            for provider_id, cost in provider_costs.items():
                lines.append(f'provider_cost_total{{provider="{provider_id}"}} {cost}')
            
            return "\n".join(lines)
        else:
            raise ValueError(f"Unknown format type: {format_type}")
    
    def _filter_metrics(
        self,
        provider_id: Optional[str] = None,
        task_type: Optional[str] = None,
        time_range: Optional[TimeRange] = None
    ) -> List[ProviderExecutionMetric]:
        """Filter metrics by various criteria"""
        filtered = self.metrics
        
        if provider_id:
            filtered = [m for m in filtered if m.provider_id == provider_id]
        
        if task_type:
            filtered = [m for m in filtered if m.task_type == task_type]
        
        if time_range:
            filtered = [
                m for m in filtered 
                if time_range.start <= m.timestamp <= time_range.end
            ]
        
        return filtered
    
    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        
        return sorted_data[index]
