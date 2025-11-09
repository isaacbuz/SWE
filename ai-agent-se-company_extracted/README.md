# AI-Agent Software Engineering Company (MoE, Anthropic + OpenAI)

This repository provides a **provider-agnostic, Mixture-of-Experts (MoE)** agent platform that routes software-engineering tasks to the most suitable model and toolchain. It uses **contract-driven I/O**, **sub-agents (Anthropic)** for multi-file repo edits and reviews, and **structured outputs (OpenAI)** for deterministic planning. The platform integrates GitHub via a common _tool surface_ (read repo, apply patch, run tests, create PR, render diagrams) and enforces compliance gates.

## Layers

- L0 Interfaces: Web/CLI/GitHub App/IDE
- L1 Gateway & Router: FastAPI gateway, policy-based provider routing
- L2 Orchestrator: Temporal/Prefect workflows for Plan→Patch→PR and Incident Swarm
- L3 Experts: CEO/Architect/VP Eng/CTO/CFO/Compliance plus granular specialists
- L4 Tools: Vendor-neutral tools mapped to GitHub, CI, lint, security, diagram
- L5 Data: Contracts (Pydantic), state (Redis), artifacts (object storage)
- L6 Observability & Governance: metrics, approvals, audits

See `docs/EXEC_SUMMARY.md` and `docs/ARCHITECTURE.md` for details.
