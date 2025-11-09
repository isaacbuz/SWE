# Implementation Roadmap for Outstanding GitHub Issues

**Generated**: November 8, 2025  
**Repository**: https://github.com/isaacbuz/SWE  
**Total Open Issues**: 26 (6 Epics, 20 Implementation Tasks)  
**CI Status**: 1 failed workflow run (initial commit)

## Executive Summary

Your AI-First Software Engineering Company has a solid foundation with **Phase 1 complete**. You have 26 well-structured GitHub issues organized into 6 epics that map to the OpenAPI & LLM Provider Integration roadmap. The CI pipeline failed on the initial commit - we need to fix that first, then systematically implement the outstanding features.

## Critical Path: Fix CI First ⚠️

**Issue**: CI Pipeline failed on initial commit  
**Workflow**: https://github.com/isaacbuz/SWE/actions/runs/19198288382

### Action Required
1. Get failed job logs to diagnose issue
2. Fix CI pipeline configuration
3. Ensure all tests pass before proceeding with new features

---

## Epic Overview & Dependency Graph

```
Epic #1: OpenAPI Tooling Infrastructure (HIGH PRIORITY)
├── Issue #7: OpenAPI Tool Registry Foundation
├── Issue #8: OpenAPI to Tool Spec Converter (depends on #7)
├── Issue #9: Tool Executor with Schema Validation (depends on #8)
├── Issue #10: Internal Tools OpenAPI Specification (depends on #8)
└── Issue #11: External API Wrappers (depends on #9)

Epic #2: OpenAI Provider Integration (HIGH PRIORITY)
├── Issue #12: Provider-Agnostic LLM Interface
├── Issue #13: OpenAI Provider Implementation (depends on #12)
├── Issue #14: Anthropic Provider Implementation (depends on #12)
├── Issue #15: MoE Router with Provider Selection (depends on #13, #14)
└── Issue #16: Provider Performance Tracking (depends on #15)

Epic #3: Tool Calling Integration (HIGH PRIORITY)
├── Issue #17: Tool Calling Pipeline (depends on #9, #13)
└── Issue #18: Sample Pipeline - Spec to GitHub Issues (depends on #15, #17)

Epic #4: Frontend Integration (MEDIUM PRIORITY)
├── Issue #19: Command Palette with OpenAPI Tools (depends on #10)
├── Issue #20: AI Dock with Provider Visibility (depends on #16)
└── Issue #21: Integrations Management Page (depends on #11)

Epic #5: Security & Compliance (HIGH PRIORITY)
├── Issue #22: Tool Execution Audit Logging (depends on #9)
├── Issue #23: Tool Permission System (depends on #22)
└── Issue #24: Rate Limiting and Quotas (depends on #16)

Epic #6: Testing & Documentation (MEDIUM PRIORITY)
├── Issue #25: Integration Tests for Tool Calling (depends on #17)
└── Issue #26: Developer Documentation (depends on ALL)
```

---

## Phase 2 Implementation Plan (4-6 Weeks)

### Week 1: Foundation & CI Fix

**Sprint Goal**: Fix CI pipeline, establish OpenAPI foundation

#### Day 1-2: CI/CD Repair & Validation
- [ ] Get CI failure logs
- [ ] Fix linting issues
- [ ] Fix test failures
- [ ] Ensure Docker builds succeed
- [ ] Green CI pipeline

#### Day 3-5: OpenAPI Foundation
- [ ] **Issue #7**: OpenAPI Tool Registry Foundation (3-5 days)
  - Create `packages/openapi-tools` package
  - Implement ToolRegistry class
  - Add OpenAPI spec loader
  - TypeScript types for ToolSpec interface
  - Unit tests

**Deliverables**:
✅ Green CI pipeline  
✅ OpenAPI Tool Registry package ready

---

### Week 2: OpenAPI Tooling Complete

