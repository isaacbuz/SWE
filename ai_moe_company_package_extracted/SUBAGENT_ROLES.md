# Claude Sub‑Agents (Roles)
- **ceo_agent** — policy/tie‑breaks/synthesis, owns deliverable integrity.
- **api_facts_agent** — queries gov endpoints; outputs `PolicyFacts` with `Evidence` metadata.
- **google_agent** — reads Sheets/Drive; maps rows to spec inputs.
- **design_rag_agent** — curated GitHub corpus retrieval; outputs Evidence chunks.
- **impl_agent** — produces `PatchPlan` (atomic diffs), tests, CI workflows, ADRs.
- **seccomp_agent** — OWASP/secrets/license checks; blocks unsafe diffs.
- **qa_agent** — test plan & readiness scoring; triggers limited re‑work.
- **delivery_agent** — creates repo/issues/PR/board; posts ADR and summary.
