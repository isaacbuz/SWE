# Next Steps Plan

**Date**: November 9, 2025  
**Current Status**: Epic #1 Complete (100%)

## 🎯 Recommended Next Steps (Priority Order)

### Option 1: Complete Router TODOs (HIGHEST PRIORITY) 🔴

**Why**: Makes the API actually functional. Currently all endpoints return 501 or empty responses.

**What**: Implement database queries and business logic in API routers:
- `apps/api/routers/projects.py` - 20+ TODOs
- `apps/api/routers/issues.py` - 25+ TODOs  
- `apps/api/routers/prs.py` - 30+ TODOs
- `apps/api/routers/analytics.py` - 20+ TODOs
- `apps/api/routers/agents.py` - 20+ TODOs

**Impact**: 
- ✅ API endpoints become functional
- ✅ Frontend can actually use the API
- ✅ End-to-end workflows become possible
- ✅ Issue #23 (Build all API routers) gets completed

**Estimated Effort**: 2-3 days

---

### Option 2: Issue #17 - Tool Calling Pipeline 🔴

**Why**: Connects Epic #1 (OpenAPI tools) with LLM providers. Natural next step.

**What**: Build pipeline that:
- Loads tools from OpenAPI registry
- Converts to provider format
- Executes via Tool Executor
- Handles multi-turn tool calling
- Integrates with agents

**Impact**:
- ✅ Agents can use OpenAPI tools
- ✅ End-to-end tool execution works
- ✅ Foundation for Epic #3

**Estimated Effort**: 3-4 days

**Dependencies**: ✅ Epic #1 complete, ✅ Providers exist

---

### Option 3: Issue #11 - External API Wrappers 🟡

**Why**: Completes Epic #1 fully. Enables external API integration.

**What**: Create wrappers for:
- GitHub API (enhance existing)
- Government APIs (Data.gov, GSA)
- Credential management
- Rate limiting per API

**Impact**:
- ✅ External APIs accessible as tools
- ✅ Epic #1 fully complete
- ✅ More tools available to agents

**Estimated Effort**: 2-3 days

**Dependencies**: ✅ Issue #9 (Tool Executor) complete

---

### Option 4: Epic #2 - LLM Provider Integration 🟡

**Why**: According to roadmap, but providers already exist. May need enhancement.

**What**: 
- Issue #12: Provider-Agnostic Interface (may already exist)
- Issue #13: OpenAI Provider (exists, may need enhancement)
- Issue #14: Anthropic Provider (exists, may need enhancement)
- Issue #15: MoE Router Enhancement (exists, may need verification)

**Impact**:
- ✅ Standardized provider interface
- ✅ Better MoE router integration
- ✅ Foundation for tool calling

**Estimated Effort**: 2-3 days (mostly verification/enhancement)

**Note**: Providers already exist in `packages/integrations/ai_providers/`. May just need verification and enhancement.

---

## 📊 Current Status Summary

### Completed ✅
- **Epic #1**: OpenAPI Tooling Infrastructure (100%)
  - Issue #7: Tool Registry ✅
  - Issue #8: Tool Spec Converter ✅
  - Issue #9: Tool Executor ✅
  - Issue #10: Internal Tools Spec ✅
- **Epic #8**: Testing Infrastructure
  - Issue #85: MoE Router Tests ✅
  - Issue #86: Agent System Tests ✅
  - Issue #87: Workflow Tests ✅
  - Issue #89: CI/CD Testing ✅

### In Progress 🚧
- **Router TODOs**: 148 TODOs across 5 routers
- **Issue #11**: External API Wrappers (pending)

### Pending ⏳
- **Epic #2**: LLM Provider Integration (providers exist, need verification)
- **Epic #3**: Tool Calling Pipeline
- **Epic #4**: Frontend Integration
- **Epic #5**: Security & Compliance

---

## 🎯 Recommended Path Forward

### Immediate (This Week)
1. **Complete Router TODOs** (2-3 days)
   - Makes API functional
   - Unblocks frontend development
   - Completes Issue #23

### Short Term (Next Week)
2. **Issue #17: Tool Calling Pipeline** (3-4 days)
   - Connects tools with LLM providers
   - Enables agent tool usage
   - Completes Epic #3 foundation

3. **Issue #11: External API Wrappers** (2-3 days)
   - Completes Epic #1 fully
   - Adds external API support

### Medium Term (Week 3-4)
4. **Epic #2: LLM Provider Integration** (2-3 days)
   - Verify and enhance existing providers
   - Standardize interfaces
   - Enhance MoE router

---

## 💡 Decision Matrix

| Option | Impact | Effort | Dependencies | Priority |
|--------|--------|--------|--------------|----------|
| Router TODOs | 🔴 High | Medium | None | **1st** |
| Tool Calling Pipeline | 🔴 High | Medium | ✅ Ready | **2nd** |
| External API Wrappers | 🟡 Medium | Low | ✅ Ready | **3rd** |
| LLM Provider Integration | 🟡 Medium | Low | ✅ Ready | **4th** |

---

## 🚀 Quick Start Commands

### To work on Router TODOs:
```bash
# Focus on projects router first
cd apps/api/routers
# Implement database queries using existing schema
# See: packages/db/schema/projects.sql
```

### To work on Tool Calling Pipeline:
```bash
# Create new package
mkdir -p packages/tool-pipeline
# Integrate with:
# - packages/openapi-tools (tools)
# - packages/integrations/ai_providers (providers)
# - packages/agents (agents)
```

---

## 📝 Notes

- **Router TODOs** are blocking actual functionality - highest priority
- **Tool Calling Pipeline** is natural next step after Epic #1
- **Providers already exist** - Epic #2 may be mostly verification
- **All Epic #1 dependencies met** - ready for tool calling

---

**Recommendation**: Start with **Router TODOs** to make the API functional, then move to **Tool Calling Pipeline** to connect everything together.

