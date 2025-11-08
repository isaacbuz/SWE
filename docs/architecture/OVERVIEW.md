# Architecture Overview

## System Vision

The AI-First Software Engineering Company is a production-grade platform that transforms plain-English requirements into production-ready software through intelligent orchestration of AI agents, with full auditability, cost optimization, and quality enforcement.

## Core Principles

1. **AI-Native**: AI agents are first-class citizens, not afterthoughts
2. **Provider-Agnostic**: Never locked to a single AI vendor
3. **Evidence-Driven**: Every decision backed by traceable evidence
4. **Contract-First**: Typed interfaces for all inter-agent communication
5. **Ops-First**: Infrastructure and CI/CD are architectural concerns, not bolt-ons
6. **Cost-Conscious**: Real-time budget tracking and intelligent model selection
7. **Security-Hardened**: Zero secrets in code, OWASP compliance, audit trails

## Layered Architecture

### Layer 0: Interface Layer
**Purpose**: Multiple entry points for human and machine interactions

**Components**:
- **Web UI** (Next.js 14): Premium AI-native interface with Command Palette, AI Dock
- **CLI**: Terminal-based workflow for power users
- **GitHub App**: Webhook-driven automation
- **IDE Extensions**: VSCode/IntelliJ integrations

**Key Design Decisions**:
- WebSocket-based real-time updates (no polling)
- Command Palette as primary interaction model
- AI Dock provides contextual suggestions based on current view
- All interfaces share same GraphQL/REST API layer

**Architecture Document**: [LAYER_0_INTERFACES.md](./layers/LAYER_0_INTERFACES.md)

---

### Layer 1: Gateway & Router
**Purpose**: Single entry point with intelligent request routing

**Components**:
- **API Gateway** (FastAPI): Authentication, rate limiting, request validation
- **MoE Router**: Intelligent model selection based on task, cost, performance
- **Load Balancer**: Distribute across model providers
- **Circuit Breaker**: Automatic failover on provider outages

**Key Algorithms**:
- **Cost Prediction**: Pre-estimate token usage before execution
- **Performance Tracking**: Real-time success rates per model/task type
- **Hybrid Routing**: Parallel execution with judge model selection
- **Learning Loop**: Feedback from PR outcomes improves routing

**Architecture Document**: [LAYER_1_GATEWAY_ROUTER.md](./layers/LAYER_1_GATEWAY_ROUTER.md)

---

### Layer 2: Orchestration Layer
**Purpose**: Stateful workflow coordination across multiple agents

**Components**:
- **Temporal Workflows**: Durable execution for Plan→Design→Code→Test→Deploy
- **Workflow Engine**: State machines for complex multi-agent flows
- **Event Bus**: Pub/sub for agent coordination
- **Saga Orchestrator**: Distributed transaction management

**Key Workflows**:
1. **Plan→Patch→PR**: Requirement → Spec → Implementation → Review → Merge
2. **Incident Swarm**: Alert → Diagnosis → Fix → Deploy → Post-mortem
3. **Migration Pipeline**: Analysis → Planning → Incremental Migration → Validation
4. **Quality Gate**: Pre-merge checks with automated fixes

**Architecture Document**: [LAYER_2_ORCHESTRATION.md](./layers/LAYER_2_ORCHESTRATION.md)

---

### Layer 3: Agent System
**Purpose**: Specialized AI agents for different engineering roles

**Agent Categories**:

1. **Executive Agents** (Strategy & Planning)
   - Chief Architect: System design, technology selection, ADRs
   - Technical Director: Code standards, best practices enforcement
   - VP Engineering: Resource allocation, priority management

2. **Development Agents** (Implementation)
   - Planner: Requirements → Issues/Milestones
   - Codegen: Feature implementation
   - Refactor: Code quality improvements
   - Migration Specialist: Framework/language migrations

3. **Quality Agents** (Verification)
   - Reviewer: Code review with context awareness
   - Tester: Test generation and execution
   - Security Auditor: OWASP, CVE scanning
   - Performance Benchmarker: Load testing, profiling

4. **Operations Agents** (Deployment & Maintenance)
   - Deployer: CI/CD orchestration
   - SRE Agent: Monitoring, alerting, incident response
   - Documentation Sync: Keep docs aligned with code

5. **Coordination Agents** (Inter-Agent Management)
   - Swarm Coordinator: Parallel agent orchestration
   - Conflict Resolver: Mediates disagreements (e.g., Reviewer vs Codegen)
   - Resource Optimizer: Manages agent workload distribution

**Agent Communication Protocol**:
```typescript
interface AgentMessage {
  messageId: string;
  from: AgentId;
  to: AgentId[];
  intent: "request" | "response" | "notification";
  payload: ContractSchema;
  evidenceIds: string[];
  timestamp: ISO8601;
}
```

**Architecture Document**: [LAYER_3_AGENTS.md](./layers/LAYER_3_AGENTS.md)

---

### Layer 4: Tools & Integrations
**Purpose**: Vendor-neutral abstractions for external systems

**Tool Categories**:

1. **Source Control Tools**
   - GitHub API: Issues, PRs, Projects, Actions
   - Git operations: Clone, commit, push, merge
   - Code search: Semantic search across repos

2. **AI Provider Tools**
   - Anthropic Claude: Sub-agents, tool use
   - OpenAI: Structured outputs, function calling
   - Google Gemini: Multimodal understanding
   - IBM Granite: Code-specialized models
   - Local Models: Ollama, vLLM for sensitive data

3. **External Data Sources**
   - Government APIs: Data.gov, GSA
   - Google Workspace: Sheets, Drive, BigQuery
   - Public Repos: Curated knowledge corpus (RAG)

