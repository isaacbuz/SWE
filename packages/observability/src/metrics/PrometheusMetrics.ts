/**
 * Prometheus Metrics Collection
 * 
 * Provides Prometheus metrics collection and export capabilities.
 */
import { Registry, Counter, Histogram, Gauge, collectDefaultMetrics } from 'prom-client';
import { OpenTelemetryTracer } from '../tracing/OpenTelemetryTracer';

/**
 * Prometheus Metrics Configuration
 */
export interface MetricsConfig {
  serviceName: string;
  serviceVersion?: string;
  environment?: string;
  enableDefaultMetrics?: boolean;
  prefix?: string;
}

/**
 * Prometheus Metrics Collector
 * 
 * Collects and exports Prometheus metrics for monitoring.
 */
export class PrometheusMetrics {
  private registry: Registry;
  private config: MetricsConfig;

  // Core metrics
  private httpRequestDuration: Histogram<string>;
  private httpRequestTotal: Counter<string>;
  private httpRequestErrors: Counter<string>;
  private llmProviderRequests: Counter<string>;
  private llmProviderLatency: Histogram<string>;
  private llmProviderTokens: Counter<string>;
  private llmProviderCost: Counter<string>;
  private toolExecutions: Counter<string>;
  private toolExecutionDuration: Histogram<string>;
  private activeConnections: Gauge<string>;
  private cacheHits: Counter<string>;
  private cacheMisses: Counter<string>;

  constructor(config: MetricsConfig) {
    this.config = {
      serviceName: config.serviceName,
      serviceVersion: config.serviceVersion || '1.0.0',
      environment: config.environment || 'development',
      enableDefaultMetrics: config.enableDefaultMetrics ?? true,
      prefix: config.prefix || 'swe_platform',
    };

    this.registry = new Registry();

    // Set default labels
    this.registry.setDefaultLabels({
      service: this.config.serviceName,
      version: this.config.serviceVersion,
      environment: this.config.environment,
    });

    // Collect default metrics (CPU, memory, etc.)
    if (this.config.enableDefaultMetrics) {
      collectDefaultMetrics({ register: this.registry });
    }

    // Initialize custom metrics
    this.initializeMetrics();
  }

  /**
   * Initialize custom metrics
   */
  private initializeMetrics(): void {
    // HTTP metrics
    this.httpRequestDuration = new Histogram({
      name: `${this.config.prefix}_http_request_duration_seconds`,
      help: 'HTTP request duration in seconds',
      labelNames: ['method', 'route', 'status_code'],
      buckets: [0.1, 0.5, 1, 2, 5, 10, 30],
      registers: [this.registry],
    });

    this.httpRequestTotal = new Counter({
      name: `${this.config.prefix}_http_requests_total`,
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'route', 'status_code'],
      registers: [this.registry],
    });

    this.httpRequestErrors = new Counter({
      name: `${this.config.prefix}_http_request_errors_total`,
      help: 'Total number of HTTP request errors',
      labelNames: ['method', 'route', 'error_type'],
      registers: [this.registry],
    });

    // LLM Provider metrics
    this.llmProviderRequests = new Counter({
      name: `${this.config.prefix}_llm_provider_requests_total`,
      help: 'Total number of LLM provider requests',
      labelNames: ['provider', 'model', 'status'],
      registers: [this.registry],
    });

