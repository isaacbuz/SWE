# AI-First Software Engineering Company

> **Mission**: Operate a software engineering company where AI agents are the primary workforce, orchestrated through a Mixture-of-Experts (MoE) router, with GitHub as the operational backbone.

## 🏗️ Architecture Overview

This is a production-ready, AI-native software engineering platform built on a layered MoE architecture:

```
┌───────────────────────────────────────────────────────────┐
│  L0: Interfaces (Web, CLI, GitHub App, IDE)               │
├───────────────────────────────────────────────────────────┤
│  L1: Gateway & Router (FastAPI + MoE Intelligence)        │
├───────────────────────────────────────────────────────────┤
│  L2: Orchestration (Temporal Workflows)                   │
├───────────────────────────────────────────────────────────┤
│  L3: Agent System (18+ Specialized Sub-Agents)            │
├───────────────────────────────────────────────────────────┤
│  L4: Tools & Integrations (GitHub, APIs, MCP)             │
├───────────────────────────────────────────────────────────┤
│  L5: Data Layer (PostgreSQL, Redis, Object Storage)       │
├───────────────────────────────────────────────────────────┤
│  L6: Observability & Governance (Metrics, Auditing)       │
└───────────────────────────────────────────────────────────┘
```

## 📁 Monorepo Structure

```
.
├── apps/
│   ├── web/                    # Next.js 14 premium UI
│   └── api/                    # FastAPI gateway
├── packages/
│   ├── ui/                     # shadcn/ui component library
│   ├── config/                 # Shared configs (ESLint, TS, etc)
│   ├── db/                     # Database schemas & migrations
│   ├── moe-router/             # MoE routing intelligence
│   ├── agents/                 # Specialized agent implementations
│   ├── integrations/           # External API connectors
│   ├── contracts/              # Pydantic schemas & TypeScript types
│   ├── tools/                  # Vendor-neutral tool surface
│   └── workflows/              # Temporal workflow definitions
├── docs/
│   ├── architecture/           # Architecture design docs
│   └── adrs/                   # Architecture Decision Records
├── infrastructure/             # Docker, K8s, Terraform
└── scripts/                    # Automation scripts
```

## 🚀 Quick Start

```bash
# Install dependencies
pnpm install

# Start development servers
pnpm dev

# Run tests
pnpm test

# Build for production
pnpm build
```

## 🎯 Key Features

- **🧠 MoE Router**: Intelligent model selection across Claude, GPT-5, Gemini, Granite, Qwen, etc.
- **🤖 18+ Specialized Agents**: Architect, Planner, Codegen, Reviewer, Tester, Security, Deployer, etc.
- **🎨 Premium UI**: AI-native interface with Command Palette, AI Dock, Narrated Diffs
- **📊 Evidence-Driven**: Every decision backed by Evidence IDs from trusted sources
- **🔒 Security-First**: OWASP compliance, secrets management, audit trails
- **💰 Cost-Optimized**: <$12 per small PR, <$60 per medium refactor
- **⚡ High Performance**: >85% PR merge rate, <60min MTTR

## 📚 Documentation

- [Architecture Overview](./docs/architecture/OVERVIEW.md)
- [Frontend Design System](./docs/architecture/FRONTEND.md)
- [MoE Router Specification](./docs/architecture/MOE_ROUTER.md)
- [Agent System Design](./docs/architecture/AGENTS.md)
- [Integration Guide](./docs/architecture/INTEGRATIONS.md)
- [Deployment Guide](./docs/architecture/DEPLOYMENT.md)

## 🔧 Tech Stack

**Frontend**: Next.js 14, React 18, Tailwind CSS, shadcn/ui, Zustand, TanStack Query
**Backend**: FastAPI, Temporal, PostgreSQL, Redis, Pydantic
**AI/ML**: Anthropic Claude, OpenAI, Google Gemini, IBM Granite, Qwen Coder
**Infrastructure**: Docker, Kubernetes, GitHub Actions, Vercel
**Observability**: OpenTelemetry, Prometheus, Grafana, Datadog

## 📊 Success Metrics

- Cost per PR: <$12 (small), <$60 (medium)
- PR merge rate: >85% without rework
- MTTR: <60 minutes on CI failures
- Test coverage: >80%
- Page load time: <200ms (p95)

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines.

## 📄 License

MIT
