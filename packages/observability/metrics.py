"""
OpenTelemetry Metrics Collection
Comprehensive metrics for latency, costs, success rates, and performance
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import time
import os
from functools import wraps

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from prometheus_client import start_http_server, REGISTRY


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    UP_DOWN_COUNTER = "up_down_counter"


class MetricsCollector:
    """
    Comprehensive metrics collection system

    Features:
    - Request latency (p50, p95, p99)
    - Agent execution time
    - Model invocation costs
    - Success/failure rates
    - Database query performance
    - Cache hit rates
    - Custom business metrics
    """

    def __init__(
        self,
        service_name: str = "swe-platform",
        environment: str = "production",
        otlp_endpoint: Optional[str] = None,
        prometheus_port: int = 9090,
    ):
        self.service_name = service_name
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_METRICS_ENDPOINT", "http://localhost:4318/v1/metrics")
        self.prometheus_port = prometheus_port

        self.meter_provider: Optional[MeterProvider] = None
        self.meter: Optional[metrics.Meter] = None

        # Metric instruments
        self.counters: Dict[str, metrics.Counter] = {}
        self.histograms: Dict[str, metrics.Histogram] = {}
        self.gauges: Dict[str, metrics.ObservableGauge] = {}
        self.up_down_counters: Dict[str, metrics.UpDownCounter] = {}

    def setup(self) -> None:
        """Initialize metrics collection"""
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            "deployment.environment": self.environment,
        })

        # Create Prometheus reader
        prometheus_reader = PrometheusMetricReader()

        # Create OTLP exporter
        otlp_exporter = OTLPMetricExporter(endpoint=self.otlp_endpoint)
        otlp_reader = PeriodicExportingMetricReader(otlp_exporter, export_interval_millis=10000)

        # Create meter provider with multiple readers
        readers = [prometheus_reader, otlp_reader]

        if self.environment == "development":
            console_exporter = ConsoleMetricExporter()
            console_reader = PeriodicExportingMetricReader(console_exporter, export_interval_millis=30000)
            readers.append(console_reader)

        self.meter_provider = MeterProvider(
            resource=resource,
            metric_readers=readers,
        )

        # Set global meter provider
        metrics.set_meter_provider(self.meter_provider)

        # Get meter
        self.meter = metrics.get_meter(__name__)

        # Start Prometheus HTTP server
        start_http_server(self.prometheus_port, registry=REGISTRY)

        # Initialize core metrics
        self._initialize_core_metrics()

        print(f"✓ Metrics collection initialized for {self.service_name}")
        print(f"✓ Prometheus metrics available at http://localhost:{self.prometheus_port}/metrics")

    def _initialize_core_metrics(self) -> None:
        """Initialize core application metrics"""
        # Request metrics
        self.histograms["http_request_duration"] = self.meter.create_histogram(
            name="http.server.request.duration",
            description="HTTP request duration in milliseconds",
            unit="ms",
        )

        self.counters["http_request_total"] = self.meter.create_counter(
            name="http.server.request.total",
            description="Total HTTP requests",
            unit="1",
        )

        self.counters["http_request_errors"] = self.meter.create_counter(
            name="http.server.request.errors",
            description="Total HTTP request errors",
            unit="1",
        )

        # Agent metrics
        self.histograms["agent_execution_duration"] = self.meter.create_histogram(
            name="agent.execution.duration",
            description="Agent execution duration in seconds",
            unit="s",
        )

        self.counters["agent_execution_total"] = self.meter.create_counter(
            name="agent.execution.total",
            description="Total agent executions",
            unit="1",
        )

        self.counters["agent_execution_errors"] = self.meter.create_counter(
            name="agent.execution.errors",
            description="Total agent execution errors",
            unit="1",
        )

        # LLM metrics
        self.histograms["llm_request_duration"] = self.meter.create_histogram(
            name="llm.request.duration",
            description="LLM request duration in seconds",
            unit="s",
        )

        self.counters["llm_tokens_total"] = self.meter.create_counter(
            name="llm.tokens.total",
            description="Total LLM tokens used",
            unit="1",
        )

        self.counters["llm_cost_total"] = self.meter.create_counter(
            name="llm.cost.total",
            description="Total LLM costs in USD",
            unit="USD",
        )

        # Database metrics
        self.histograms["db_query_duration"] = self.meter.create_histogram(
            name="db.query.duration",
            description="Database query duration in milliseconds",
            unit="ms",
        )

        self.counters["db_query_total"] = self.meter.create_counter(
            name="db.query.total",
            description="Total database queries",
            unit="1",
        )

        # Cache metrics
        self.counters["cache_hits"] = self.meter.create_counter(
            name="cache.hits",
            description="Cache hit count",
            unit="1",
        )

        self.counters["cache_misses"] = self.meter.create_counter(
            name="cache.misses",
            description="Cache miss count",
            unit="1",
        )

        # Quality metrics
        self.counters["quality_gate_passed"] = self.meter.create_counter(
            name="quality.gate.passed",
            description="Quality gates passed",
            unit="1",
        )

        self.counters["quality_gate_failed"] = self.meter.create_counter(
            name="quality.gate.failed",
            description="Quality gates failed",
            unit="1",
        )

        # Business metrics
        self.counters["tasks_completed"] = self.meter.create_counter(
            name="tasks.completed",
            description="Tasks completed",
            unit="1",
        )

        self.counters["tasks_failed"] = self.meter.create_counter(
            name="tasks.failed",
            description="Tasks failed",
            unit="1",
        )

    def record_http_request(
        self,
        duration_ms: float,
        method: str,
        path: str,
        status_code: int,
        error: Optional[str] = None,
    ) -> None:
        """Record HTTP request metrics"""
        attributes = {
            "http.method": method,
            "http.route": path,
            "http.status_code": status_code,
        }

        self.histograms["http_request_duration"].record(duration_ms, attributes)
        self.counters["http_request_total"].add(1, attributes)

        if error or status_code >= 400:
            error_attributes = {**attributes, "error.type": error or "http_error"}
            self.counters["http_request_errors"].add(1, error_attributes)

    def record_agent_execution(
        self,
        agent_name: str,
        task: str,
        duration_seconds: float,
        status: str,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
    ) -> None:
        """Record agent execution metrics"""
        attributes = {
            "agent.name": agent_name,
            "agent.task": task,
            "agent.status": status,
        }

        self.histograms["agent_execution_duration"].record(duration_seconds, attributes)
        self.counters["agent_execution_total"].add(1, attributes)

        if status == "error":
            self.counters["agent_execution_errors"].add(1, attributes)

        if tokens_used:
            self.counters["llm_tokens_total"].add(tokens_used, attributes)

        if cost:
            self.counters["llm_cost_total"].add(cost, attributes)

    def record_llm_request(
        self,
        provider: str,
        model: str,
        duration_seconds: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        status: str = "success",
    ) -> None:
        """Record LLM request metrics"""
        attributes = {
            "llm.provider": provider,
            "llm.model": model,
            "llm.status": status,
        }

        self.histograms["llm_request_duration"].record(duration_seconds, attributes)

        token_attributes = {**attributes, "token.type": "prompt"}
        self.counters["llm_tokens_total"].add(prompt_tokens, token_attributes)

        token_attributes["token.type"] = "completion"
        self.counters["llm_tokens_total"].add(completion_tokens, token_attributes)

        self.counters["llm_cost_total"].add(cost, attributes)

    def record_db_query(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        status: str = "success",
    ) -> None:
        """Record database query metrics"""
        attributes = {
            "db.operation": operation,
            "db.table": table,
            "db.status": status,
        }

        self.histograms["db_query_duration"].record(duration_ms, attributes)
        self.counters["db_query_total"].add(1, attributes)

    def record_cache_operation(
        self,
        operation: str,
        hit: bool,
        key_pattern: Optional[str] = None,
    ) -> None:
        """Record cache operation metrics"""
        attributes = {
            "cache.operation": operation,
        }
        if key_pattern:
            attributes["cache.key_pattern"] = key_pattern

        if hit:
            self.counters["cache_hits"].add(1, attributes)
        else:
            self.counters["cache_misses"].add(1, attributes)

    def record_quality_gate(
        self,
        gate_type: str,
        passed: bool,
        project_id: str,
    ) -> None:
        """Record quality gate metrics"""
        attributes = {
            "quality.gate_type": gate_type,
            "project.id": project_id,
        }

        if passed:
            self.counters["quality_gate_passed"].add(1, attributes)
        else:
            self.counters["quality_gate_failed"].add(1, attributes)

    def record_task_completion(
        self,
        task_type: str,
        success: bool,
        duration_seconds: float,
        project_id: str,
    ) -> None:
        """Record task completion metrics"""
        attributes = {
            "task.type": task_type,
            "project.id": project_id,
        }

        if success:
            self.counters["tasks_completed"].add(1, attributes)
        else:
            self.counters["tasks_failed"].add(1, attributes)

    def create_counter(
        self,
        name: str,
        description: str,
        unit: str = "1",
    ) -> metrics.Counter:
        """Create a custom counter metric"""
        if name not in self.counters:
            self.counters[name] = self.meter.create_counter(
                name=name,
                description=description,
                unit=unit,
            )
        return self.counters[name]

    def create_histogram(
        self,
        name: str,
        description: str,
        unit: str = "1",
    ) -> metrics.Histogram:
        """Create a custom histogram metric"""
        if name not in self.histograms:
            self.histograms[name] = self.meter.create_histogram(
                name=name,
                description=description,
                unit=unit,
            )
        return self.histograms[name]

    def measure_duration(self, metric_name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Context manager to measure operation duration

        Usage:
            with metrics.measure_duration("my_operation", {"operation": "process"}):
                # Your code here
                pass
        """
        class DurationMeasurement:
            def __init__(self, collector, metric_name, attributes):
                self.collector = collector
                self.metric_name = metric_name
                self.attributes = attributes or {}
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                if self.metric_name in self.collector.histograms:
                    self.collector.histograms[self.metric_name].record(
                        duration * 1000,  # Convert to ms
                        self.attributes
                    )

        return DurationMeasurement(self, metric_name, attributes)

    def shutdown(self) -> None:
        """Shutdown metrics collection"""
        if self.meter_provider:
            self.meter_provider.shutdown()
            print("✓ Metrics collection shutdown complete")


# Global metrics instance
metrics_collector = MetricsCollector(
    service_name=os.getenv("SERVICE_NAME", "swe-platform"),
    environment=os.getenv("ENVIRONMENT", "production"),
)


# Convenience decorator
def measure_performance(metric_name: str, attributes: Optional[Dict[str, Any]] = None):
    """Decorator to measure function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                attrs = attributes or {}
                attrs["status"] = "success"
                if metric_name in metrics_collector.histograms:
                    metrics_collector.histograms[metric_name].record(duration, attrs)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                attrs = attributes or {}
                attrs["status"] = "error"
                attrs["error"] = str(e)
                if metric_name in metrics_collector.histograms:
                    metrics_collector.histograms[metric_name].record(duration, attrs)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                attrs = attributes or {}
                attrs["status"] = "success"
                if metric_name in metrics_collector.histograms:
                    metrics_collector.histograms[metric_name].record(duration, attrs)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                attrs = attributes or {}
                attrs["status"] = "error"
                attrs["error"] = str(e)
                if metric_name in metrics_collector.histograms:
                    metrics_collector.histograms[metric_name].record(duration, attrs)
                raise

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
