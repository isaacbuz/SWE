# Claude — Full Implementation Prompt

Act as a senior software team implementing the **AI Dev Team MoE Platform** in this repo.
Goals:

- Implement model-specific clients for catalog entries in `config/models.yaml`.
- Replace agent stubs to actually call routed models, streaming outputs to UI.
- Add MCP client adapters per `config/mcp_tools.yaml` (repo manager, quality, search, fs).
- Implement GitHub automation (PR/issues/projects/actions) behind a feature flag.
- Add tests for router heuristics and cost-cap enforcement.

Constraints:

- Keep secrets in env vars. Respect cost caps.
- Fail fast with helpful errors.

Deliverables:

- Working `router` with dynamic signals
- Implemented agents with real LLM calls
- MCP adapters
- GitHub automation
- Tests + docs + examples
