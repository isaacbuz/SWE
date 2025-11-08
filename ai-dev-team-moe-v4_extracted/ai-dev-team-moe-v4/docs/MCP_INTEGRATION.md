
# MCP Integration Plan

We define logical tools in `config/mcp_tools.yaml`. A host runner (e.g., MCP-capable orchestrator)
binds them to actual servers (git, quality, search, file ops). Each agent calls tools through a
thin adapter, enabling standardized, audited actions.