**Sprint Goal**: Complete OpenAPI infrastructure (Epic #1)

#### Day 1-2: Tool Spec Converter
- [ ] **Issue #8**: OpenAPI to Tool Spec Converter (3-4 days)
  - Implement `openApiToToolSpecs()` function
  - Support OpenAPI 3.0 and 3.1
  - Extract operation metadata
  - Convert schemas to JSON Schema format
  - Comprehensive tests

#### Day 3-5: Tool Executor & Internal Tools
- [ ] **Issue #9**: Tool Executor with Schema Validation (4-5 days)
  - Build ToolExecutor class
  - Integrate Ajv/Zod for validation
  - Tool registration system
  - Security features (sanitization, rate limiting)
  - Audit logging integration
  - Tests

- [ ] **Issue #10**: Internal Tools OpenAPI Spec (3-4 days - parallel)
  - Create `tools/openapi/ai-dev-tools.yaml`
  - Define GitHub operations (6 tools)
  - Define Code operations (5 tools)
  - Define CI/CD operations (4 tools)
  - Validate with OpenAPI linter

**Deliverables**:
✅ Complete OpenAPI tooling infrastructure  
✅ Internal tools defined and validated

---

### Week 3: LLM Provider Integration

**Sprint Goal**: Complete provider integration (Epic #2)

#### Day 1-2: Provider Interface & OpenAI
- [ ] **Issue #12**: Provider-Agnostic LLM Interface (2-3 days)
  - Create `packages/llm-providers` package
  - Define LLMProvider interface
  - Message format standardization
  - Tool calling support
  - TypeScript types

- [ ] **Issue #13**: OpenAI Provider Implementation (4-5 days)
  - Implement OpenAIProvider class
  - GPT-4 and GPT-4 Turbo support
  - Tool/function calling
  - Streaming support
  - Error handling and retries
  - Cost tracking
  - Comprehensive tests

#### Day 3-5: Anthropic Provider & External APIs
- [ ] **Issue #14**: Anthropic Provider (4-5 days - parallel)
  - Implement AnthropicProvider class
  - Claude 3 models (Opus, Sonnet, Haiku)
  - Tool use format conversion
  - Tests

- [ ] **Issue #11**: External API Wrappers (5-7 days)
  - Create `packages/external-api-tools`
  - GitHub API wrapper (issues, PRs, repos)
  - Open GSA API wrapper
  - Credential management
  - Rate limiting per API
  - Response caching
  - Retry logic

**Deliverables**:
✅ OpenAI and Anthropic providers ready  
✅ External APIs wrapped securely

---

### Week 4: MoE Router & Tool Calling Pipeline

**Sprint Goal**: Connect all pieces with intelligent routing

#### Day 1-3: MoE Router Enhancement
- [ ] **Issue #15**: MoE Router with Provider Selection (5-7 days)
  - Enhance existing MoE router in `packages/moe_router/`
  - Provider scoring algorithm
  - Task classification
  - Cost optimization logic
  - Provider fallback
  - A/B testing capabilities
  - Health tracking
  - Configuration for routing policies

#### Day 3-5: Tool Calling Pipeline & Performance Tracking
- [x] **Issue #17**: Tool Calling Pipeline (5-6 days) ✅ **COMPLETE**
  - ✅ Create `packages/tool-pipeline` package
  - ✅ Tool discovery from OpenAPI registry
  - ✅ Convert specs to provider formats
  - ✅ Tool call parsing
  - ✅ Multi-turn tool calling (tool → LLM loops)
  - ✅ Validation and safety checks
  - ✅ Comprehensive logging

- [x] **Issue #16**: Provider Performance Tracking (4-5 days - parallel) ✅ **COMPLETE**
  - ✅ Extend `packages/observability`
  - ✅ Per-provider metrics collection
  - ✅ Win-rate tracking
  - ✅ Cost/performance curves
  - ✅ Alerting for anomalies
  - ✅ Export to Prometheus/Datadog (via base MetricsCollector)

**Deliverables**:
✅ Intelligent MoE routing working  
✅ Complete tool calling pipeline  
✅ Performance tracking in place

---

### Week 5: Security, Frontend & Examples

**Sprint Goal**: Security hardening and user-facing features

#### Day 1-2: Security Features
- [ ] **Issue #22**: Tool Execution Audit Logging (4-5 days)
  - Extend `packages/observability` with audit logging
  - Complete audit log entries
  - PII detection and redaction
  - Log retention policies
  - Export capabilities
  - Suspicious pattern detection

- [ ] **Issue #23**: Tool Permission System (5-6 days)
  - Create permission model (RBAC)
  - PermissionChecker class
  - Default role definitions
  - Permission conditions
  - Integration with ToolExecutor
  - UI for permission management

#### Day 3-5: Frontend Integration
- [x] **Issue #19**: Command Palette with OpenAPI Tools (4-5 days) ✅ **COMPLETE**
  - ✅ Extend command palette in `apps/web`
  - ✅ Load tools from registry
  - ✅ Group by category
  - ✅ Parameter input forms
  - ✅ Execute tools from palette
  - ✅ Show progress and results

- [ ] **Issue #20**: AI Dock with Provider Visibility (5-6 days)
  - Create AI Dock component
  - Display current/last provider
  - Provider selection UI
  - Tool call trace viewer
  - Token usage and cost
  - Re-run with different provider

- [x] **Issue #18**: Sample Pipeline - Spec to GitHub Issues (3-4 days) ✅ **COMPLETE**
  - ✅ Create CLI tool package
  - ✅ `spec-to-github` command
  - ✅ Full pipeline demonstration
  - ✅ Example spec files
  - ✅ Documentation and tutorial

**Deliverables**:
✅ Security controls in place  
✅ Frontend tools integrated  
✅ Working example pipeline

---

### Week 6: Testing, Documentation & Polish

**Sprint Goal**: Quality assurance and documentation

#### Day 1-3: Comprehensive Testing
- [ ] **Issue #25**: Integration Tests for Tool Calling (5-6 days)
  - Create integration test suite
  - Mock external APIs
  - Test complete flows
  - Error scenario testing
  - Multi-turn testing
  - Provider fallback testing
  - Performance tests
  - Coverage reporting (>80% target)

#### Day 3-5: Rate Limiting & Documentation
- [ ] **Issue #24**: Rate Limiting and Quotas (4-5 days)
  - Rate limiting middleware
  - Per-user and per-tool limits
  - Cost quotas (daily/monthly)
  - Real-time cost tracking
  - Quota exhaustion alerts
  - Quota management UI

- [ ] **Issue #21**: Integrations Management Page (4-5 days)
  - Create integrations page in `apps/web`
  - Credential management UI
  - API health status
  - Rate limit display
  - Tool enable/disable
  - Connection testing
  - Usage statistics

- [ ] **Issue #26**: Developer Documentation (4-5 days)
  - Create `docs/openapi-tools/` directory
  - Architecture overview
  - Adding tools guide
  - Adding providers guide
  - Tutorial: Build Your First Tool
  - MoE routing documentation
  - API reference
  - Code examples
  - Troubleshooting guide
  - Architecture diagrams

**Deliverables**:
✅ Comprehensive test coverage  
✅ Complete documentation  
✅ All epics closed  
✅ Production-ready system

---

## Implementation Strategy

### Parallel Workstreams

To maximize velocity, we can run 3 parallel workstreams:

**Stream 1: Core Infrastructure** (Priority: CRITICAL)
- Issues #7, #8, #9, #10, #11
- Focus: OpenAPI tooling foundation
- Owner: Backend/Infrastructure agents

**Stream 2: LLM Integration** (Priority: CRITICAL)
- Issues #12, #13, #14, #15, #16, #17
- Focus: Provider integration and routing
- Owner: AI/ML agents

**Stream 3: Security & Frontend** (Priority: HIGH)
- Issues #18, #19, #20, #21, #22, #23, #24
- Focus: User-facing features and security
- Owner: Frontend/Security agents

**Stream 4: Quality** (Priority: MEDIUM - Week 6)
- Issues #25, #26
- Focus: Testing and documentation
- Owner: QA/Docs agents

### Recommended Agent Assignments

Based on your 18 specialized agents:

1. **Infrastructure Team (3 agents)** → Stream 1
   - OpenAPI registry, converter, executor
   - External API wrappers

2. **Backend Team (4 agents)** → Stream 2
   - LLM provider interfaces
   - MoE router enhancements
   - Tool calling pipeline

3. **Frontend Team (4 agents)** → Stream 3 (partial)
   - Command Palette
   - AI Dock
   - Integrations page

4. **Agent Development Team (3 agents)** → Stream 2
   - Provider integration testing
   - Tool execution workflows

5. **Security Team (from Agent Dev)** → Stream 3 (partial)
   - Audit logging
   - Permission system
   - Rate limiting

6. **Quality & Observability Team (2 agents)** → Stream 4
   - Integration tests
   - Documentation

7. **Integration Team (2 agents)** → Support all streams
   - Cross-stream coordination
   - API integration

---

## Risk Mitigation

### Technical Risks

**Risk 1: CI/CD Pipeline Issues**
- **Mitigation**: Fix CI first before any new development
- **Action**: Get logs, diagnose, fix linting/tests

**Risk 2: OpenAPI Tool Spec Complexity**
- **Mitigation**: Start with simple tools, iterate
- **Action**: Use GitHub API as reference implementation

**Risk 3: LLM Provider API Changes**
- **Mitigation**: Abstract provider interface, version pinning
- **Action**: Follow provider changelogs, implement adapters

**Risk 4: Performance/Cost Overruns**
- **Mitigation**: Early metrics, quotas, circuit breakers
- **Action**: Implement Issue #16 (tracking) early

**Risk 5: Security Vulnerabilities**
- **Mitigation**: Security-first design, early auditing
- **Action**: Implement Issue #22 (audit logs) before production

### Project Risks

**Risk 1: Scope Creep**
- **Mitigation**: Stick to defined issues, no "just one more thing"
- **Action**: Use project board to track scope

**Risk 2: Dependency Blocking**
- **Mitigation**: Clear dependency graph, parallel streams
- **Action**: Start independent tasks first

**Risk 3: Testing Delays**
- **Mitigation**: Test as you go, don't save for end
- **Action**: Each issue includes tests in acceptance criteria

---

## Success Metrics

### Week 2 Checkpoint
- [ ] CI pipeline green
- [ ] OpenAPI registry functional
- [ ] At least 5 internal tools defined

### Week 4 Checkpoint
- [ ] OpenAI and Anthropic providers working
- [ ] MoE router selecting providers intelligently
- [ ] Tool calling pipeline executing successfully
- [ ] At least 1 end-to-end demo working

### Week 6 Checkpoint (Phase 2 Complete)
- [ ] All 26 issues closed
- [ ] >80% test coverage
- [ ] Complete documentation published
- [ ] Security audit passed
- [ ] Performance targets met (<200ms routing, <$12/small PR)
- [ ] Production deployment ready

---

## Quick Start Guide for Agents

### For Each Issue Implementation:

1. **Read the issue carefully** - Review acceptance criteria
2. **Check dependencies** - Ensure prerequisite issues are complete
3. **Create feature branch** - `git checkout -b feature/issue-<number>`
4. **Implement with tests** - Follow TDD where possible
5. **Update documentation** - Keep docs in sync
6. **Run quality gates** - `pnpm run quality:check`
7. **Create PR** - Reference issue number, get review
8. **Merge and close issue** - Deploy to staging

### Code Quality Standards

- **TypeScript**: Strict mode, no `any`, full type coverage
- **Python**: Type hints, pydantic models, async/await
- **Tests**: >80% coverage, unit + integration
- **Docs**: All public APIs documented
- **Security**: No secrets in code, input validation
- **Performance**: <200ms API latency, <5s tool execution

---

## Immediate Next Steps

### 1. Fix CI Pipeline (TODAY)
```bash
# Get failed job logs
gh run view 19198288382 --log-failed

# Diagnose and fix issues
# Common issues: missing dependencies, linting errors, test failures

# Re-run CI
git commit --allow-empty -m "ci: trigger pipeline"
git push
```

### 2. Create Project Board (TODAY)
```bash
# Create GitHub Project board
gh project create --owner isaacbuz --title "OpenAPI & LLM Integration"

# Add all issues to board
for i in {1..26}; do
  gh issue edit $i --add-project "OpenAPI & LLM Integration"
done

# Create milestones
gh api repos/isaacbuz/SWE/milestones -f title="Epic 1: OpenAPI Tooling" -f due_on="2025-11-22T23:59:59Z"
```

### 3. Assign Issues to Agents (TODAY)
Review the agent assignments above and assign issues in GitHub.

### 4. Kick Off Week 1 (MONDAY)
Start with Epic #1, Issue #7: OpenAPI Tool Registry Foundation.

---

## Resources & References

### External Documentation
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [JSON Schema](https://json-schema.org/)

### Internal Documentation
- [Architecture Overview](/docs/architecture/OVERVIEW.md)
- [MoE Router Spec](/docs/architecture/MOE_ROUTER.md)
- [Skills Integration](/docs/architecture/CLAUDE_SKILLS.md)

### Tools & Libraries
- **OpenAPI**: `openapi3-ts`, `swagger-parser`
- **Validation**: `ajv`, `zod`
- **LLM SDKs**: `openai`, `@anthropic-ai/sdk`
- **Testing**: `vitest`, `pytest`, `playwright`

---

## Conclusion

You have a well-structured roadmap with clear dependencies and 6 weeks to implement a production-ready OpenAPI + LLM Provider Integration system. The foundation from Phase 1 is solid - now it's time to build the intelligence layer.

**Priority Order**:
1. ✅ Fix CI (CRITICAL)
2. 🔧 Epic #1: OpenAPI Tooling (CRITICAL)
3. 🤖 Epic #2: LLM Providers (CRITICAL)
4. 🔗 Epic #3: Tool Calling (CRITICAL)
5. 🔒 Epic #5: Security (HIGH)
6. 🎨 Epic #4: Frontend (MEDIUM)
7. ✅ Epic #6: Testing & Docs (MEDIUM)

Let's build this! 🚀
