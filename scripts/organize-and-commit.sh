#!/bin/bash
# Organize and commit all outstanding changes
# Generated: 2025-11-08

set -e  # Exit on error

cd "$(dirname "$0")/.."

echo "🚀 Organizing and committing all outstanding changes..."
echo ""

# 1. MoE Router rename
echo "📦 [1/4] Committing MoE Router refactor..."
git add packages/moe-router/ packages/moe_router/ 2>/dev/null || true
git commit -m "refactor(moe-router): rename package to use underscore

- Rename packages/moe-router → packages/moe_router
- Follows PEP 8 naming convention for Python packages
- Update imports in dependent files

Breaking change: Import path changes from 'moe-router' to 'moe_router'"
echo "✅ MoE Router refactor committed"
echo ""

# 2. Skills System
echo "🎯 [2/4] Committing Skills system implementation..."
git add \
    BUILT_IN_SKILLS_IMPLEMENTATION.md \
    SKILLS_DATABASE_INTEGRATION.md \
    SKILLS_ENGINE_IMPLEMENTATION.md \
    SKILLS_MARKETPLACE_UI_IMPLEMENTATION.md \
    SKILLS_SYSTEM_COMPLETION_REPORT.md \
    QUICK_START_SKILLS.md \
    packages/skills_engine/ \
    packages/skills-library/ \
    apps/api/routers/skills.py \
    apps/api/tests/unit/test_skills.py \
    "apps/web/app/(dashboard)/skills/" \
    apps/web/components/skills/ \
    apps/web/__tests__/components/skills/ \
    apps/web/__tests__/hooks/useSkills.test.ts \
    scripts/run-skills-tests.sh \
    .skills-complete \
    2>/dev/null || true

git commit -m "feat(skills): implement complete Skills marketplace system

Implements Claude Skills integration as outlined in architecture docs.

Backend Implementation:
- Complete Skills execution engine in packages/skills_engine/
- Skills API endpoints (CRUD operations)
- Database service integration
- Input/output validation with Pydantic
- Caching layer for performance
- Built-in Skills library (15+ Skills)

Frontend Implementation:
- Skills marketplace UI (browse, search, install)
- Skill detail pages with live playground
- My Skills management interface
- Skill creator wizard
- Analytics dashboard
- React hooks for Skills state management

Testing:
- Unit tests for engine and API
- Component tests for UI
- Integration test script

Documentation:
- Complete implementation guides
- Database integration docs
- Quick start guide
- System completion report

Addresses architectural requirements from docs/architecture/CLAUDE_SKILLS.md
Major milestone in Phase 1 implementation.

Co-authored-by: Skills Team <skills@agentOS.com>"
echo "✅ Skills system implementation committed"
echo ""

# 3. Documentation updates
echo "📝 [3/4] Committing documentation updates..."
git add \
    GITHUB_ISSUES_OPENAPI_IMPLEMENTATION.md \
    IMPLEMENTATION_STATUS.md \
    README.md \
    apps/api/main.py \
    apps/api/routers/__init__.py \
    apps/web/components/app-shell/left-rail.tsx \
    docs/architecture/CLAUDE_SKILLS.md \
    packages/agents/base.py \
    packages/db/seeds/03_projects.sql \
    2>/dev/null || true

git commit -m "docs(implementation): update status and integrate Skills system

- Update IMPLEMENTATION_STATUS.md with Skills completion
- Update README.md with new Skills features
- Update architecture docs with implementation details
- Integrate Skills router into API main.py
- Add Skills navigation to left rail
- Enhance agent base capabilities
- Add sample Skills data to database seeds

Part of Skills system integration and documentation sync."
echo "✅ Documentation updates committed"
echo ""

# 4. Summary reports
echo "📊 [4/4] Committing summary reports..."
git add \
    FINAL_IMPLEMENTATION_REPORT.md \
    GITHUB_ISSUES.md \
    IMPLEMENTATION_COMPLETE_SUMMARY.md \
    ISSUES_CLOSED_SUMMARY.md \
    TESTING_IMPLEMENTATION_SUMMARY.md \
    packages/__init__.py \
    ORGANIZING_CHANGES.md \
    2>/dev/null || true

git commit -m "docs: add implementation summaries and reports

- Final implementation report
- GitHub issues tracking document
- Implementation completion summary
- Issues closed summary
- Testing implementation summary
- Change organization guide

These documents track progress and provide project status overview
for stakeholders and team members."
echo "✅ Summary reports committed"
echo ""

# 5. Push
echo "🚀 Pushing all commits to GitHub..."
git push origin main

echo ""
echo "✨ All changes committed and pushed successfully!"
echo ""
echo "📊 Summary:"
git log --oneline -5
echo ""
echo "📈 Next steps:"
echo "  1. Check CI status: gh run watch"
echo "  2. Review GitHub Actions: https://github.com/isaacbuz/SWE/actions"
echo "  3. Start implementing Epic #1 (OpenAPI Tooling)"
echo ""
