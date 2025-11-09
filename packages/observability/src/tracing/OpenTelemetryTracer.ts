/**
 * OpenTelemetry Distributed Tracing
 * 
 * Provides distributed tracing capabilities using OpenTelemetry.
 */
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { OTLPTraceExporter } from '@opentelemetry/exporter-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { trace, Span, SpanKind, SpanStatusCode, context, propagation } from '@opentelemetry/api';

/**
 * OpenTelemetry Tracer Configuration
 */
export interface TracerConfig {
  serviceName: string;
  serviceVersion?: string;
  environment?: string;
  otlpEndpoint?: string;
  otlpHeaders?: Record<string, string>;
  enableAutoInstrumentation?: boolean;
  sampleRate?: number; // 0.0 to 1.0
}

/**
 * OpenTelemetry Tracer
 * 
 * Manages distributed tracing for the application.
 */
export class OpenTelemetryTracer {
  private sdk: NodeSDK | null = null;
  private initialized = false;

  constructor(private config: TracerConfig) {
    this.config = {
      serviceName: config.serviceName,
      serviceVersion: config.serviceVersion || '1.0.0',
      environment: config.environment || 'development',
      otlpEndpoint: config.otlpEndpoint || process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318',
      otlpHeaders: config.otlpHeaders || {},
      enableAutoInstrumentation: config.enableAutoInstrumentation ?? true,
      sampleRate: config.sampleRate ?? 1.0,
    };
  }

  /**
   * Initialize OpenTelemetry SDK
   */
  initialize(): void {
    if (this.initialized) {
      return;
    }

    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: this.config.serviceName,
      [SemanticResourceAttributes.SERVICE_VERSION]: this.config.serviceVersion,
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: this.config.environment,
    });

    const traceExporter = new OTLPTraceExporter({
      url: `${this.config.otlpEndpoint}/v1/traces`,
      headers: this.config.otlpHeaders,
    });

    const spanProcessor = new BatchSpanProcessor(traceExporter, {
      maxQueueSize: 2048,
      maxExportBatchSize: 512,
      scheduledDelayMillis: 5000,
      exportTimeoutMillis: 30000,
    });

    const instrumentations = this.config.enableAutoInstrumentation
      ? [getNodeAutoInstrumentations()]
      : [];

    this.sdk = new NodeSDK({
      resource,
      traceExporter,
      spanProcessor,
      instrumentations,
      sampler: {
        shouldSample: () => {
          return Math.random() < this.config.sampleRate!
            ? { decision: 1 } // RECORD_AND_SAMPLE
            : { decision: 0 }; // DROP
        },
      },
    });

    this.sdk.start();
    this.initialized = true;
  }

  /**
   * Shutdown tracer
   */
  async shutdown(): Promise<void> {
    if (this.sdk) {
      await this.sdk.shutdown();
      this.initialized = false;
    }
  }

  /**
   * Get tracer instance
   */
  getTracer(name?: string, version?: string) {
    return trace.getTracer(name || this.config.serviceName, version || this.config.serviceVersion);
  }

  /**
   * Start a new span
   */
  startSpan(name: string, options?: {
    kind?: SpanKind;
    attributes?: Record<string, string | number | boolean>;
    parent?: Span;
  }): Span {
    const tracer = this.getTracer();
    const spanOptions: any = {
      kind: options?.kind || SpanKind.INTERNAL,
      attributes: options?.attributes || {},
    };

    if (options?.parent) {
      spanOptions.parent = options.parent;
    }

    return tracer.startSpan(name, spanOptions);
  }

  /**
   * Execute function within a span
   */
  async trace<T>(
    name: string,
    fn: (span: Span) => Promise<T>,
    options?: {
      kind?: SpanKind;
      attributes?: Record<string, string | number | boolean>;
    }
  ): Promise<T> {
    const tracer = this.getTracer();
    const span = tracer.startSpan(name, {
      kind: options?.kind || SpanKind.INTERNAL,
      attributes: options?.attributes || {},
    });

    try {
      const result = await fn(span);
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  }

  /**
   * Add event to current span
   */
  addEvent(name: string, attributes?: Record<string, string | number | boolean>): void {
    const activeSpan = trace.getActiveSpan();
    if (activeSpan) {
      activeSpan.addEvent(name, attributes);
    }
  }

  /**
   * Set attribute on current span
   */
  setAttribute(key: string, value: string | number | boolean): void {
    const activeSpan = trace.getActiveSpan();
    if (activeSpan) {
      activeSpan.setAttribute(key, value);
    }
  }

  /**
   * Inject trace context into headers for propagation
   */
  injectHeaders(headers: Record<string, string>): Record<string, string> {
    const carrier: Record<string, string> = { ...headers };
    propagation.inject(context.active(), carrier);
    return carrier;
  }

  /**
   * Extract trace context from headers
   */
  extractContext(headers: Record<string, string>): any {
    return propagation.extract(context.active(), headers);
  }
}

