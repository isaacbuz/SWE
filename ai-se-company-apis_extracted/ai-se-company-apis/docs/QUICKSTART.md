# Quickstart

1. `cp .env.example .env` and fill API keys (optional for public GitHub).
2. Edit `configs/providers.yaml` to enable/disable lanes.
3. Use the **Router** to decide which connectors to use per job.
4. Call the **Planner** (OpenAI lane) then **Execution** (Claude sub‑agents lane).
5. (Optional) Store/serve corpora for RAG built from public GitHub.

This pack is **scaffolding**; wire it into your existing repo's main workflow.
