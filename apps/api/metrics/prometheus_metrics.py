"""
Prometheus Metrics for FastAPI
Custom metrics for agents, costs, quality, and business KPIs
"""

from typing import Optional, Dict, Any
from functools import wraps
import time

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    Enum,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
import asyncio


class PrometheusMetrics:
    """
    Prometheus metrics for SWE Platform

    Custom metrics:
    - Agent execution metrics
    - Cost tracking metrics
    - Quality gate metrics
    - Business KPI metrics
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()

        # HTTP Request metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            registry=self.registry,
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        self.http_request_size_bytes = Histogram(
            "http_request_size_bytes",
            "HTTP request size in bytes",
            ["method", "endpoint"],
            registry=self.registry,
        )

        self.http_response_size_bytes = Histogram(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # Agent execution metrics
        self.agent_executions_total = Counter(
            "agent_executions_total",
            "Total agent executions",
            ["agent_name", "task_type", "status"],
            registry=self.registry,
        )

        self.agent_execution_duration_seconds = Histogram(
            "agent_execution_duration_seconds",
            "Agent execution duration in seconds",
            ["agent_name", "task_type"],
            registry=self.registry,
            buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),
        )

        self.active_agents = Gauge(
            "active_agents",
            "Number of currently active agents",
            ["agent_name"],
            registry=self.registry,
        )

        self.agent_queue_depth = Gauge(
            "agent_queue_depth",
            "Number of tasks in agent queue",
            ["agent_name"],
            registry=self.registry,
        )

        # LLM and Cost metrics
        self.llm_requests_total = Counter(
            "llm_requests_total",
            "Total LLM API requests",
            ["provider", "model", "status"],
            registry=self.registry,
        )

        self.llm_tokens_total = Counter(
            "llm_tokens_total",
            "Total LLM tokens consumed",
            ["provider", "model", "token_type"],
            registry=self.registry,
        )

        self.llm_cost_usd_total = Counter(
            "llm_cost_usd_total",
            "Total LLM costs in USD",
            ["provider", "model"],
            registry=self.registry,
        )

        self.llm_request_duration_seconds = Histogram(
            "llm_request_duration_seconds",
            "LLM request duration in seconds",
            ["provider", "model"],
            registry=self.registry,
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        )

        # Cost tracking metrics
        self.project_cost_usd = Gauge(
            "project_cost_usd",
            "Current project costs in USD",
            ["project_id"],
            registry=self.registry,
        )

        self.budget_utilization_percent = Gauge(
            "budget_utilization_percent",
            "Budget utilization percentage",
            ["project_id"],
            registry=self.registry,
        )

        self.cost_per_request_usd = Histogram(
            "cost_per_request_usd",
            "Cost per request in USD",
            ["endpoint", "project_id"],
            registry=self.registry,
            buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
        )

        # Quality gate metrics
        self.quality_gates_total = Counter(
            "quality_gates_total",
            "Total quality gate executions",
            ["gate_type", "status"],
            registry=self.registry,
        )

        self.quality_gate_duration_seconds = Histogram(
            "quality_gate_duration_seconds",
            "Quality gate execution duration in seconds",
            ["gate_type"],
            registry=self.registry,
        )

        self.code_coverage_percent = Gauge(
            "code_coverage_percent",
            "Code coverage percentage",
            ["project_id"],
            registry=self.registry,
        )

        self.security_vulnerabilities = Gauge(
            "security_vulnerabilities",
            "Number of security vulnerabilities",
            ["severity", "project_id"],
            registry=self.registry,
        )

        self.code_quality_score = Gauge(
            "code_quality_score",
            "Code quality score (0-100)",
            ["project_id"],
            registry=self.registry,
        )

        # Database metrics
        self.db_queries_total = Counter(
            "db_queries_total",
            "Total database queries",
            ["operation", "table", "status"],
            registry=self.registry,
        )

        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation", "table"],
            registry=self.registry,
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
        )

        self.db_connection_pool_size = Gauge(
            "db_connection_pool_size",
            "Database connection pool size",
            ["pool_name"],
            registry=self.registry,
        )

        self.db_active_connections = Gauge(
            "db_active_connections",
            "Number of active database connections",
            ["pool_name"],
            registry=self.registry,
        )

        # Cache metrics
        self.cache_operations_total = Counter(
            "cache_operations_total",
            "Total cache operations",
            ["operation", "result"],
            registry=self.registry,
        )

        self.cache_hit_ratio = Gauge(
            "cache_hit_ratio",
            "Cache hit ratio",
            ["cache_name"],
            registry=self.registry,
        )

        self.cache_size_bytes = Gauge(
            "cache_size_bytes",
            "Cache size in bytes",
            ["cache_name"],
            registry=self.registry,
        )

        # Business metrics
        self.tasks_completed_total = Counter(
            "tasks_completed_total",
            "Total tasks completed",
            ["task_type", "project_id"],
            registry=self.registry,
        )

        self.task_completion_duration_seconds = Histogram(
            "task_completion_duration_seconds",
            "Task completion duration in seconds",
            ["task_type"],
            registry=self.registry,
            buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 28800),
        )

        self.user_satisfaction_score = Gauge(
            "user_satisfaction_score",
            "User satisfaction score (1-5)",
            ["project_id"],
            registry=self.registry,
        )

        self.roi_percent = Gauge(
            "roi_percent",
            "Return on investment percentage",
            ["project_id"],
            registry=self.registry,
        )

        # System health metrics
        self.system_cpu_usage_percent = Gauge(
            "system_cpu_usage_percent",
            "System CPU usage percentage",
            registry=self.registry,
        )

        self.system_memory_usage_percent = Gauge(
            "system_memory_usage_percent",
            "System memory usage percentage",
            registry=self.registry,
        )

        self.system_disk_usage_percent = Gauge(
            "system_disk_usage_percent",
            "System disk usage percentage",
            ["mount_point"],
            registry=self.registry,
        )

    # Recording methods
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration_seconds: float,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
    ) -> None:
        """Record HTTP request metrics"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status,
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration_seconds)

        if request_size_bytes:
            self.http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint,
            ).observe(request_size_bytes)

        if response_size_bytes:
            self.http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint,
            ).observe(response_size_bytes)

    def record_agent_execution(
        self,
        agent_name: str,
        task_type: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Record agent execution metrics"""
        self.agent_executions_total.labels(
            agent_name=agent_name,
            task_type=task_type,
            status=status,
        ).inc()

        self.agent_execution_duration_seconds.labels(
            agent_name=agent_name,
            task_type=task_type,
        ).observe(duration_seconds)

    def record_llm_request(
        self,
        provider: str,
        model: str,
        status: str,
        duration_seconds: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record LLM request metrics"""
        self.llm_requests_total.labels(
            provider=provider,
            model=model,
            status=status,
        ).inc()

        self.llm_tokens_total.labels(
            provider=provider,
            model=model,
            token_type="prompt",
        ).inc(prompt_tokens)

        self.llm_tokens_total.labels(
            provider=provider,
            model=model,
            token_type="completion",
        ).inc(completion_tokens)

        self.llm_cost_usd_total.labels(
            provider=provider,
            model=model,
        ).inc(cost_usd)

        self.llm_request_duration_seconds.labels(
            provider=provider,
            model=model,
        ).observe(duration_seconds)

    def record_quality_gate(
        self,
        gate_type: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Record quality gate execution"""
        self.quality_gates_total.labels(
            gate_type=gate_type,
            status=status,
        ).inc()

        self.quality_gate_duration_seconds.labels(
            gate_type=gate_type,
        ).observe(duration_seconds)

    def update_project_metrics(
        self,
        project_id: str,
        cost_usd: Optional[float] = None,
        budget_utilization: Optional[float] = None,
        code_coverage: Optional[float] = None,
        quality_score: Optional[float] = None,
    ) -> None:
        """Update project-level metrics"""
        if cost_usd is not None:
            self.project_cost_usd.labels(project_id=project_id).set(cost_usd)

        if budget_utilization is not None:
            self.budget_utilization_percent.labels(project_id=project_id).set(budget_utilization)

        if code_coverage is not None:
            self.code_coverage_percent.labels(project_id=project_id).set(code_coverage)

        if quality_score is not None:
            self.code_quality_score.labels(project_id=project_id).set(quality_score)

    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format"""
        return generate_latest(self.registry)


# Global metrics instance
prometheus_metrics = PrometheusMetrics()


# FastAPI middleware
async def prometheus_middleware(request: Request, call_next):
    """FastAPI middleware to track request metrics"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Record metrics
    duration = time.time() - start_time
    prometheus_metrics.record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration_seconds=duration,
    )

    return response


# Metrics endpoint
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        content=prometheus_metrics.get_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
