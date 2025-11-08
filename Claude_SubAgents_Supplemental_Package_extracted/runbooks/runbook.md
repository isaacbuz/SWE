# Runbook: Operating the AI Engineering Org (MoE + Sub-Agents)

## 0) Prereqs
- Claude Code installed; access to sub-agents (`/agents`).
- MCP servers configured in `mcp/mcp.config.example.json`.
- GitHub repo and tokens ready; Actions enabled.

## 1) Initialize
- Place `.claude/agents/` in repo root (commit to VCS).
- Paste `prompts/master_project_prompt.md` into Claude to bootstrap context.

## 2) Design → Plan
- In Claude: “Use `chief-architect` to create ADR-0000 for <product> and diagrams.”
- Then: “Use `planner` to open GitHub issues and create the project board with columns.”

## 3) Implement
- “Use `codegen` to implement Epic-1 stories in a feature branch.”
- “Create PRs via `git-ops` and link issues.”

## 4) Review, Test, Secure
- “Invoke `tester` + `reviewer` on PR #XYZ.”
- “Invoke `security-auditor` and attach the security report.”

## 5) Deploy
- “Use `deployer` to push release v0.1.0 to staging via Vercel (MCP).”

## 6) Governance
- Keep ADRs updated.
- Enforce branch protections; block without green checks.
- Monthly cost review: swap model choices per `benchmarker` tables.
