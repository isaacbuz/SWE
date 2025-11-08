# Example Agent Workflows

Complete workflow examples demonstrating agent orchestration for common scenarios.

## Table of Contents
1. [New Feature Development](#new-feature-development)
2. [System Refactoring](#system-refactoring)
3. [Database Migration](#database-migration)
4. [Technical Debt Resolution](#technical-debt-resolution)
5. [Emergency Bug Fix](#emergency-bug-fix)

---

## New Feature Development

**Scenario**: Build a new user authentication system from scratch

### Workflow Steps

```python
import asyncio
from agents import (
    AgentRegistry,
    ChiefArchitectAgent,
    PlannerAgent,
    CodegenAgent,
    TechnicalDirectorAgent,
    Task,
    Context,
    TaskType,
    Priority
)

async def new_feature_workflow():
    # Setup
    registry = AgentRegistry(
        moe_router=moe_router,
        anthropic_client=anthropic_client,
        openai_client=openai_client
    )

    # Register agents
    registry.register(
        "chief_architect",
        ChiefArchitectAgent,
        [TaskType.PLANNING],
        "Architecture design",
        priority=90
    )
    registry.register(
        "planner",
        PlannerAgent,
        [TaskType.PLANNING],
        "Project planning",
        priority=85
    )
    registry.register(
        "codegen",
        CodegenAgent,
        [TaskType.CODE_GENERATION],
        "Code implementation",
        priority=80
    )
    registry.register(
        "tech_director",
        TechnicalDirectorAgent,
        [TaskType.CODE_REVIEW],
        "Technical oversight",
        priority=95
    )

    context = Context(
        project_path="/path/to/project",
        config={
            "language": "python",
            "framework": "fastapi"
        }
    )

    # Step 1: Architecture Design
    print("Step 1: Architecture Design")
    arch_task = Task(
        id="auth-arch-001",
        type=TaskType.PLANNING,
        description="Design authentication system architecture",
        priority=Priority.CRITICAL,
        input_data={
            "requirements": """
                Build a secure user authentication system with:
                - Email/password registration
                - Email verification
                - OAuth integration (Google, GitHub)
                - JWT-based session management
                - Password reset flow
                - MFA support (future)
            """,
            "project_type": "web_api",
            "constraints": {
                "must_support_oauth": True,
                "max_latency_ms": 500,
                "compliance": ["GDPR", "SOC2"]
            }
        }
    )

    arch_result = await registry.execute_task(arch_task, context)

    print(f"✓ Architecture created: {len(arch_result.artifacts)} artifacts")
    print(f"  - ADRs: {len([a for a in arch_result.artifacts if 'adr' in a.lower()])}")
    print(f"  - Diagrams: {len([a for a in arch_result.artifacts if 'diagram' in a.lower()])}")

    # Step 2: Technical Review
    print("\nStep 2: Technical Review")
    review_task = Task(
        id="auth-review-001",
        type=TaskType.CODE_REVIEW,
        description="Review architecture decisions",
        priority=Priority.HIGH,
        input_data={
            "review_type": "architecture",
            "items": [
                {
                    "id": "oauth_decision",
                    "type": "architecture",
                    "description": "OAuth integration approach",
                    "details": arch_result.output["architecture_document"]
                }
            ]
        },
        dependencies=["auth-arch-001"]
    )

    review_result = await registry.execute_task(review_task, context)

    print(f"✓ Review completed: {len(review_result.output['reviews'])} decisions reviewed")

    # Only proceed if approved
    if all(r["recommendation"] == "approve" for r in review_result.output["reviews"]):
        print("  - All decisions approved")
    else:
        print("  - Some decisions need revision")
        return

    # Step 3: Project Planning
    print("\nStep 3: Project Planning")
    plan_task = Task(
        id="auth-plan-001",
        type=TaskType.PLANNING,
        description="Create implementation plan",
        priority=Priority.HIGH,
        input_data={
            "architecture_document": arch_result.output["architecture_document"],
            "adrs": [a for a in arch_result.artifacts if "adr" in a.lower()],
            "requirements": arch_task.input_data["requirements"],
            "timeline": "4 weeks"
        },
        dependencies=["auth-arch-001", "auth-review-001"]
    )

    plan_result = await registry.execute_task(plan_task, context)

    epics = plan_result.output["epics"]
    stories = plan_result.output["stories"]

    print(f"✓ Plan created:")
    print(f"  - Epics: {len(epics)}")
    print(f"  - Stories: {len(stories)}")
    print(f"  - Total story points: {plan_result.output['total_story_points']}")

    # Step 4: Implementation (Parallel)
    print("\nStep 4: Implementation")

    # Select high-priority stories for first sprint
    sprint_stories = [s for s in stories if "high" in s.get("labels", [])][:5]

    impl_tasks = []
    for story in sprint_stories:
        task = Task(
            id=f"auth-impl-{story['id']}",
            type=TaskType.CODE_GENERATION,
            description=f"Implement {story['title']}",
            priority=Priority.HIGH if "critical" in story.get("labels", []) else Priority.MEDIUM,
            input_data={
                "story": story,
                "architecture_refs": [a for a in arch_result.artifacts if "adr" in a.lower()],
                "existing_code": {}  # First sprint, no existing code
            },
            dependencies=["auth-plan-001"]
        )
        impl_tasks.append(task)

    # Execute implementations in parallel
    impl_results = await registry.execute_workflow(
        impl_tasks,
        context,
        parallel=True
    )

    successful = [r for r in impl_results if r.success]
    print(f"✓ Implementation completed:")
    print(f"  - Stories implemented: {len(successful)}/{len(impl_tasks)}")
    print(f"  - Files created: {sum(len(r.output.get('files_created', [])) for r in successful)}")
    print(f"  - Tests created: {sum(len(r.output.get('tests_created', [])) for r in successful)}")

    # Step 5: Summary
    print("\n" + "="*50)
    print("WORKFLOW SUMMARY")
    print("="*50)
    print(f"Total tasks: {len([arch_task, review_task, plan_task] + impl_tasks)}")
    print(f"Architecture artifacts: {len(arch_result.artifacts)}")
    print(f"Stories planned: {len(stories)}")
    print(f"Stories implemented: {len(successful)}")
    print(f"Total cost: ${sum(r.cost or 0 for r in [arch_result, review_result, plan_result] + impl_results):.4f}")

# Run workflow
asyncio.run(new_feature_workflow())
```

### Expected Output Structure
```
/path/to/project/
├── docs/
│   ├── architecture/
│   │   ├── decisions/
│   │   │   ├── 0001-oauth-integration.md
│   │   │   ├── 0002-jwt-sessions.md
│   │   │   └── 0003-password-hashing.md
│   │   ├── diagrams/
│   │   │   ├── c4-auth-system.md
│   │   │   └── sequence-oauth-flow.md
│   │   └── contracts/
│   │       └── auth-api.json
│   ├── planning/
│   │   ├── project_plan.md
│   │   └── backlog.json
│   └── implementation/
│       ├── implementation-story-001.md
│       └── implementation-story-002.md
├── src/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   ├── models.py
│   │   └── validators.py
│   └── ...
└── tests/
    ├── auth/
    │   ├── test_registration.py
    │   └── test_oauth.py
    └── ...
```

---

## System Refactoring

**Scenario**: Refactor legacy authentication module to improve maintainability

### Workflow Steps

```python
async def refactoring_workflow():
    registry = AgentRegistry(moe_router=moe_router)
    context = Context(project_path="/path/to/project")

    # Step 1: Code Analysis
    print("Step 1: Analyze existing code for refactoring opportunities")

    # Read existing code
    existing_code = {
        "auth/legacy_handler.py": Path("auth/legacy_handler.py").read_text(),
        "auth/utils.py": Path("auth/utils.py").read_text()
    }

    analysis_task = Task(
        id="refactor-analysis-001",
        type=TaskType.REFACTORING,
        description="Analyze authentication module for code smells",
        input_data={
            "target_files": ["auth/legacy_handler.py", "auth/utils.py"],
            "refactoring_type": "general",
            "existing_code": existing_code,
            "test_coverage": {
                "auth/legacy_handler.py": 0.65,
                "auth/utils.py": 0.45
            }
        }
    )

    analysis_result = await registry.execute_task(analysis_task, context)

    code_smells = analysis_result.output["code_smells"]
    plans = analysis_result.output["refactoring_plans"]

    print(f"✓ Analysis completed:")
    print(f"  - Code smells found: {len(code_smells)}")
    print(f"  - Refactoring plans: {len(plans)}")

    # Display critical smells
    critical_smells = [s for s in code_smells if s["severity"] == "critical"]
    if critical_smells:
        print("\n  Critical issues:")
        for smell in critical_smells:
            print(f"    - {smell['smell_type']}: {smell['file_path']}")

    # Step 2: Technical Review
    print("\nStep 2: Review refactoring plans")

    review_task = Task(
        id="refactor-review-001",
        type=TaskType.CODE_REVIEW,
        description="Review refactoring plans",
        input_data={
            "review_type": "refactoring_plan",
            "items": [
                {
                    "id": f"plan-{i}",
                    "type": "refactoring_plan",
                    "description": plan["title"],
                    "details": plan
                }
                for i, plan in enumerate(plans)
            ]
        }
    )

    review_result = await registry.execute_task(review_task, context)

    approved_plans = [
        plans[i] for i, review in enumerate(review_result.output["reviews"])
        if review["recommendation"] == "approve"
    ]

    print(f"✓ Review completed:")
    print(f"  - Plans approved: {len(approved_plans)}/{len(plans)}")

    # Step 3: Execute Refactorings
    print("\nStep 3: Apply approved refactorings")

    for i, plan in enumerate(approved_plans):
        refactor_task = Task(
            id=f"refactor-apply-{i:03d}",
            type=TaskType.REFACTORING,
            description=f"Apply: {plan['title']}",
            input_data={
                "target_files": plan.get("affected_files", []),
                "refactoring_type": "execute",
                "refactoring_plan": plan,
                "existing_code": existing_code
            }
        )

        result = await registry.execute_task(refactor_task, context)

        if result.success:
            print(f"  ✓ Applied: {plan['title']}")
        else:
            print(f"  ✗ Failed: {plan['title']} - {result.error}")

    print("\n✓ Refactoring workflow completed")

asyncio.run(refactoring_workflow())
```

---

## Database Migration

**Scenario**: Migrate from SQLite to PostgreSQL with zero downtime

### Workflow Steps

```python
async def database_migration_workflow():
    registry = AgentRegistry(moe_router=moe_router)
    context = Context(project_path="/path/to/project")

    # Step 1: Migration Analysis
    print("Step 1: Analyze migration scope and complexity")

    migration_task = Task(
        id="migrate-db-001",
        type=TaskType.CODE_GENERATION,
        description="Plan SQLite to PostgreSQL migration",
        priority=Priority.CRITICAL,
        input_data={
            "migration_type": "database_migration",
            "from_version": "SQLite 3.x",
            "to_version": "PostgreSQL 14",
            "requirements": """
                - Zero-downtime migration
                - Data validation at each step
                - Rollback capability
                - ~50GB data
                - 1M users
            """,
            "constraints": {
                "max_downtime_minutes": 0,
                "data_size_gb": 50,
                "user_count": 1000000,
                "must_validate_all_data": True
            }
        }
    )

    migration_result = await registry.execute_task(migration_task, context)

    scope = migration_result.output["scope_analysis"]
    steps = migration_result.output["migration_steps"]
    scripts = migration_result.output["migration_scripts"]

    print(f"✓ Migration analysis completed:")
    print(f"  - Complexity: {scope['estimated_complexity']}")
    print(f"  - Migration steps: {len(steps)}")
    print(f"  - Scripts generated: {len(scripts)}")
    print(f"  - Affected components: {len(scope['affected_components'])}")

    # Step 2: Review Migration Plan
    print("\nStep 2: Technical review of migration plan")

    review_task = Task(
        id="migrate-review-001",
        type=TaskType.CODE_REVIEW,
        description="Review migration plan",
        input_data={
            "review_type": "migration_plan",
            "items": [
                {
                    "id": "migration_plan",
                    "type": "migration",
                    "description": "SQLite to PostgreSQL migration plan",
                    "details": {
                        "scope": scope,
                        "steps": steps,
                        "scripts": scripts
                    }
                }
            ]
        }
    )

    review_result = await registry.execute_task(review_task, context)

    if review_result.output["reviews"][0]["recommendation"] != "approve":
        print("  ✗ Migration plan needs revision")
        print(f"  Rationale: {review_result.output['reviews'][0]['rationale']}")
        return

    print("  ✓ Migration plan approved")

    # Step 3: Execute Migration (simulated - would be done step by step in production)
    print("\nStep 3: Execute migration steps")

    print("\nMigration Steps Overview:")
    for step in steps:
        print(f"  Step {step['step_number']}: {step['title']}")
        print(f"    - Implementation: {step['implementation'][:60]}...")
        print(f"    - Validation: {step['validation'][:60]}...")
        print(f"    - Rollback: Ready")

    # In production, would execute each step with validation
    print("\n✓ Migration plan ready for execution")
    print("\nNext steps:")
    print("  1. Review generated migration guide")
    print("  2. Test in staging environment")
    print("  3. Execute step-by-step with validation")
    print("  4. Monitor metrics during migration")

    # Summary
    guide_path = [a for a in migration_result.artifacts if "migration-guide" in a][0]
    print(f"\nMigration guide: {guide_path}")

asyncio.run(database_migration_workflow())
```

---

## Technical Debt Resolution

**Scenario**: Systematically address accumulated technical debt

### Workflow Steps

```python
async def tech_debt_workflow():
    registry = AgentRegistry(moe_router=moe_router)
    context = Context(project_path="/path/to/project")

    # Step 1: Identify Technical Debt
    print("Step 1: Scan codebase for technical debt")

    # Analyze multiple modules
    modules = ["auth", "payment", "notification", "api"]
    debt_tasks = []

    for module in modules:
        task = Task(
            id=f"debt-scan-{module}",
            type=TaskType.REFACTORING,
            description=f"Analyze {module} module for technical debt",
            input_data={
                "target_files": [f"{module}/*.py"],
                "refactoring_type": "debt_analysis",
                "existing_code": load_module_code(module)
            }
        )
        debt_tasks.append(task)

    # Run scans in parallel
    debt_results = await registry.execute_workflow(
        debt_tasks,
        context,
        parallel=True
    )

    # Aggregate results
    all_smells = []
    for result in debt_results:
        all_smells.extend(result.output.get("code_smells", []))

    # Prioritize by severity
    critical = [s for s in all_smells if s["severity"] == "critical"]
    high = [s for s in all_smells if s["severity"] == "high"]
    medium = [s for s in all_smells if s["severity"] == "medium"]

    print(f"✓ Technical debt identified:")
    print(f"  - Critical: {len(critical)}")
    print(f"  - High: {len(high)}")
    print(f"  - Medium: {len(medium)}")

    # Step 2: Create Resolution Plan
    print("\nStep 2: Create resolution plan")

    plan_task = Task(
        id="debt-plan-001",
        type=TaskType.PLANNING,
        description="Create technical debt resolution plan",
        input_data={
            "architecture_document": "Current system architecture",
            "requirements": f"""
                Address technical debt identified:
                - {len(critical)} critical issues
                - {len(high)} high priority issues
                Focus on: Security, Performance, Maintainability
            """,
            "timeline": "8 weeks"
        }
    )

    plan_result = await registry.execute_task(plan_task, context)

    stories = plan_result.output["stories"]
    print(f"✓ Resolution plan created:")
    print(f"  - Stories: {len(stories)}")

    # Step 3: Execute High-Priority Fixes
    print("\nStep 3: Execute critical and high-priority fixes")

    # Address critical issues first
    critical_stories = [s for s in stories if "critical" in s.get("labels", [])][:3]

    for story in critical_stories:
        # Determine if refactoring or reimplementation
        if "refactor" in story["title"].lower():
            task_type = TaskType.REFACTORING
        else:
            task_type = TaskType.CODE_GENERATION

        fix_task = Task(
            id=f"debt-fix-{story['id']}",
            type=task_type,
            description=f"Fix: {story['title']}",
            priority=Priority.CRITICAL,
            input_data={
                "story": story,
                "existing_code": load_relevant_code(story)
            }
        )

        result = await registry.execute_task(fix_task, context)

        if result.success:
            print(f"  ✓ Fixed: {story['title']}")
        else:
            print(f"  ✗ Failed: {story['title']}")

    print("\n✓ Technical debt workflow completed")

def load_module_code(module):
    # Load all Python files in module
    return {}

def load_relevant_code(story):
    # Load code relevant to story
    return {}

asyncio.run(tech_debt_workflow())
```

---

## Emergency Bug Fix

**Scenario**: Critical production bug requires immediate fix

### Workflow Steps

```python
async def emergency_bugfix_workflow():
    registry = AgentRegistry(moe_router=moe_router)
    context = Context(project_path="/path/to/project")

    print("EMERGENCY BUG FIX WORKFLOW")
    print("="*50)

    # Step 1: Rapid Assessment
    print("\nStep 1: Assess bug and create fix story")

    bug_description = """
    CRITICAL: Authentication bypass vulnerability
    - Users can access protected endpoints without authentication
    - Affects /api/user/* endpoints
    - Discovered in production
    - ~1000 requests affected
    """

    # Create emergency story
    story = {
        "id": "HOTFIX-001",
        "title": "Fix authentication bypass vulnerability",
        "description": bug_description,
        "acceptance_criteria": [
            "All /api/user/* endpoints require authentication",
            "Existing tests pass",
            "New tests verify fix",
            "No performance regression",
            "Security audit passes"
        ],
        "labels": ["critical", "security", "hotfix"]
    }

    # Step 2: Generate Fix
    print("\nStep 2: Generate fix implementation")

    fix_task = Task(
        id="hotfix-impl-001",
        type=TaskType.CODE_GENERATION,
        description="Implement authentication fix",
        priority=Priority.CRITICAL,
        input_data={
            "story": story,
            "architecture_refs": ["ADR-0005: Authentication Middleware"],
            "existing_code": {
                "api/middleware.py": Path("api/middleware.py").read_text(),
                "api/routes.py": Path("api/routes.py").read_text()
            }
        }
    )

    fix_result = await registry.execute_task(fix_task, context)

    if not fix_result.success:
        print(f"✗ Fix generation failed: {fix_result.error}")
        return

    print("✓ Fix generated:")
    print(f"  - Files updated: {len(fix_result.output['files_updated'])}")
    print(f"  - Tests created: {len(fix_result.output['tests_created'])}")

    # Step 3: Technical Review
    print("\nStep 3: Emergency review")

    review_task = Task(
        id="hotfix-review-001",
        type=TaskType.CODE_REVIEW,
        description="Review emergency fix",
        priority=Priority.CRITICAL,
        input_data={
            "review_type": "hotfix",
            "items": [
                {
                    "id": "auth_fix",
                    "type": "security_fix",
                    "description": "Authentication bypass fix",
                    "details": {
                        "files_changed": fix_result.output["files_updated"],
                        "tests_added": fix_result.output["tests_created"]
                    }
                }
            ]
        }
    )

    review_result = await registry.execute_task(review_task, context)

    review = review_result.output["reviews"][0]

    if review["recommendation"] != "approve":
        print(f"✗ Fix not approved: {review['rationale']}")
        if review.get("modifications"):
            print("Required modifications:")
            for mod in review["modifications"]:
                print(f"  - {mod}")
        return

    print("✓ Fix approved for deployment")

    # Step 4: Deployment Checklist
    print("\nStep 4: Pre-deployment checklist")
    print("  [ ] All tests pass")
    print("  [ ] Security scan clean")
    print("  [ ] Performance tests pass")
    print("  [ ] Staging deployment successful")
    print("  [ ] Rollback plan ready")
    print("  [ ] Monitoring alerts configured")

    print("\n✓ Emergency fix ready for production deployment")

asyncio.run(emergency_bugfix_workflow())
```

---

## Workflow Best Practices

### 1. Always Use Evidence
```python
# Review evidence trail
for evidence in result.evidence:
    print(f"{evidence.source}: {evidence.description}")
```

### 2. Handle Failures Gracefully
```python
if not result.success:
    print(f"Task failed: {result.error}")
    # Implement retry logic or alternative path
    return
```

### 3. Track Costs
```python
total_cost = sum(r.cost or 0 for r in results)
print(f"Total workflow cost: ${total_cost:.4f}")
```

### 4. Use Dependencies
```python
task2 = Task(
    id="task-002",
    dependencies=["task-001"],  # Won't run until task-001 completes
    # ...
)
```

### 5. Parallel When Possible
```python
# Independent tasks can run in parallel
results = await registry.execute_workflow(
    independent_tasks,
    context,
    parallel=True
)
```

### 6. Monitor Progress
```python
# Check agent status
stats = registry.get_registry_stats()
print(f"Active agents: {stats['active_instances']}")
print(f"Tasks completed: {stats['agent_stats']}")
```
