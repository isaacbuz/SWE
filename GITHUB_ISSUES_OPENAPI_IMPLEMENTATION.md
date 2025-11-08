# GitHub Issues: OpenAPI & OpenAI Implementation Plan

This document contains GitHub issues for implementing OpenAPI specifications and OpenAI as an LLM provider in the AI Company MoE architecture.

---

## Epic: OpenAPI Tooling Infrastructure

**Epic Description:**
Implement OpenAPI as the universal contract for exposing tools to agents and wrapping external APIs. This provides type-safe, validated tool calling across all LLM providers and enables seamless integration with external services (GitHub, GSA APIs, etc.).

---

### Issue #1: Create OpenAPI Tool Registry Foundation

**Labels:** `enhancement`, `infrastructure`, `openapi`, `priority:high`

**Title:** Implement OpenAPI Tool Registry and Schema Loader

**Description:**

Create the foundational infrastructure for managing OpenAPI tool specifications that will be used by all LLM providers in the MoE system.

**Acceptance Criteria:**
- [ ] Create `packages/openapi-tools` package in the monorepo
- [ ] Implement OpenAPI schema loader that can read and parse OpenAPI 3.1.0 specs
- [ ] Create a tool registry that maintains all available tools from OpenAPI specs
- [ ] Support loading multiple OpenAPI spec files and merging them into a unified registry
- [ ] Add validation using `openapi3-ts` or similar library
- [ ] Include TypeScript types for `ToolSpec` interface:
  ```typescript
  interface ToolSpec {
    name: string;
    description: string;
    jsonSchema: object; // JSON Schema for parameters
    operationId: string;
    endpoint?: string;
  }
  ```

**Technical Details:**
```typescript
// packages/openapi-tools/src/registry/ToolRegistry.ts
export class ToolRegistry {
  async loadSpecs(paths: string[]): Promise<void>
  getToolSpecs(): ToolSpec[]
  getToolByName(name: string): ToolSpec | undefined
}
```

**Dependencies:** None

**Estimated Effort:** 3-5 days

---

### Issue #2: Build OpenAPI to Tool Spec Converter

**Labels:** `enhancement`, `openapi`, `priority:high`

**Title:** Convert OpenAPI Operations to LLM Tool Specifications

**Description:**

Create a converter that transforms OpenAPI operation definitions into tool specifications compatible with OpenAI, Anthropic, and other LLM providers.

**Acceptance Criteria:**
- [ ] Implement `openApiToToolSpecs()` function that converts OpenAPI paths to tool specs
- [ ] Extract operation metadata (operationId, summary, description)
- [ ] Convert requestBody schemas to JSON Schema format for tool parameters
- [ ] Handle different parameter types (path, query, body)
- [ ] Generate clear, LLM-friendly descriptions from OpenAPI documentation
- [ ] Support both OpenAPI 3.0 and 3.1 formats
- [ ] Add comprehensive unit tests with sample OpenAPI specs

**Technical Details:**
```typescript
// packages/openapi-tools/src/converters/openApiToToolSpecs.ts
export function openApiToToolSpecs(doc: OpenAPIObject): ToolSpec[] {
  // Walk operations, map to {name, description, jsonSchema}
  // Extract requestBody schema as the function parameters
  // Return list for providers that support tool/function-calling
}
```

**Dependencies:** Issue #1

**Estimated Effort:** 3-4 days

---

### Issue #3: Implement Tool Executor with Schema Validation

**Labels:** `enhancement`, `openapi`, `security`, `priority:high`

**Title:** Create Tool Executor with Runtime Schema Validation

**Description:**

Build a secure tool executor that validates inputs against JSON Schema before execution and routes to registered tool implementations.

**Acceptance Criteria:**
- [ ] Create `ToolExecutor` class that manages tool execution
- [ ] Integrate Ajv or Zod for runtime JSON Schema validation
- [ ] Implement tool registration system with type-safe handlers
- [ ] Add input sanitization and validation before execution
- [ ] Implement error handling with detailed validation errors
- [ ] Add execution logging (inputs, outputs, duration)
- [ ] Include circuit breaker for failing tools
- [ ] Add rate limiting per tool