4. **Infrastructure Tools**
   - Docker: Container management
   - Kubernetes: Orchestration
   - Terraform: IaC provisioning
   - Vercel/Netlify: Frontend deployment

5. **Observability Tools**
   - Datadog: APM, metrics
   - Grafana: Dashboards
   - Sentry: Error tracking
   - OpenTelemetry: Distributed tracing

**Tool Interface Standard**:
```python
class Tool(Protocol):
    name: str
    description: str
    schema: JSONSchema

    async def execute(
        self,
        params: dict,
        context: ExecutionContext
    ) -> ToolResult:
        ...
```

**Architecture Document**: [LAYER_4_TOOLS.md](./layers/LAYER_4_TOOLS.md)

---

### Layer 5: Data Layer
**Purpose**: Persistent storage with strong consistency guarantees

**Components**:

1. **PostgreSQL** (Primary Store)
   - Projects, Issues, PRs, Agents
   - Evidence registry
   - Audit logs (append-only)
   - User accounts & permissions

2. **Redis** (Caching & Real-time State)
   - Active workflow state
   - Agent availability/status
   - Rate limit counters
   - WebSocket session state

3. **Object Storage** (S3/GCS)
   - Code artifacts (patches, diffs)
   - Test results & coverage reports
   - Generated diagrams
   - Backup snapshots

4. **Vector DB** (Pinecone/Weaviate)
   - Code embeddings for semantic search
   - Evidence corpus (RAG)
   - Historical PR outcomes for learning

**Data Models**:
- **Contract-First**: All schemas defined in Pydantic (Python) and Zod (TypeScript)
- **Event Sourcing**: Critical entities (Projects, PRs) maintain event history
- **CQRS**: Separate read/write models for analytics

**Architecture Document**: [LAYER_5_DATA.md](./layers/LAYER_5_DATA.md)

---

### Layer 6: Observability & Governance
**Purpose**: Visibility, compliance, and continuous improvement

**Observability Components**:
1. **Metrics** (Prometheus)
   - Request latency (p50, p95, p99)
   - Cost per operation
   - Agent success rates
   - Model performance trends

2. **Tracing** (OpenTelemetry)
   - Full request paths through agents
   - Agent handoff visualization
   - Bottleneck identification

3. **Logging** (Structured JSON)
   - Agent decision rationale
   - Tool invocations
   - Error stack traces

4. **Alerting**
   - Cost budget exceeded
   - Quality gates failing
   - Agent performance degradation
   - Security vulnerabilities detected

**Governance Components**:
1. **Evidence Registry**
   - Source credibility scoring
   - Freshness tracking
   - Citation graph

2. **Audit Trail**
   - Immutable logs (cryptographically signed)
   - Decision provenance
   - Compliance reports (SOC2, HIPAA)

3. **Cost Management**
   - Real-time budget tracking
   - Per-project cost allocation
   - ROI calculation

4. **Quality Metrics**
   - PR merge rate
   - MTTR (Mean Time To Recovery)
   - Test coverage trends
   - Security posture score

**Architecture Document**: [LAYER_6_OBSERVABILITY.md](./layers/LAYER_6_OBSERVABILITY.md)

---

## Cross-Cutting Concerns

### Security
- **Authentication**: OAuth 2.0 + OIDC
- **Authorization**: RBAC with fine-grained permissions
- **Secrets**: GitHub Secrets + HashiCorp Vault
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Audit**: Tamper-proof logs with digital signatures

### Performance
- **Caching**: Multi-tier (Redis, CDN, browser)
- **Optimization**: Prompt compression, batching, parallelization
- **Scalability**: Horizontal scaling via Kubernetes

### Reliability
- **Circuit Breakers**: Prevent cascade failures
- **Retries**: Exponential backoff with jitter
- **Failover**: Multi-provider redundancy
- **Blue/Green Deployments**: Zero-downtime updates

## Technology Decisions

See [ADR Index](../adrs/INDEX.md) for detailed Architecture Decision Records.

Key decisions:
- [ADR-0001: Monorepo with Turborepo](../adrs/0001-monorepo-turborepo.md)
- [ADR-0002: Next.js 14 for Frontend](../adrs/0002-nextjs-14-frontend.md)
- [ADR-0003: FastAPI for Gateway](../adrs/0003-fastapi-gateway.md)
- [ADR-0004: Temporal for Workflows](../adrs/0004-temporal-workflows.md)
- [ADR-0005: PostgreSQL + Redis](../adrs/0005-postgres-redis.md)

## Deployment Architecture

```
┌─────────────┐
│   Vercel    │ ← Next.js Web UI
└─────────────┘
       │
       ↓
┌─────────────┐
│  CloudFlare │ ← CDN + DDoS Protection
└─────────────┘
       │
       ↓
┌──────────────────────────────────┐
│   Kubernetes Cluster (GKE/EKS)   │
│  ┌────────────┐  ┌────────────┐  │
│  │ API Gateway│  │  Temporal  │  │
│  └────────────┘  └────────────┘  │
│  ┌────────────┐  ┌────────────┐  │
│  │   Agents   │  │   Workers  │  │
│  └────────────┘  └────────────┘  │
└──────────────────────────────────┘
       │                    │
       ↓                    ↓
┌─────────────┐      ┌─────────────┐
│ PostgreSQL  │      │   Redis     │
│  (Cloud SQL)│      │  (Memstore) │
└─────────────┘      └─────────────┘
```

## Next Steps

1. Review module-specific architecture documents in [./modules/](./modules/)
2. Understand agent specifications in [./agents/](./agents/)
3. Read ADRs for context on key decisions in [../adrs/](../adrs/)
4. See deployment guide in [DEPLOYMENT.md](./DEPLOYMENT.md)
