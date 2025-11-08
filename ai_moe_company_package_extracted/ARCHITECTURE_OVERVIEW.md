# Architecture Overview (Layered)
```
┌───────────────────────────────────────────────────────────┐
│  L1: Intake & Policy Router                               │
│  - Parse brief, detect domains (gov, data, web, ml)       │
│  - Route to planning/evidence lanes                       │
├───────────────────────────────────────────────────────────┤
│  L2: Evidence & Context Fabric                            │
│  - Government APIs (api.data.gov/open.gsa.gov)            │
│  - Google (Sheets/Drive/BigQuery)                         │
│  - Curated GitHub RAG (allowlisted repos)                 │
│  -> Normalized PolicyFacts & Evidence objects              │
├───────────────────────────────────────────────────────────┤
│  L3: Planning (OpenAI JSON mode)                          │
│  - SystemSpec & Backlog (strict JSON, with evidence_ids)  │
│  - Risks, NFRs, acceptance tests                          │
├───────────────────────────────────────────────────────────┤
│  L4: Execution (Claude + Sub‑Agents)                      │
│  - PatchPlan: atomic diffs, tests, CI, ADRs               │
│  - Security/Compliance & QA gates                         │
├───────────────────────────────────────────────────────────┤
│  L5: Delivery (GitHub)                                    │
│  - Repo, Issues/Projects, PR(s), Actions, Releases        │
│  - Decision logs (ADRs) & provenance                      │
├───────────────────────────────────────────────────────────┤
│  L6: Governance & Observability                           │
│  - Cost budgets, token accounting, retries/backoff        │
│  - Evidence registry, auditing                            │
└───────────────────────────────────────────────────────────┘
```
