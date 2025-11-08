# Implementation Notes
- **Router**: If `tags` contains `gov`, run `api_facts_agent` with `gov_queries`. If `google-sheets-intake`, run `google_agent`. Always call `design_rag_agent` (allowlist).
- **Planner**: Use OpenAI JSON mode; enforce `evidence_ids`. Validate `SystemSpec`/`Backlog` via schema.
- **Execution**: Claude sub‑agents produce `PatchPlan`, tests, CI; ADRs cite Evidence.
- **Security**: `seccomp_agent` blocks PR on critical issues (secrets, weak crypto, missing auth).
- **QA**: readiness score with thresholds; at most 2 auto‑iterations.
- **Delivery**: Repo, Issues from Backlog, Kanban columns, atomic PR, ADRs, summary with evidence links.
