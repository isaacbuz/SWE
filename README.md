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
│   ├── moe_router/             # MoE routing intelligence
│   ├── agents/                 # Specialized agent implementations
│   ├── skills_engine/          # Skills execution engine ⭐ NEW
│   ├── skills-library/         # Built-in Skills library ⭐ NEW
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
- **⚡ Skills Marketplace**: 16+ built-in Skills for code generation, testing, review, documentation ⭐ NEW
- **📊 Evidence-Driven**: Every decision backed by Evidence IDs from trusted sources
- **🔒 Security-First**: OWASP compliance, secrets management, audit trails
- **💰 Cost-Optimized**: <$12 per small PR, <$60 per medium refactor
- **⚡ High Performance**: >85% PR merge rate, <60min MTTR

## ⚡ Skills System

The Skills System provides a marketplace for AI-powered Skills that can be discovered, installed, and executed by both users and agents.

### Quick Start

```bash
# Load Skills into database
export DATABASE_URL="postgresql://user:pass@localhost:5432/swe_agent"
python packages/skills-library/seed_skills.py

# Access marketplace
# Navigate to: http://localhost:3000/skills
```

### Features

- ✅ Skills execution engine with validation and caching
- ✅ RESTful API with 8 endpoints
- ✅ Marketplace UI with search, filter, and playground
- ✅ 16 built-in Skills across 5 categories
- ✅ Agent integration for seamless usage
- ✅ 80%+ test coverage

See [README_SKILLS.md](./README_SKILLS.md) for detailed Skills documentation.

## 📚 Documentation

- [Architecture Overview](./docs/architecture/OVERVIEW.md)
- [Frontend Design System](./docs/architecture/FRONTEND.md)
- [MoE Router Specification](./docs/architecture/MOE_ROUTER.md)
- [Agent System Design](./docs/architecture/AGENTS.md)
- [Skills System](./docs/architecture/CLAUDE_SKILLS.md) ⭐ NEW
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

## 🎉 Recent Updates

**November 8, 2025**: Skills System v1.0.0 released
- Complete Skills marketplace implementation
- 16 built-in Skills
- Agent integration
- 80%+ test coverage

See [CHANGELOG_SKILLS.md](./CHANGELOG_SKILLS.md) for details.
