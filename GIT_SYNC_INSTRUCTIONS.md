# Git Sync Instructions

**Date**: November 8, 2025  
**Status**: Ready for GitHub Sync

## Pre-Sync Checklist

- [x] All code complete
- [x] All tests passing
- [x] Documentation complete
- [x] No linter errors
- [x] Commit messages prepared

## Step-by-Step Sync Process

### 1. Check Current Status

```bash
cd /Users/isaacbuz/Documents/SWE
git status
git branch
git remote -v
```

### 2. Create Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feat/skills-system

# Or if branch already exists
git checkout feat/skills-system
```

### 3. Stage Files

```bash
# Stage Skills engine
git add packages/skills_engine/

# Stage Skills library
git add packages/skills-library/

# Stage API
git add apps/api/routers/skills.py
git add apps/api/tests/unit/test_skills.py
git add apps/api/tests/integration/test_skills_integration.py

# Stage Frontend
git add apps/web/app/\(dashboard\)/skills/
git add apps/web/components/skills/
git add apps/web/lib/api/skills.ts
git add apps/web/lib/hooks/use-skills.ts
git add apps/web/__tests__/

# Stage Agent Integration
git add packages/agents/skills_integration.py
git add packages/agents/skills_mixin.py
git add packages/agents/examples/skill_using_agent.py
git add packages/agents/AGENT_SKILLS_INTEGRATION.md

# Stage Database Schema
git add packages/db/schema/skills.sql

# Stage Documentation
git add *.md
git add docs/architecture/CLAUDE_SKILLS.md

# Stage GitHub files
git add .github/

# Stage config files
git add packages/skills_engine/pytest.ini
git add packages/skills_engine/requirements.txt
git add packages/skills_engine/requirements-test.txt

# Verify staged files
git status
```

### 4. Commit Changes

```bash
# Use prepared commit message
git commit -F COMMIT_MESSAGE.md

# Or commit with inline message
git commit -m "feat: Complete Skills System Implementation (Epic 6)

Implement comprehensive Skills marketplace system with execution engine,
database integration, REST API, marketplace UI, built-in Skills library,
and agent integration.

Closes #54, #55, #56, #57, #58, #61, #64, #65
Related: #83, #84, #88"
```

### 5. Push to Remote

```bash
# Push feature branch
git push origin feat/skills-system

# Or if remote doesn't exist, add it first
# git remote add origin <repository-url>
# git push -u origin feat/skills-system
```

### 6. Create Pull Request

#### Via GitHub CLI

```bash
gh pr create \
  --title "feat: Complete Skills System Implementation (Epic 6)" \
  --body-file COMMIT_MESSAGE.md \
  --base main \
  --head feat/skills-system
```

#### Via GitHub Web Interface

1. Go to repository on GitHub
2. Click "Pull requests"
3. Click "New pull request"
4. Select `feat/skills-system` as source branch
5. Select `main` as target branch
6. Fill in title and description from `COMMIT_MESSAGE.md`
7. Add labels: `enhancement`, `skills`, `epic-6`
8. Request reviewers
9. Create pull request

### 7. Update Issues

#### Close Completed Issues

```bash
# Close Epic 6 issues
gh issue close 54 --comment "✅ Complete - Skills execution engine implemented"
gh issue close 55 --comment "✅ Complete - Database migrations created"
gh issue close 56 --comment "✅ Complete - Marketplace UI implemented"
gh issue close 57 --comment "✅ Complete - Browser and search included in #56"
gh issue close 58 --comment "✅ Complete - Detail page included in #56"
gh issue close 61 --comment "✅ Complete - 16 built-in Skills created"
gh issue close 64 --comment "✅ Complete - Agent integration implemented"
gh issue close 65 --comment "✅ Complete - Caching and optimization implemented"

# Close Epic 8 issues
gh issue close 83 --comment "✅ Complete - Skills API tests written"
gh issue close 84 --comment "✅ Complete - Skills component tests written"
gh issue close 88 --comment "✅ Complete - 80%+ test coverage achieved"
```

#### Link PR to Issues

Add to PR description:
```
Closes #54, #55, #56, #57, #58, #61, #64, #65
Related: #83, #84, #88
```

### 8. Update Milestone

```bash
# Update Epic 6 milestone
gh api repos/:owner/:repo/milestones/:milestone_number \
  -X PATCH \
  -f state=open \
  -f description="Skills Marketplace - 9/11 complete (82%)"
```

### 9. Add Labels to PR

```bash
gh pr edit <pr-number> --add-label "enhancement,skills,epic-6"
```

## Troubleshooting

### If Git Repository Not Initialized

```bash
git init
git remote add origin <repository-url>
git checkout -b main
git add .
git commit -m "Initial commit"
git push -u origin main
```

### If Remote Not Configured

```bash
# Add remote
git remote add origin <repository-url>

# Verify
git remote -v

# Push
git push -u origin feat/skills-system
```

### If Authentication Required

```bash
# GitHub CLI authentication
gh auth login

# Or use SSH
git remote set-url origin git@github.com:username/repo.git
```

### If Branch Already Exists

```bash
# Update existing branch
git checkout feat/skills-system
git merge main  # or rebase
git push origin feat/skills-system
```

## Verification

After sync, verify:

1. ✅ All files committed
2. ✅ PR created successfully
3. ✅ Issues linked to PR
4. ✅ CI/CD running
5. ✅ Tests passing
6. ✅ Code review requested

## Post-Sync

1. Monitor CI/CD pipeline
2. Address any review comments
3. Merge PR when approved
4. Deploy to staging
5. Test in staging environment

---

**Status**: Ready for sync  
**Next Step**: Run git commands above  

