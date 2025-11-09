"""
Prometheus Metrics Service

Provides Prometheus metrics collection and export.
"""
import asyncio
from typing import Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    REGISTRY,
    CollectorRegistry,
)
from prometheus_client.multiprocess import MultiProcessCollector

# Create a separate registry for this service
_metrics_registry: Optional[CollectorRegistry] = None


def get_metrics_registry() -> CollectorRegistry:
    """Get or create metrics registry"""
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = CollectorRegistry()
    return _metrics_registry


class MetricsService:
    """Prometheus metrics service"""

    def __init__(self):
        self.registry = get_metrics_registry()

        # HTTP metrics
        self.http_request_duration = Histogram(
            'swe_platform_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'route', 'status_code'],
            registry=self.registry
        )

        self.http_request_total = Counter(
            'swe_platform_http_requests_total',
            'Total number of HTTP requests',
            ['method', 'route', 'status_code'],
            registry=self.registry
        )

        self.http_request_errors = Counter(
            'swe_platform_http_request_errors_total',
            'Total number of HTTP request errors',
            ['method', 'route', 'error_type'],
            registry=self.registry
        )

        # LLM Provider metrics
        self.llm_provider_requests = Counter(
            'swe_platform_llm_provider_requests_total',
            'Total number of LLM provider requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )

        self.llm_provider_latency = Histogram(
            'swe_platform_llm_provider_latency_seconds',
            'LLM provider request latency in seconds',
            ['provider', 'model'],
            registry=self.registry
        )

        self.llm_provider_tokens = Counter(
            'swe_platform_llm_provider_tokens_total',
            'Total number of tokens processed',
            ['provider', 'model', 'type'],
            registry=self.registry
        )

        self.llm_provider_cost = Counter(
            'swe_platform_llm_provider_cost_usd_total',
            'Total cost in USD for LLM provider usage',
            ['provider', 'model'],
            registry=self.registry
        )

        # Tool execution metrics
        self.tool_executions = Counter(
            'swe_platform_tool_executions_total',
            'Total number of tool executions',
            ['tool_name', 'status'],
            registry=self.registry
        )

        self.tool_execution_duration = Histogram(
            'swe_platform_tool_execution_duration_seconds',
            'Tool execution duration in seconds',
            ['tool_name'],
            registry=self.registry
        )

        # Connection metrics
        self.active_connections = Gauge(
            'swe_platform_active_connections',
            'Number of active connections',
            ['type'],
            registry=self.registry
        )

        # Cache metrics
        self.cache_hits = Counter(
            'swe_platform_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )

        self.cache_misses = Counter(
            'swe_platform_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )

    async def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        # Use multiprocess collector if in multiprocess mode
        if hasattr(self.registry, '_multiprocess_mode'):
            collector = MultiProcessCollector(self.registry)
            return generate_latest(collector)
        return generate_latest(self.registry)

    def record_http_request(
        self,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float
    ):
        """Record HTTP request metrics"""
        self.http_request_duration.labels(
            method=method,
            route=route,
            status_code=str(status_code)
        ).observe(duration_seconds)

        self.http_request_total.labels(
            method=method,
            route=route,
            status_code=str(status_code)
        ).inc()

        if status_code >= 400:
            error_type = 'server_error' if status_code >= 500 else 'client_error'
            self.http_request_errors.labels(
                method=method,
                route=route,
                error_type=error_type
            ).inc()

    def record_llm_request(
        self,
        provider: str,
        model: str,
        status: str,
        latency_seconds: float,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None
    ):
        """Record LLM provider request metrics"""
        self.llm_provider_requests.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()

        self.llm_provider_latency.labels(
            provider=provider,
            model=model
        ).observe(latency_seconds)

        if prompt_tokens:
            self.llm_provider_tokens.labels(
                provider=provider,
                model=model,
                type='prompt'
            ).inc(prompt_tokens)

        if completion_tokens:
            self.llm_provider_tokens.labels(
                provider=provider,
                model=model,
                type='completion'
            ).inc(completion_tokens)

        if cost_usd:
            self.llm_provider_cost.labels(
                provider=provider,
                model=model
            ).inc(cost_usd)

    def record_tool_execution(
        self,
        tool_name: str,
        status: str,
        duration_seconds: float
    ):
        """Record tool execution metrics"""
        self.tool_executions.labels(
            tool_name=tool_name,
            status=status
        ).inc()

        self.tool_execution_duration.labels(
            tool_name=tool_name
        ).observe(duration_seconds)

    def update_active_connections(self, connection_type: str, count: int):
        """Update active connections gauge"""
        self.active_connections.labels(type=connection_type).set(count)

    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        self.cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        self.cache_misses.labels(cache_type=cache_type).inc()


# Singleton instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get metrics service singleton"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service

