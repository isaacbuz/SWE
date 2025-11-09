# AI Agent SE Company — Open API Integrations Pack

This supplemental pack shows how to **plug external open APIs** into your Mixture‑of‑Experts (MoE)
AI‑engineering company stack. It focuses on three lanes:

1. **Google APIs** (Sheets, Drive, BigQuery, Vertex, etc.)
2. **U.S. Government APIs** (e.g., `open.gsa.gov/api`, Data.gov families)
3. **Public GitHub Repos** as domain corpora for **Prompt‑Domain RAG** (plans, standards, templates)

It includes:

- Provider‑agnostic connectors (stubbed with real patterns: auth, quotas, retries, caching).
- Policy‑driven **Router** config to select the right lane (API tool use vs. RAG vs. codegen).
- Example **pipelines** that pull data, normalize, generate plans/patches, and post back to GitHub.
- **Prompts** for Claude/OpenAI to reason over API docs and repo corpora.
- **Diagrams** (Mermaid/PlantUML text) ready to paste into docs.
- A minimal `.env.example` and `requirements.txt` to get started.

> Drop this folder alongside your core repo, or merge `/src` and `/configs` into it.