    this.llmProviderLatency = new Histogram({
      name: `${this.config.prefix}_llm_provider_latency_seconds`,
      help: 'LLM provider request latency in seconds',
      labelNames: ['provider', 'model'],
      buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60],
      registers: [this.registry],
    });

    this.llmProviderTokens = new Counter({
      name: `${this.config.prefix}_llm_provider_tokens_total`,
      help: 'Total number of tokens processed',
      labelNames: ['provider', 'model', 'type'], // type: prompt, completion
      registers: [this.registry],
    });

    this.llmProviderCost = new Counter({
      name: `${this.config.prefix}_llm_provider_cost_usd_total`,
      help: 'Total cost in USD for LLM provider usage',
      labelNames: ['provider', 'model'],
      registers: [this.registry],
    });

    // Tool execution metrics
    this.toolExecutions = new Counter({
      name: `${this.config.prefix}_tool_executions_total`,
      help: 'Total number of tool executions',
      labelNames: ['tool_name', 'status'],
      registers: [this.registry],
    });

    this.toolExecutionDuration = new Histogram({
      name: `${this.config.prefix}_tool_execution_duration_seconds`,
      help: 'Tool execution duration in seconds',
      labelNames: ['tool_name'],
      buckets: [0.1, 0.5, 1, 2, 5, 10, 30],
      registers: [this.registry],
    });

    // Connection metrics
    this.activeConnections = new Gauge({
      name: `${this.config.prefix}_active_connections`,
      help: 'Number of active connections',
      labelNames: ['type'], // type: websocket, http, db
      registers: [this.registry],
    });

    // Cache metrics
    this.cacheHits = new Counter({
      name: `${this.config.prefix}_cache_hits_total`,
      help: 'Total number of cache hits',
      labelNames: ['cache_type'],
      registers: [this.registry],
    });

    this.cacheMisses = new Counter({
      name: `${this.config.prefix}_cache_misses_total`,
      help: 'Total number of cache misses',
      labelNames: ['cache_type'],
      registers: [this.registry],
    });
  }

  /**
   * Record HTTP request metrics
   */
  recordHttpRequest(
    method: string,
    route: string,
    statusCode: number,
    durationSeconds: number
  ): void {
    this.httpRequestDuration.observe(
      { method, route, status_code: statusCode.toString() },
      durationSeconds
    );
    this.httpRequestTotal.inc({ method, route, status_code: statusCode.toString() });

    if (statusCode >= 400) {
      this.httpRequestErrors.inc({
        method,
        route,
        error_type: statusCode >= 500 ? 'server_error' : 'client_error',
      });
    }
  }

  /**
   * Record LLM provider request metrics
   */
  recordLLMRequest(
    provider: string,
    model: string,
    status: 'success' | 'error',
    latencySeconds: number,
    promptTokens?: number,
    completionTokens?: number,
    costUSD?: number
  ): void {
    this.llmProviderRequests.inc({ provider, model, status });
    this.llmProviderLatency.observe({ provider, model }, latencySeconds);

    if (promptTokens) {
      this.llmProviderTokens.inc({ provider, model, type: 'prompt' }, promptTokens);
    }

    if (completionTokens) {
      this.llmProviderTokens.inc({ provider, model, type: 'completion' }, completionTokens);
    }

    if (costUSD) {
      this.llmProviderCost.inc({ provider, model }, costUSD);
    }
  }

  /**
   * Record tool execution metrics
   */
  recordToolExecution(
    toolName: string,
    status: 'success' | 'error',
    durationSeconds: number
  ): void {
    this.toolExecutions.inc({ tool_name: toolName, status });
    this.toolExecutionDuration.observe({ tool_name: toolName }, durationSeconds);
  }

  /**
   * Update active connections gauge
   */
  updateActiveConnections(type: string, count: number): void {
    this.activeConnections.set({ type }, count);
  }

  /**
   * Record cache hit
   */
  recordCacheHit(cacheType: string): void {
    this.cacheHits.inc({ cache_type: cacheType });
  }

  /**
   * Record cache miss
   */
  recordCacheMiss(cacheType: string): void {
    this.cacheMisses.inc({ cache_type: cacheType });
  }

  /**
   * Get metrics as Prometheus format string
   */
  async getMetrics(): Promise<string> {
    return this.registry.metrics();
  }

  /**
   * Get registry for custom metrics
   */
  getRegistry(): Registry {
    return this.registry;
  }

  /**
   * Reset all metrics (useful for testing)
   */
  reset(): void {
    this.registry.resetMetrics();
    this.initializeMetrics();
  }
}

