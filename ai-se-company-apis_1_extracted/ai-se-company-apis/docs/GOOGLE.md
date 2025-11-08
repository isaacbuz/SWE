# Google APIs Integration (Design Notes)

**Goals**
- Safely leverage Google Sheets/Drive/BigQuery as *source-of-truth* inputs to planning and code‑gen lanes.
- Use **read-only** scopes by default; escalate write scopes via policy approvals.
- Normalize outputs to **Contracts** (Pydantic models) to feed MoE agents.

**Auth Options**
- OAuth Client (end-user consent, best for interactive ops consoles)
- Service Account (machine-to-machine; use domain-wide delegation if your Google Workspace allows)

**Patterns**
1. **Schema-first**: Define a `Contract` for what you fetch (Sheet → `ProjectBacklog`, `Requirements`).
2. **Caching**: Cache GET results by ETag/If-None-Match. Invalidate on webhook or scheduled TTL.
3. **Retry & Quota**: Exponential backoff on 429/5xx using `tenacity`.
4. **Least-privilege**: Separate readers from writers. Use different creds for prod vs. dev.
5. **Observability**: Add `x-request-id`, log rate-limit headers, surface to ops console.

**Example Sheet to Contract**
- Single Sheet tab named `spec` with columns: `key, value`
- Convert into `SystemSpec` contract consumed by planning agent.

**When to prefer BigQuery**
- Large analytics/RAG corpora creation → export embeddings to your vector store.
