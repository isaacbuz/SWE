/**
 * @ai-company/observability
 * 
 * Observability utilities for metrics, logging, and tracing
 */

export { OpenTelemetryTracer, TracerConfig } from './tracing';
export { trace, Span, SpanKind, SpanStatusCode } from '@opentelemetry/api';
export { PrometheusMetrics, MetricsConfig } from './metrics';
export { Registry, Counter, Histogram, Gauge } from 'prom-client';

