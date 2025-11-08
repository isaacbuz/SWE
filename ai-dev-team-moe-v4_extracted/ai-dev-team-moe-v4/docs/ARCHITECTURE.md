
# System Architecture

Layers:
1. UI (Streamlit)
2. Orchestration (Router + Workflow)
3. Agents (Role-specialized)
4. Tooling (MCP tools, GitHub, Quality)
5. Platform (GitHub Projects/Issues/PR/Actions)

Sequence (high-level):
User → UI → Router (MoE) → Agents (plan/design/ops/cost/innovation) →
Quality gates → GitHub automation.