**Technical Details:**
```typescript
// packages/openapi-tools/src/executor/ToolExecutor.ts
export class ToolExecutor {
  constructor(
    private registry: Map<string, ToolHandler>,
    private validator: SchemaValidator
  ) {}

  async execute(
    toolName: string,
    args: unknown,
    schema: object
  ): Promise<ToolResult> {
    // 1. Validate args against JSON Schema
    // 2. Rate limit check
    // 3. Execute registered handler
    // 4. Log execution metrics
    // 5. Return typed result
  }
}
```

**Security Considerations:**
- Never expose internal credentials to LLMs
- Validate all inputs against strict schemas
- Implement allowlist for permitted operations
- Add audit logging for all tool executions

**Dependencies:** Issue #2

**Estimated Effort:** 4-5 days

---

### Issue #4: Create Internal Tools OpenAPI Specification

**Labels:** `enhancement`, `openapi`, `documentation`, `priority:medium`

**Title:** Define OpenAPI Spec for Internal AI Dev Team Tools

**Description:**

Create comprehensive OpenAPI specification for internal tools that agents can use (GitHub operations, code analysis, testing, etc.).

**Acceptance Criteria:**
- [ ] Create `tools/openapi/ai-dev-tools.yaml` with OpenAPI 3.1.0 spec
- [ ] Define GitHub operations:
  - `createIssues` - Create multiple issues from spec
  - `createPR` - Create pull request
  - `reviewPR` - Analyze and review PR
  - `updateIssue` - Update issue status/labels
- [ ] Define code operations:
  - `analyzeCode` - Run static analysis
  - `generateTests` - Generate test cases
  - `refactorCode` - Apply refactoring
- [ ] Define CI/CD operations:
  - `runTests` - Execute test suite
  - `deployPreview` - Create preview deployment
  - `createWorkflow` - Generate GitHub Actions workflow
- [ ] Include detailed descriptions, examples, and parameter constraints
- [ ] Add JSON Schema validation rules for all inputs

**Example Structure:**
```yaml
openapi: 3.1.0
info:
  title: AI Dev Team Tools
  version: 1.0.0
  description: Tools available to AI agents for software development tasks

paths:
  /github/create-issues:
    post:
      operationId: createIssues
      summary: Create multiple GitHub issues from a specification
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [owner, repo, tasks]
              properties:
                owner: { type: string, description: "GitHub repository owner" }
                repo: { type: string, description: "Repository name" }
                tasks:
                  type: array
                  items:
                    type: object
                    required: [title, body]
                    properties:
                      title: { type: string }
                      body: { type: string }
                      labels: { type: array, items: { type: string } }
                      assignees: { type: array, items: { type: string } }
```

**Dependencies:** Issue #2

**Estimated Effort:** 3-4 days

---

### Issue #5: Build External API Wrappers (GitHub, GSA)

**Labels:** `enhancement`, `integration`, `openapi`, `priority:medium`

**Title:** Create OpenAPI Wrappers for External APIs

**Description:**

Build secure wrappers around external APIs (GitHub, Open GSA, etc.) that expose them as OpenAPI tools with credential management and rate limiting.

**Acceptance Criteria:**
- [ ] Create `packages/external-api-tools` package
- [ ] Implement GitHub API wrapper:
  - Issues CRUD operations
  - PR creation and management
  - Repository operations
  - Workflow management
- [ ] Implement Open GSA API wrapper:
  - SAM.gov entity search
  - Contract opportunities
  - Federal hierarchy data
- [ ] Add credential management (read from secure vault, never expose to LLMs)
- [ ] Implement rate limiting per API (respect API quotas)
- [ ] Add response caching where appropriate
- [ ] Include retry logic with exponential backoff
- [ ] Generate OpenAPI specs for each wrapper

**Technical Details:**
```typescript
// packages/external-api-tools/src/github/GitHubToolWrapper.ts
export class GitHubToolWrapper {
  constructor(
    private credentials: CredentialVault,
    private rateLimiter: RateLimiter
  ) {}

  async createIssues(args: CreateIssuesArgs): Promise<CreateIssuesResult> {
    // 1. Validate args (already done by ToolExecutor)
    // 2. Get credentials from vault
    // 3. Check rate limit
    // 4. Call GitHub API
    // 5. Normalize response
    // 6. Return result (never include credentials)
  }
}
```

