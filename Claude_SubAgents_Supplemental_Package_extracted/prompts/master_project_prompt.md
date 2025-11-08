# Master Project Prompt (Claude Code + Sub-Agents + MCP)

Goal: Implement an AI-first software engineering org using a Mixture-of-Experts (MoE) of Claude sub-agents and MCP tools,
with GitHub as the PM/DevOps backbone.

## Primary Steps
1) Use `chief-architect` to produce ADR-0000 and diagrams from /docs/architecture.
2) Use `planner` to generate milestones, issues, and project board.
3) Use `codegen` to implement stories; open PRs via `git-ops`.
4) On each PR, run `tester` and `reviewer`, then `security-auditor`.
5) After merge, trigger `deployer` (MCP) to chosen environment; post release notes.
6) Maintain DECISION LOG and STATUS DASHBOARD in Discussions.

## Model Routing (MoE)
- Default order: Claude Sonnet/Ops for planning + GPT-5 for critical reasoning;
  switch to open models on-cost where spec is deterministic (e.g., Granite/Qwen for codegen),
  escalate back to Claude/GPT-5 when quality drops (failing tests, reviewer blocks).

## Policies
- Coverage threshold: 80%.
- No secrets in repo; use secret stores.
- ADR required for breaking changes.

Produce all artifacts in-repo. Ask for missing constraints explicitly, but do not block on minor ambiguity.
