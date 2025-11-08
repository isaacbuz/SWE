# Architecture Overview

We build the **intelligence layer** and **leverage platforms** (GitHub, Actions, Discussions, Projects). The system is organized into five lanes:

1. **Presentation**: Streamlit UI, REST API, CLI.
2. **Orchestration & MoE**: task decomposition, expert routing, consensus, quality gating.
3. **Experts & Tools**: role-specialized LLM agents, MCP tool chest.
4. **Providers & Data**: multi-model mesh (closed/open source), DB, vector store, artifact store.
5. **Ops**: tracing, metrics, secrets, budgets, policy.

See `/diagrams/multilayer-mermaid.md` for a detailed Mermaid diagram and `/diagrams/multilayer-plantuml.puml` for PlantUML.