**Security Requirements:**
- Credentials stored in environment variables or secret manager
- No credentials in logs or responses
- Input sanitization for all user-provided data
- Scope tokens to minimum required permissions

**Dependencies:** Issue #3

**Estimated Effort:** 5-7 days

---

## Epic: OpenAI Provider Integration

**Epic Description:**
Add OpenAI as a first-class LLM provider in the MoE router, enabling access to GPT-4 and future models with structured tool calling capabilities.

---

### Issue #6: Define Provider-Agnostic LLM Interface

**Labels:** `enhancement`, `architecture`, `llm`, `priority:high`

**Title:** Create Abstract LLM Provider Interface

**Description:**

Define a provider-agnostic interface that all LLM providers (OpenAI, Anthropic, etc.) must implement, enabling the MoE router to work with any provider.

**Acceptance Criteria:**
- [ ] Create `packages/llm-providers` package
- [ ] Define `LLMProvider` interface with standard methods
- [ ] Support streaming and non-streaming completions
- [ ] Include tool/function calling support
- [ ] Add provider metadata (name, context limits, pricing)
- [ ] Define standard message format
- [ ] Include TypeScript types for all interfaces
- [ ] Add provider capability flags (supports tools, supports vision, etc.)

**Technical Details:**
```typescript
// packages/llm-providers/src/domain/LLMProvider.ts
export interface LLMProvider {
  name: string;
  maxContext: number;
  pricePerMTokIn: number;
  pricePerMTokOut: number;
  capabilities: {
    tools: boolean;
    vision: boolean;
    streaming: boolean;
    jsonMode: boolean;
  };

  completion(opts: CompletionOptions): Promise<CompletionResult>;
  streamCompletion(opts: CompletionOptions): AsyncIterable<CompletionChunk>;
}

export interface CompletionOptions {
  system?: string;
  messages: Message[];
  tools?: ToolSpec[];
  temperature?: number;
  maxTokens?: number;
  responseFormat?: "text" | "json_object";
}

export interface Message {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  toolCalls?: ToolCall[];
}
```

**Dependencies:** None

**Estimated Effort:** 2-3 days

---

### Issue #7: Implement OpenAI Provider

**Labels:** `enhancement`, `llm`, `openai`, `priority:high`

**Title:** Build OpenAI Provider Implementation

**Description:**

Create a concrete implementation of the LLMProvider interface for OpenAI's API, supporting GPT-4 and future models.

**Acceptance Criteria:**
- [ ] Implement `OpenAIProvider` class conforming to `LLMProvider` interface
- [ ] Support GPT-4, GPT-4 Turbo, and configurable model selection
- [ ] Implement tool/function calling with OpenAI's format
- [ ] Support streaming responses
- [ ] Handle rate limiting and retries
- [ ] Add proper error handling with typed errors
- [ ] Include cost tracking (token usage)
- [ ] Support JSON mode for structured outputs
- [ ] Add comprehensive tests with mocked API responses

**Technical Details:**
```typescript
// packages/llm-providers/src/providers/openai/OpenAIProvider.ts
import OpenAI from "openai";
import { LLMProvider, CompletionOptions, CompletionResult } from "../../domain/LLMProvider";

export class OpenAIProvider implements LLMProvider {
  name = "openai:gpt-4";
  maxContext = 128_000;
  pricePerMTokIn = 10.0;
  pricePerMTokOut = 30.0;
  capabilities = {
    tools: true,
    vision: true,
    streaming: true,
    jsonMode: true
  };

  private client: OpenAI;
  private model: string;

  constructor(apiKey: string, model = "gpt-4-turbo-preview") {
    this.client = new OpenAI({ apiKey });
    this.model = model;
  }

  async completion(opts: CompletionOptions): Promise<CompletionResult> {
    // Convert ToolSpec[] to OpenAI function format
    // Call OpenAI API
    // Parse tool calls from response
    // Return normalized result
  }

  async *streamCompletion(opts: CompletionOptions): AsyncIterable<CompletionChunk> {
    // Streaming implementation
  }
}
```

