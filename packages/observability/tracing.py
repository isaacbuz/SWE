"""
OpenTelemetry Distributed Tracing Setup
Comprehensive tracing for FastAPI, agents, and external API calls
"""

from typing import Optional, Dict, Any, Callable
from functools import wraps
import time
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import attach, detach


class DistributedTracing:
    """
    Distributed tracing manager with OpenTelemetry

    Features:
    - Automatic instrumentation for FastAPI, HTTP clients
    - Custom span creation for agent executions
    - Trace context propagation across services
    - Multiple exporters (OTLP, Datadog, Console)
    - Performance tracking and bottleneck detection
    """

    def __init__(
        self,
        service_name: str = "swe-platform",
        service_version: str = "1.0.0",
        environment: str = "production",
        otlp_endpoint: Optional[str] = None,
        datadog_enabled: bool = False,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
        self.datadog_enabled = datadog_enabled

        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self.propagator = TraceContextTextMapPropagator()

    def setup(self) -> None:
        """Initialize OpenTelemetry tracing"""
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "deployment.environment": self.environment,
            "service.namespace": "swe-platform",
        })

        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)

        # Add OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
        self.tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Add console exporter for development
        if self.environment == "development":
            console_exporter = ConsoleSpanExporter()
            self.tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        # Auto-instrument HTTP clients
        RequestsInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()

        print(f"✓ Distributed tracing initialized for {self.service_name}")

    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI application"""
        FastAPIInstrumentor.instrument_app(app)
        print("✓ FastAPI instrumented for tracing")

    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    ) -> Span:
        """Create a new span with attributes"""
        span = self.tracer.start_span(
            name=name,
            kind=kind,
            attributes=attributes or {},
        )
        return span

    def trace_agent_execution(
        self,
        agent_name: str,
        task: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Decorator to trace agent execution

        Usage:
            @tracing.trace_agent_execution("QualityLead", "code_review")
            async def review_code(self, code: str):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                attributes = {
                    "agent.name": agent_name,
                    "agent.task": task,
                    "agent.type": "ai_agent",
                }
                if metadata:
                    attributes.update({f"agent.{k}": v for k, v in metadata.items()})

                with self.tracer.start_as_current_span(
                    f"agent.{agent_name}.{task}",
                    kind=trace.SpanKind.INTERNAL,
                    attributes=attributes,
                ) as span:
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("agent.status", "success")
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_attribute("agent.status", "error")
                        span.set_attribute("agent.error", str(e))
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                    finally:
                        duration = time.time() - start_time
                        span.set_attribute("agent.duration_seconds", duration)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                attributes = {
                    "agent.name": agent_name,
                    "agent.task": task,
                    "agent.type": "ai_agent",
                }
                if metadata:
                    attributes.update({f"agent.{k}": v for k, v in metadata.items()})

                with self.tracer.start_as_current_span(
                    f"agent.{agent_name}.{task}",
                    kind=trace.SpanKind.INTERNAL,
                    attributes=attributes,
                ) as span:
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("agent.status", "success")
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_attribute("agent.status", "error")
                        span.set_attribute("agent.error", str(e))
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                    finally:
                        duration = time.time() - start_time
                        span.set_attribute("agent.duration_seconds", duration)

            # Return appropriate wrapper based on function type
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def trace_llm_call(
        self,
        model: str,
        provider: str,
        operation: str = "completion",
    ):
        """
        Decorator to trace LLM API calls

        Usage:
            @tracing.trace_llm_call("gpt-4", "openai")
            async def call_openai(self, prompt: str):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                attributes = {
                    "llm.provider": provider,
                    "llm.model": model,
                    "llm.operation": operation,
                }

                with self.tracer.start_as_current_span(
                    f"llm.{provider}.{operation}",
                    kind=trace.SpanKind.CLIENT,
                    attributes=attributes,
                ) as span:
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)

                        # Extract token usage if available
                        if hasattr(result, "usage"):
                            span.set_attribute("llm.tokens.prompt", result.usage.prompt_tokens)
                            span.set_attribute("llm.tokens.completion", result.usage.completion_tokens)
                            span.set_attribute("llm.tokens.total", result.usage.total_tokens)

                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_attribute("llm.error", str(e))
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                    finally:
                        duration = time.time() - start_time
                        span.set_attribute("llm.duration_seconds", duration)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                attributes = {
                    "llm.provider": provider,
                    "llm.model": model,
                    "llm.operation": operation,
                }

                with self.tracer.start_as_current_span(
                    f"llm.{provider}.{operation}",
                    kind=trace.SpanKind.CLIENT,
                    attributes=attributes,
                ) as span:
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)

                        if hasattr(result, "usage"):
                            span.set_attribute("llm.tokens.prompt", result.usage.prompt_tokens)
                            span.set_attribute("llm.tokens.completion", result.usage.completion_tokens)
                            span.set_attribute("llm.tokens.total", result.usage.total_tokens)

                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_attribute("llm.error", str(e))
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                    finally:
                        duration = time.time() - start_time
                        span.set_attribute("llm.duration_seconds", duration)

            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """Inject trace context into carrier (e.g., HTTP headers)"""
        self.propagator.inject(carrier)

    def extract_context(self, carrier: Dict[str, str]):
        """Extract trace context from carrier"""
        context = self.propagator.extract(carrier)
        token = attach(context)
        return token

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the current span"""
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes or {})

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the current span"""
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute(key, value)

    def shutdown(self) -> None:
        """Shutdown tracing and flush all spans"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            print("✓ Tracing shutdown complete")


# Global tracing instance
tracing = DistributedTracing(
    service_name=os.getenv("SERVICE_NAME", "swe-platform"),
    environment=os.getenv("ENVIRONMENT", "production"),
)


# Convenience decorators
def trace_operation(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Trace any operation"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracing.tracer.start_as_current_span(
                name,
                attributes=attributes or {},
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracing.tracer.start_as_current_span(
                name,
                attributes=attributes or {},
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
