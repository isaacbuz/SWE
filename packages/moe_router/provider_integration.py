"""
Provider Metrics Integration for MoE Router

Integrates MoE Router with ProviderMetricsCollector for enhanced provider selection
based on real-time performance metrics.
"""
import logging
from typing import Optional, Dict, Any
from .models import RoutingRequest, TaskType, Provider

try:
    from ..observability.provider_metrics import (
        ProviderMetricsCollector,
        ProviderStats,
        TimeRange
    )
    PROVIDER_METRICS_AVAILABLE = True
except ImportError:
    PROVIDER_METRICS_AVAILABLE = False
    logging.warning("ProviderMetricsCollector not available - using basic metrics only")


class ProviderMetricsIntegration:
    """
    Integration layer between MoE Router and ProviderMetricsCollector
    
    Enhances router decisions with real-time provider performance data.
    """
    
    def __init__(self, provider_metrics_collector: Optional[Any] = None):
        """
        Initialize provider metrics integration
        
        Args:
            provider_metrics_collector: Optional ProviderMetricsCollector instance
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.provider_metrics = provider_metrics_collector
        self.enabled = PROVIDER_METRICS_AVAILABLE and provider_metrics_collector is not None
        
        if not self.enabled:
            self.logger.warning(
                "Provider metrics integration disabled - "
                "ProviderMetricsCollector not available"
            )
    
    def get_provider_score_adjustment(
        self,
        provider: Provider,
        task_type: TaskType,
        time_range: TimeRange = TimeRange.DAY
    ) -> float:
        """
        Get score adjustment for a provider based on performance metrics
        
        Returns a multiplier (0.0 to 2.0) to adjust provider scores:
        - < 1.0: Penalty for poor performance
        - 1.0: No adjustment (baseline)
        - > 1.0: Bonus for excellent performance
        
        Args:
            provider: Provider to evaluate
            task_type: Task type for context
            time_range: Time range for metrics
            
        Returns:
            Score adjustment multiplier
        """
        if not self.enabled:
            return 1.0
        
        try:
            stats = self.provider_metrics.get_provider_stats(
                provider_id=provider.value,
                time_range=time_range,
                task_type=task_type.value
            )
            
            # Base adjustment from success rate
            if stats.total_requests < 10:
                return 1.0  # Not enough data
            
            # Success rate adjustment (0.5 to 1.5 multiplier)
            success_rate_adjustment = 0.5 + (stats.success_rate * 1.0)
            
            # Latency adjustment (penalize high latency)
            latency_adjustment = 1.0
            if stats.avg_latency_ms and stats.avg_latency_ms > 5000:
                # Penalize if average latency > 5 seconds
                latency_adjustment = max(0.7, 1.0 - (stats.avg_latency_ms - 5000) / 10000)
            
            # Cost efficiency adjustment (bonus for low cost)
            cost_adjustment = 1.0
            if stats.avg_cost_per_request and stats.avg_cost_per_request > 0:
                # Bonus for cost efficiency (inverse relationship)
                cost_adjustment = min(1.2, 1.0 + (0.01 / max(stats.avg_cost_per_request, 0.001)))
            
            # Combined adjustment
            adjustment = success_rate_adjustment * latency_adjustment * cost_adjustment
            
            # Clamp to reasonable range
            adjustment = max(0.5, min(2.0, adjustment))
            
            self.logger.debug(
                f"Provider {provider.value} adjustment: {adjustment:.2f} "
                f"(success={stats.success_rate:.2%}, latency={stats.avg_latency_ms}ms, "
                f"cost=${stats.avg_cost_per_request:.6f})"
            )
            
            return adjustment
            
        except Exception as e:
            self.logger.warning(f"Error getting provider metrics: {e}")
            return 1.0
    
    def get_win_rate(
        self,
        task_type: TaskType,
        time_range: TimeRange = TimeRange.DAY
    ) -> Dict[str, float]:
        """
        Get win rates for all providers on a task type
        
        Args:
            task_type: Task type to analyze
            time_range: Time range for metrics
            
        Returns:
            Dictionary mapping provider_id -> win_rate
        """
        if not self.enabled:
            return {}
        
        try:
            return self.provider_metrics.get_win_rates(
                task_type=task_type.value,
                time_range=time_range
            )
        except Exception as e:
            self.logger.warning(f"Error getting win rates: {e}")
            return {}
    
    def detect_provider_anomalies(
        self,
        provider: Provider,
        task_type: Optional[TaskType] = None,
        time_range: TimeRange = TimeRange.DAY
    ) -> list:
        """
        Detect performance anomalies for a provider
        
        Args:
            provider: Provider to check
            task_type: Optional task type filter
            time_range: Time range for analysis
            
        Returns:
            List of anomaly descriptions
        """
        if not self.enabled:
            return []
        
        try:
            return self.provider_metrics.detect_anomalies(
                provider_id=provider.value,
                task_type=task_type.value if task_type else None,
                time_range=time_range
            )
        except Exception as e:
            self.logger.warning(f"Error detecting anomalies: {e}")
            return []