**Dependencies:** Issue #6

**Estimated Effort:** 4-5 days

---

### Issue #8: Implement Anthropic (Claude) Provider

**Labels:** `enhancement`, `llm`, `anthropic`, `priority:high`

**Title:** Build Anthropic Provider Implementation

**Description:**

Create Anthropic/Claude provider implementation for comparison and fallback in the MoE system.

**Acceptance Criteria:**
- [ ] Implement `AnthropicProvider` class conforming to `LLMProvider` interface
- [ ] Support Claude 3 models (Opus, Sonnet, Haiku)
- [ ] Implement tool use with Anthropic's format
- [ ] Support streaming responses
- [ ] Handle rate limiting and retries
- [ ] Add cost tracking
- [ ] Include comprehensive tests

**Technical Details:**
Similar structure to OpenAI provider but using Anthropic's SDK and message format.

**Dependencies:** Issue #6

**Estimated Effort:** 4-5 days

---

### Issue #9: Build MoE Router with Provider Selection

**Labels:** `enhancement`, `architecture`, `moe`, `priority:high`

**Title:** Implement Mixture-of-Experts Router for Provider Selection

**Description:**

Create an intelligent router that selects the best LLM provider for each task based on cost, latency, capabilities, and historical performance.

**Acceptance Criteria:**
- [ ] Create `packages/moe-router` package
- [ ] Implement scoring algorithm for provider selection
- [ ] Add task classification (code generation, analysis, planning, etc.)
- [ ] Include cost optimization logic
- [ ] Support provider fallback on failures
- [ ] Add A/B testing capabilities
- [ ] Implement provider health tracking
- [ ] Include metrics collection (latency, success rate, cost)
- [ ] Add configuration for routing policies
- [ ] Support manual provider override

**Routing Logic:**
```typescript
// packages/moe-router/src/Router.ts
export interface RoutingPolicy {
  taskType: TaskType;
  preferredProviders: string[];
  costWeight: number;
  latencyWeight: number;
  qualityWeight: number;
  maxCostPerRequest: number;
}

export class MoERouter {
  async selectProvider(
    task: Task,
    availableProviders: LLMProvider[]
  ): Promise<LLMProvider> {
    // 1. Classify task type
    // 2. Score each provider
    // 3. Apply routing policy
    // 4. Check provider health
    // 5. Return best provider
  }
}
```

**Scoring Factors:**
- Task type match (e.g., code tasks → prefer models strong at coding)
- Cost per token
- Expected latency
- Historical success rate for similar tasks
- Context length requirements
- Tool calling requirements
- Current provider health/availability

**Dependencies:** Issues #7, #8

**Estimated Effort:** 5-7 days

---

### Issue #10: Add Provider Performance Tracking

**Labels:** `enhancement`, `observability`, `metrics`, `priority:medium`

**Title:** Implement Provider Performance Metrics and Analytics

**Description:**

Build comprehensive observability for tracking LLM provider performance, costs, and quality metrics.

**Acceptance Criteria:**
- [ ] Extend `packages/observability` with provider-specific metrics
- [ ] Track per-provider metrics:
  - Token usage (input/output)
  - Cost per request and cumulative
  - Latency (p50, p95, p99)
  - Success/failure rates
  - Tool calling success rates
- [ ] Add per-task-type breakdowns
- [ ] Implement win-rate tracking (which provider performs best)
- [ ] Create cost/performance curves for optimization
- [ ] Add alerting for anomalies (high costs, high latency)
- [ ] Build dashboard views for metrics
- [ ] Support export to external monitoring (Prometheus, Datadog)

**Technical Details:**
```typescript
// packages/observability/src/providers/ProviderMetrics.ts
export interface ProviderExecutionMetric {
  providerId: string;
  taskType: string;
  tokensIn: number;
  tokensOut: number;
  cost: number;
  latencyMs: number;
  success: boolean;
  toolCallsCount: number;
  timestamp: Date;
}

export class ProviderMetricsCollector {
  recordExecution(metric: ProviderExecutionMetric): void
  getProviderStats(providerId: string, timeRange: TimeRange): ProviderStats
  getWinRates(taskType: string): Map<string, number>
}
```

