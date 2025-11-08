# Executive Summary

**Mission:** Operate a software engineering company where the *workforce is AI agents*. We combine Anthropic (Claude) and OpenAI models with open-source coders (Qwen/Granite) under a **Mixture-of-Experts (MoE)** router, and ship changes as **GitHub PRs** guarded by compliance and test gates.

**Key Ideas**
- Contract-driven: every step emits typed JSON (plans, patch specs, reports).
- Provider-agnostic: the same tool surface is exposed to *both* providers.
- Sub-agents (Claude): multi-file editing/review/publish loops.
- Structured outputs (OpenAI): plan/spec manifests guaranteed by schema.
- Ops-first: repo/CI/security are first-class tools, not side jobs.

**Target KPIs**
- <$12 per small PR, <$60 per medium refactor
- >85% PR merge rate without rework
- MTTR (red→green) < 60 minutes on CI failures

See `docs/ROADMAP.md` and `docs/OPERATING_MODEL.md`.
