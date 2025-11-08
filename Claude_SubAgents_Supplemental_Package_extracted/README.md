# Claude Sub-Agents Supplemental Package

This package equips your repo with Claude Code **sub-agents**, MCP config examples, executive prompts,
and a runbook to operate a Mixture-of-Experts (MoE) engineering workflow centered on GitHub + MCP.

## Layout
- `.claude/agents/` — Specialist agents (architect, planner, codegen, reviewer, tester, security, deployer, git-ops, bench).
- `prompts/` — Executive Router and master project prompt.
- `mcp/` — Example MCP config JSON.
- `runbooks/` — Step-by-step operations guide.
- `docs/` — (optional) Put diagrams, ADRs, security reports here.

## Quick Start
1. Commit this folder to your repo root.
2. In Claude Code, type `/agents` → verify agents appear.
3. Paste `prompts/master_project_prompt.md` into Claude and follow the runbook.

## Notes
- Restrict tools per agent when needed by editing YAML front-matter.
- Add your MCP servers (GitHub, Vercel, AWS, etc.) to your Claude config.
- Treat ADRs and the Decision Log as your single source of truth.