**Dependencies:** Issue #9

**Estimated Effort:** 4-5 days

---

## Epic: Tool Calling Integration

**Epic Description:**
Integrate OpenAPI tools with LLM providers to enable agents to call internal and external tools safely and effectively.

---

### Issue #11: Implement Tool Calling Pipeline

**Labels:** `enhancement`, `integration`, `tools`, `priority:high`

**Title:** Build End-to-End Tool Calling Pipeline

**Description:**

Create the complete pipeline for LLMs to discover, call, and execute tools defined in OpenAPI specifications.

**Acceptance Criteria:**
- [ ] Create `packages/tool-pipeline` package
- [ ] Implement tool discovery from OpenAPI registry
- [ ] Convert tool specs to provider-specific formats (OpenAI vs Anthropic)
- [ ] Handle tool call parsing from LLM responses
- [ ] Execute tools via ToolExecutor
- [ ] Format tool results for LLM consumption
- [ ] Support multi-turn tool calling (tool → LLM → tool loops)
- [ ] Add tool call validation and safety checks
- [ ] Implement tool call retries on failures
- [ ] Add comprehensive logging and tracing

**Technical Details:**
```typescript
// packages/tool-pipeline/src/ToolCallingPipeline.ts
export class ToolCallingPipeline {
  constructor(
    private toolRegistry: ToolRegistry,
    private toolExecutor: ToolExecutor,
    private provider: LLMProvider
  ) {}

  async executeWithTools(
    prompt: string,
    availableTools: string[],
    maxTurns = 5
  ): Promise<PipelineResult> {
    // 1. Get tool specs from registry
    // 2. Send to LLM with tools
    // 3. Parse tool calls from response
    // 4. Execute tools
    // 5. Send results back to LLM
    // 6. Repeat until done or max turns
    // 7. Return final result
  }
}
```

**Dependencies:** Issues #3, #7

**Estimated Effort:** 5-6 days

---

### Issue #12: Create Sample Pipeline: Spec to GitHub Issues

**Labels:** `enhancement`, `example`, `integration`, `priority:medium`

**Title:** Build Example Pipeline: Convert Spec to GitHub Issues Using Tools

**Description:**

Create a complete example pipeline that demonstrates the full system: taking a specification document and using LLM + tools to create structured GitHub issues.

**Acceptance Criteria:**
- [ ] Create `apps/cli-tools` or extend existing CLI
- [ ] Implement `spec-to-github` command
- [ ] Parse input specification (markdown, text)
- [ ] Use MoE router to select provider
- [ ] Provide GitHub tools to LLM
- [ ] Let LLM break down spec into tasks
- [ ] Execute `createIssues` tool
- [ ] Return created issue numbers
- [ ] Add detailed logging of each step
- [ ] Include example spec files for testing
- [ ] Write documentation and tutorial

**Example Usage:**
```bash
pnpm run spec-to-github \
  --spec ./examples/feature-spec.md \
  --owner isaacbuz \
  --repo my-app \
  --provider openai
```

**Technical Details:**
```typescript
// apps/cli-tools/src/commands/specToGithub.ts
export async function specToGithub(options: SpecToGithubOptions) {
  // 1. Load spec file
  // 2. Initialize MoE router
  // 3. Get tool specs for GitHub operations
  // 4. Create pipeline with selected provider
  // 5. Execute with tools
  // 6. Parse and display results
}
```

**Dependencies:** Issues #9, #11

**Estimated Effort:** 3-4 days

---

## Epic: Frontend Integration

**Epic Description:**
Integrate OpenAPI tools and multiple LLM providers into the frontend UI, giving users visibility and control over the MoE system.

---

### Issue #13: Build Command Palette with OpenAPI Tools

**Labels:** `enhancement`, `frontend`, `ui`, `priority:medium`

**Title:** Extend Command Palette to Show Available OpenAPI Tools

**Description:**

Enhance the command palette in the web UI to dynamically display all available tools from the OpenAPI registry as executable actions.

**Acceptance Criteria:**
- [ ] Extend `apps/web` command palette component
- [ ] Load available tools from OpenAPI registry
- [ ] Display tools grouped by category (GitHub, Code, CI/CD, External)
- [ ] Show tool descriptions and parameters in search
- [ ] Implement tool execution from palette
- [ ] Show parameter input forms for selected tools
- [ ] Display execution progress and results
- [ ] Add keyboard shortcuts for common tools
- [ ] Include search/filter by tool name and description

**UI Design:**
```
Command Palette:
  > /create-issues
  > /create-pr
  > /analyze-code
  > /run-tests
  > /gov-search-grants (from Open GSA)
  > /deploy-preview
```

**Dependencies:** Issue #4

**Estimated Effort:** 4-5 days

---

### Issue #14: Create AI Dock with Provider Visibility

**Labels:** `enhancement`, `frontend`, `ui`, `observability`, `priority:medium`

**Title:** Build AI Dock Component for Provider Selection and Execution Trace

**Description:**

Create a new "AI Dock" UI component that shows which provider handled each request, tool calls made, and allows provider switching.

**Acceptance Criteria:**
- [ ] Create new dock component in `apps/web`
- [ ] Display current/last provider used
- [ ] Show provider selection UI (manual override)
- [ ] Display tool call trace:
  - Which tools were called
  - Input parameters (sanitized)
  - Results summary
  - Execution time
- [ ] Add "re-run with different provider" button
- [ ] Show token usage and cost per request
- [ ] Include provider health indicators
- [ ] Add collapsible detail views
- [ ] Support dark/light themes

**UI Layout:**
```
AI Dock:
┌─────────────────────────────────┐
│ Provider: OpenAI GPT-4          │
│ [Switch Provider ▼]             │
├─────────────────────────────────┤
│ Tool Calls (3):                 │
│   1. analyzeCode                │
│      Duration: 1.2s             │
│   2. createIssues (5 issues)    │
│      Duration: 0.8s             │
│   3. createPR                   │
│      Duration: 1.5s             │
├─────────────────────────────────┤
│ Tokens: 2,450 in / 1,200 out   │
│ Cost: $0.042                    │
│ [Re-run with Claude ▶]          │
└─────────────────────────────────┘
```

**Dependencies:** Issue #10

**Estimated Effort:** 5-6 days

---

### Issue #15: Add Integrations Management Page

**Labels:** `enhancement`, `frontend`, `ui`, `priority:low`

**Title:** Create Integrations Page for API Credentials and Tool Health

**Description:**

Build a settings page where users can manage API credentials, view tool health, and configure tool permissions.

**Acceptance Criteria:**
- [ ] Create integrations page in `apps/web`
- [ ] Add credential management UI (encrypted storage)
- [ ] Show health status for each external API
- [ ] Display rate limit status
- [ ] Allow enabling/disabling specific tools
- [ ] Show tool usage statistics
- [ ] Include connection testing
- [ ] Add credential validation

**Dependencies:** Issue #5

**Estimated Effort:** 4-5 days

---

## Epic: Security & Compliance

**Epic Description:**
Implement security controls, audit logging, and compliance features for safe LLM and tool usage.

---

### Issue #16: Implement Tool Execution Audit Logging

**Labels:** `security`, `compliance`, `audit`, `priority:high`

**Title:** Build Comprehensive Audit Log for All Tool Executions

**Description:**

Create detailed audit logging for every tool execution to support compliance, debugging, and security analysis.

**Acceptance Criteria:**
- [ ] Extend `packages/observability` with audit logging
- [ ] Log all tool executions with:
  - Timestamp
  - User/agent identity
  - Tool name and operation
  - Input parameters (sanitized, no secrets)
  - Output summary
  - Success/failure status
  - Provider used
  - Cost incurred
- [ ] Implement log retention policies
- [ ] Add PII detection and redaction
- [ ] Support log export (JSON, CSV)
- [ ] Include search and filter capabilities
- [ ] Add alerting for suspicious patterns
- [ ] Ensure logs are tamper-evident

**Technical Details:**
```typescript
// packages/observability/src/audit/AuditLogger.ts
export interface AuditLogEntry {
  id: string;
  timestamp: Date;
  userId: string;
  agentId?: string;
  toolName: string;
  operation: string;
  inputs: Record<string, unknown>; // sanitized
  outputs: unknown; // sanitized
  success: boolean;
  error?: string;
  providerId: string;
  cost: number;
  durationMs: number;
}

export class AuditLogger {
  logToolExecution(entry: AuditLogEntry): Promise<void>
  query(filter: AuditFilter): Promise<AuditLogEntry[]>
  export(format: "json" | "csv", filter: AuditFilter): Promise<Buffer>
}
```

**Dependencies:** Issue #3

**Estimated Effort:** 4-5 days

---

### Issue #17: Add Tool Permission System

**Labels:** `security`, `permissions`, `priority:high`

**Title:** Implement Fine-Grained Permission System for Tool Access

**Description:**

Create a permission system that controls which users/agents can execute which tools, with role-based access control.

**Acceptance Criteria:**
- [ ] Define permission model (roles, users, tools)
- [ ] Implement permission checking in ToolExecutor
- [ ] Add role definitions (admin, developer, agent, readonly)
- [ ] Support per-tool permissions
- [ ] Include per-user overrides
- [ ] Add permission inheritance
- [ ] Implement audit logging for permission changes
- [ ] Create UI for permission management
- [ ] Add permission testing utilities

**Permission Examples:**
- Admin: Can execute all tools
- Developer: Can execute code and GitHub tools, but not deployment tools
- Agent: Limited to read-only tools and approved write operations
- CEO/Manager: Can execute high-level orchestration tools

**Dependencies:** Issue #16

**Estimated Effort:** 5-6 days

---

### Issue #18: Implement Rate Limiting and Quotas

**Labels:** `security`, `infrastructure`, `priority:medium`

**Title:** Add Rate Limiting and Cost Quotas for Tools and Providers

**Description:**

Implement rate limiting to prevent abuse and cost quotas to control LLM spending.

**Acceptance Criteria:**
- [ ] Create rate limiting middleware for tool execution
- [ ] Implement per-user rate limits
- [ ] Add per-tool rate limits (respect external API quotas)
- [ ] Implement cost quotas per user/team
- [ ] Add real-time cost tracking
- [ ] Include quota exhaustion alerts
- [ ] Support quota resets (daily, monthly)
- [ ] Create quota management UI
- [ ] Add override capabilities for admins

**Technical Details:**
```typescript
// packages/openapi-tools/src/ratelimit/RateLimiter.ts
export interface RateLimit {
  maxRequests: number;
  windowMs: number;
  per: "user" | "tool" | "global";
}

export interface CostQuota {
  maxCostPerDay: number;
  maxCostPerMonth: number;
  userId?: string;
}

export class RateLimiter {
  checkLimit(userId: string, toolName: string): Promise<boolean>
  checkQuota(userId: string, estimatedCost: number): Promise<boolean>
}
```

**Dependencies:** Issue #10

**Estimated Effort:** 4-5 days

---

## Epic: Testing & Documentation

**Epic Description:**
Comprehensive testing and documentation for the OpenAPI and OpenAI integration.

---

### Issue #19: Write Integration Tests for Tool Calling

**Labels:** `testing`, `integration`, `priority:high`

**Title:** Create End-to-End Integration Tests for Tool Calling Pipeline

**Description:**

Build comprehensive integration tests that verify the complete tool calling flow from LLM to tool execution.

**Acceptance Criteria:**
- [ ] Create integration test suite in `packages/tool-pipeline/tests`
- [ ] Test complete flow: LLM → tool call → execution → response
- [ ] Mock external APIs (GitHub, GSA) for testing
- [ ] Test error scenarios (invalid inputs, API failures)
- [ ] Test multi-turn tool calling
- [ ] Test provider fallback
- [ ] Test rate limiting and quotas
- [ ] Test permission enforcement
- [ ] Include performance tests
- [ ] Add test coverage reporting (target: >80%)

**Dependencies:** Issue #11

**Estimated Effort:** 5-6 days

---

### Issue #20: Create Developer Documentation

**Labels:** `documentation`, `priority:medium`

**Title:** Write Comprehensive Documentation for OpenAPI Tools and LLM Providers

**Description:**

Create detailed documentation for developers to understand, use, and extend the OpenAPI and LLM provider system.

**Acceptance Criteria:**
- [ ] Create `docs/openapi-tools/` directory
- [ ] Write architecture overview
- [ ] Document how to add new tools to OpenAPI specs
- [ ] Document how to add new LLM providers
- [ ] Create tutorial: "Build Your First Tool"
- [ ] Document MoE routing logic and configuration
- [ ] Create API reference documentation
- [ ] Add code examples for common use cases
- [ ] Document security best practices
- [ ] Include troubleshooting guide
- [ ] Add diagrams (architecture, flow)

**Documentation Structure:**
```
docs/openapi-tools/
  ├── README.md                    # Overview
  ├── architecture.md              # System architecture
  ├── adding-tools.md              # How to add new tools
  ├── adding-providers.md          # How to add LLM providers
  ├── tutorial-first-tool.md       # Tutorial
  ├── moe-routing.md               # MoE router explained
  ├── security.md                  # Security guidelines
  ├── api-reference.md             # API docs
  └── troubleshooting.md           # Common issues
```

**Dependencies:** All previous issues

**Estimated Effort:** 4-5 days

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)
- Issue #1: OpenAPI Tool Registry
- Issue #2: OpenAPI to Tool Spec Converter
- Issue #3: Tool Executor
- Issue #6: LLM Provider Interface

### Phase 2: Providers & Tools (Weeks 4-6)
- Issue #4: Internal Tools OpenAPI Spec
- Issue #7: OpenAI Provider
- Issue #8: Anthropic Provider
- Issue #5: External API Wrappers

### Phase 3: Intelligence & Integration (Weeks 7-9)
- Issue #9: MoE Router
- Issue #10: Provider Performance Tracking
- Issue #11: Tool Calling Pipeline
- Issue #12: Example Pipeline

### Phase 4: Frontend & UX (Weeks 10-11)
- Issue #13: Command Palette
- Issue #14: AI Dock
- Issue #15: Integrations Page

### Phase 5: Security & Compliance (Weeks 12-13)
- Issue #16: Audit Logging
- Issue #17: Permission System
- Issue #18: Rate Limiting & Quotas

### Phase 6: Quality & Documentation (Week 14)
- Issue #19: Integration Tests
- Issue #20: Developer Documentation

## Dependencies Graph

```
Issue #1 (Registry)
  └─→ Issue #2 (Converter)
        └─→ Issue #3 (Executor)
              ├─→ Issue #4 (Internal Specs)
              ├─→ Issue #5 (External APIs)
              └─→ Issue #11 (Pipeline)

Issue #6 (Provider Interface)
  ├─→ Issue #7 (OpenAI)
  ├─→ Issue #8 (Anthropic)
  └─→ Issue #9 (MoE Router)
        └─→ Issue #10 (Metrics)

Issue #11 (Pipeline)
  └─→ Issue #12 (Example)

Issue #4, #10
  └─→ Issue #13, #14, #15 (Frontend)

Issue #3, #10
  └─→ Issue #16, #17, #18 (Security)

All Issues
  └─→ Issue #19, #20 (Testing & Docs)
```

## Estimated Timeline
- **Total Effort:** ~80-95 developer-days
- **With 2-3 developers:** 14-16 weeks
- **With 4-5 developers:** 8-10 weeks

## Success Metrics
- [ ] All internal tools available via OpenAPI
- [ ] At least 2 LLM providers integrated (OpenAI, Anthropic)
- [ ] MoE router selecting providers based on task type
- [ ] <200ms overhead for tool calling pipeline
- [ ] >99% tool execution success rate
- [ ] Complete audit trail for all tool executions
- [ ] >80% test coverage
- [ ] Full documentation published
