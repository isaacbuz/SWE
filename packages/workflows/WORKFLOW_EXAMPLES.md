# Workflow Execution Examples

This document provides detailed examples of workflow executions with expected inputs, outputs, and behaviors.

## Table of Contents

- [Plan-Patch-PR Workflow](#plan-patch-pr-workflow)
- [Incident Swarm Workflow](#incident-swarm-workflow)
- [Code Migration Workflow](#code-migration-workflow)
- [Quality Gate Workflow](#quality-gate-workflow)

## Plan-Patch-PR Workflow

### Example 1: Simple Feature Addition

**Input:**

```python
requirement = "Add user profile page with avatar upload"
auto_merge = False
```

**Execution Flow:**

1. **Chief Architect Phase** (2-3 minutes)
   - Analyzes requirement
   - Creates design document
   - Identifies components: frontend, backend, storage

2. **Planner Phase** (1-2 minutes)
   - Breaks down into issues:
     - Issue 1: Create user profile API endpoint
     - Issue 2: Implement avatar storage service
     - Issue 3: Build profile page UI
     - Issue 4: Add profile tests

3. **Parallel Code Generation** (5-10 minutes)
   - 4 coders work in parallel
   - Each generates code for one issue
   - Produces patches with implementation and tests

4. **Quality Gates** (3-5 minutes)
   - Tests: 48/48 passed ✓
   - Linting: 2 issues found (auto-fixed) ✓
   - Security: No vulnerabilities ✓
   - Coverage: 87.5% ✓

5. **PR Creation** (30 seconds)
   - Creates branch: `feature/add-user-profile-page`
   - Opens PR with detailed description
   - Adds labels: automated, feature

**Output:**

```python
PRResult(
    pr_number=456,
    pr_url="https://github.com/org/repo/pull/456",
    branch_name="feature/add-user-profile-page",
    files_changed=[
        "backend/api/profile.py",
        "backend/services/avatar_storage.py",
        "frontend/pages/Profile.tsx",
        "tests/test_profile.py"
    ],
    test_results={
        'passed': True,
        'total': 48,
        'coverage': 87.5
    },
    qa_score=92.5,
    merged=False,
)
```

**Timeline:**

- Total duration: 12-18 minutes
- Parallel efficiency: 60% time saved vs sequential

### Example 2: Bug Fix with Auto-Merge

**Input:**

```python
requirement = "Fix memory leak in background job processor"
auto_merge = True
```

**Execution Flow:**

1. Chief Architect identifies root cause
2. Planner creates single focused issue
3. Coder generates fix
4. Quality gates pass (100% on all metrics)
5. PR auto-merged to main

**Output:**

```python
PRResult(
    pr_number=457,
    pr_url="https://github.com/org/repo/pull/457",
    branch_name="bugfix/fix-memory-leak-in-background-job",
    files_changed=["workers/job_processor.py"],
    test_results={'passed': True, 'total': 12, 'coverage': 95.0},
    qa_score=98.0,
    merged=True,
    merge_commit_sha="abc123def456",
)
```

**Timeline:**

- Total duration: 6-8 minutes
- Auto-merged in 7 minutes from start

## Incident Swarm Workflow

### Example 1: Database Connection Pool Exhaustion

**Input:**

```python
alert = {
    'id': 'alert-db-001',
    'severity': 'critical',
    'service': 'api-service',
    'message': 'Database connection pool exhausted',
    'timestamp': '2024-01-15T14:32:00Z',
    'metrics': {
        'error_rate': 15.5,
        'response_time_p95': 5000,
        'active_connections': 100,
        'max_connections': 100,
    },
    'logs': [],
}
num_diagnostic_agents = 3
auto_fix = True
```

**Execution Flow:**

1. **Context Gathering** (30 seconds)
   - Fetches metrics: High connection usage, timeout errors
   - Fetches logs: Connection refused errors

2. **Parallel Diagnosis** (2-3 minutes)
   - Agent 1 diagnosis:
     - Root cause: "Connection pool too small for traffic"
     - Confidence: 0.85
     - Evidence: Connection count at max, traffic spike

   - Agent 2 diagnosis:
     - Root cause: "Connection pool too small for traffic"
     - Confidence: 0.90
     - Evidence: Pool metrics, error patterns

   - Agent 3 diagnosis:
     - Root cause: "Database connection leak in service"
     - Confidence: 0.70
     - Evidence: Gradual connection increase

3. **Consensus Building** (10 seconds)
   - 2/3 agents agree on pool size issue
   - Overall confidence: 0.88 (high)
   - Consensus: "Connection pool too small for traffic"

4. **Fix Generation** (2 minutes)
   - Generates config change: Increase pool from 100 to 200
   - Adds monitoring for connection usage
   - Creates runbook update

5. **Testing** (1 minute)
   - Tests pass ✓
   - Validates pool configuration

6. **Hotfix PR** (30 seconds)
   - Creates PR with hotfix label
   - Severity: critical
   - Recommends immediate review

7. **Postmortem** (1 minute)
   - Generates document with timeline
   - Root cause analysis
   - Prevention measures

**Output:**

```python
IncidentResult(
    alert_id='alert-db-001',
    consensus=ConsensusResult(
        root_cause='Connection pool too small for traffic',
        confidence=0.88,
        supporting_diagnoses=[Agent1, Agent2],
        conflicting_diagnoses=[Agent3],
    ),
    fix_applied=True,
    hotfix_pr_url='https://github.com/org/repo/pull/458',
    postmortem_url='https://docs.example.com/postmortem/alert-db-001',
    resolution_time_minutes=7.5,
    rollback_performed=False,
)
```

**Timeline:**

- Detection to diagnosis: 3 minutes
- Fix generation and testing: 3 minutes
- Total resolution: 7.5 minutes

### Example 2: Low Confidence - Manual Intervention

**Input:**

```python
alert = {
    'id': 'alert-perf-002',
    'severity': 'high',
    'service': 'recommendation-engine',
    'message': 'Elevated latency in recommendations',
    'timestamp': '2024-01-15T15:00:00Z',
}
```

**Execution Flow:**

1. Context gathering
2. Parallel diagnosis yields conflicting results:
   - Agent 1: Database query slow (confidence: 0.60)
   - Agent 2: ML model performance (confidence: 0.55)
   - Agent 3: Cache invalidation issue (confidence: 0.65)

3. Consensus: 0.60 (below 0.70 threshold)

4. **No auto-fix applied** - Creates manual issue instead

**Output:**

```python
IncidentResult(
    alert_id='alert-perf-002',
    consensus=ConsensusResult(
        root_cause='Cache invalidation issue',
        confidence=0.60,  # Too low for auto-fix
        ...
    ),
    fix_applied=False,
    hotfix_pr_url=None,
    postmortem_url='https://docs.example.com/postmortem/alert-perf-002',
    resolution_time_minutes=4.0,
    rollback_performed=False,
)
```

## Code Migration Workflow

### Example 1: React 16 → 18 Upgrade

**Input:**

```python
migration_type = "react-upgrade"
source_version = "16.14.0"
target_version = "18.2.0"
incremental = True
auto_rollback = True
```

**Execution Flow:**

1. **Codebase Analysis** (5 minutes)
   - Scans 500 files
   - Identifies 42 files using React
   - Finds deprecated APIs: componentWillMount, findDOMNode

2. **Migration Plan** (3 minutes)
   - Creates 6 steps:
     - Step 1: Update package.json dependencies
     - Step 2: Replace deprecated lifecycle methods
     - Step 3: Update ReactDOM.render to createRoot
     - Step 4: Fix prop types and typing issues
     - Step 5: Update test utilities
     - Step 6: Update documentation

3. **Incremental Execution** (25 minutes total)

   **Step 1: Dependencies** (3 min)
   - Updates package.json
   - Runs tests: ✓ Pass
   - Validation: ✓ Pass

   **Step 2: Lifecycle Methods** (8 min)
   - Replaces componentWillMount with useEffect
   - Updates 15 components
   - Tests: ✓ Pass

   **Step 3: ReactDOM** (5 min)
   - Updates all render calls
   - Tests: ✓ Pass

   **Step 4: Types** (6 min)
   - Fixes TypeScript types
   - Tests: ✓ Pass

   **Step 5: Test Utils** (2 min)
   - Updates testing-library usage
   - Tests: ✓ Pass

   **Step 6: Docs** (1 min)
   - Updates README and docs
   - Validation: ✓ Pass

4. **PR Creation** (30 seconds)
   - Creates comprehensive PR
   - Includes migration report
   - Lists all changes by step

**Output:**

```python
MigrationResult(
    plan_name='Migration to 18.2.0',
    total_steps=6,
    completed_steps=6,
    failed_steps=0,
    step_results=[
        StepResult(step_id='step-1', success=True, ...),
        StepResult(step_id='step-2', success=True, ...),
        StepResult(step_id='step-3', success=True, ...),
        StepResult(step_id='step-4', success=True, ...),
        StepResult(step_id='step-5', success=True, ...),
        StepResult(step_id='step-6', success=True, ...),
    ],
    final_pr_url='https://github.com/org/repo/pull/459',
    rollback_performed=False,
    duration_minutes=36.5,
)
```

**Timeline:**

- Analysis and planning: 8 minutes
- Migration execution: 25 minutes
- Total duration: 36.5 minutes

### Example 2: Migration with Rollback

**Input:**

```python
migration_type = "python3-migration"
source_version = "2.7"
target_version = "3.11"
incremental = True
auto_rollback = True
```

**Execution Flow:**

1. Analysis and planning (10 min)
2. Step 1-3 succeed (15 min)
3. **Step 4 fails** - Syntax error in generated code
4. **Auto-rollback triggered**
   - Reverts step 3
   - Reverts step 2
   - Reverts step 1
5. Returns to clean state

**Output:**

```python
MigrationResult(
    plan_name='Migration to 3.11',
    total_steps=8,
    completed_steps=3,
    failed_steps=1,
    step_results=[...],
    final_pr_url=None,
    rollback_performed=True,
    duration_minutes=28.0,
)
```

## Quality Gate Workflow

### Example 1: All Checks Pass

**Input:**

```python
pr_number = 123
branch = "feature/add-notifications"
attempt_auto_fix = True
required_coverage = 80.0
required_score = 85.0
```

**Execution Flow:**

1. **Parallel Quality Checks** (5 minutes)
   - Unit tests: 50/50 passed ✓
   - Integration tests: 15/15 passed ✓
   - Linting: 3 issues found (auto-fixed) ✓
   - Security: No vulnerabilities ✓
   - Coverage: 88.5% ✓
   - Performance: No regressions ✓
   - Dependencies: Up to date ✓
   - Static analysis: Score 94 ✓

2. **Auto-fixes Applied** (2 minutes)
   - Fixed 3 linting issues
   - Re-ran checks: All pass

3. **PR Update**
   - Status: Success ✓
   - Comment added with detailed results

**Output:**

```python
QualityGateResult(
    pr_number=123,
    all_checks_passed=True,
    required_checks_passed=True,
    can_merge=True,
    checks=[...],  # 8 checks, all passed
    overall_score=93.5,
    auto_fixes_applied=True,
    blocking_issues=[],
)
```

### Example 2: Blocking Issues

**Input:**

```python
pr_number = 124
branch = "feature/new-api"
attempt_auto_fix = True
required_coverage = 80.0
required_score = 85.0
```

**Execution Flow:**

1. **Quality Checks**
   - Tests: 45/50 passed ✗ (5 failures)
   - Coverage: 65% ✗ (below threshold)
   - Security: 1 critical vulnerability ✗

2. **Auto-fix Attempts**
   - Linting: Fixed ✓
   - Coverage: Improved to 72% (still below threshold) ✗
   - Tests: Cannot auto-fix ✗

3. **PR Update**
   - Status: Failure ✗
   - Blocking issues listed
   - Cannot merge

**Output:**

```python
QualityGateResult(
    pr_number=124,
    all_checks_passed=False,
    required_checks_passed=False,
    can_merge=False,
    checks=[...],
    overall_score=68.5,
    auto_fixes_applied=True,
    blocking_issues=[
        '[Unit Tests] 5 test failures',
        '[Code Coverage] Coverage 72% < required 80%',
        '[Security Scan] Critical: SQL injection vulnerability',
    ],
)
```

## Workflow Patterns

### Pattern 1: Human-in-the-Loop

For workflows requiring human approval:

```python
# Workflow waits for signal
await workflow.wait_condition(lambda: self.approved)

# Human reviews and signals
await client.signal_workflow(workflow_id, "approve")
```

### Pattern 2: Compensating Transactions

For rollback scenarios:

```python
try:
    result = await execute_operation()
except Exception:
    await compensate_operation()
    raise
```

### Pattern 3: Saga Pattern

For complex multi-step operations:

```python
completed_steps = []
try:
    for step in steps:
        result = await execute_step(step)
        completed_steps.append(result)
except Exception:
    # Rollback in reverse order
    for step in reversed(completed_steps):
        await rollback_step(step)
```

## Performance Metrics

### Typical Execution Times

| Workflow       | Simple    | Medium    | Complex   |
| -------------- | --------- | --------- | --------- |
| Plan-Patch-PR  | 8-12 min  | 15-25 min | 30-45 min |
| Incident Swarm | 4-8 min   | 8-15 min  | 15-30 min |
| Code Migration | 20-40 min | 40-80 min | 2-4 hours |
| Quality Gate   | 3-5 min   | 5-10 min  | 10-20 min |

### Parallelization Benefits

- Code generation: 3-4x faster with parallel execution
- Quality checks: 8x faster (8 checks in parallel)
- Incident diagnosis: 3x faster (3 agents in parallel)

### Resource Usage

- Worker memory: ~200MB per worker
- Activity memory: ~50-100MB per activity
- Network: Low (mostly API calls)
- CPU: Medium during code analysis

## Debugging Tips

### View Workflow History

```bash
temporal workflow show \
  --workflow-id plan-patch-pr-12345 \
  --namespace default
```

### Replay Failed Workflow

```bash
temporal workflow reset \
  --workflow-id plan-patch-pr-12345 \
  --event-id 10
```

### Query Workflow State

```python
status = await client.get_workflow_status(workflow_id)
print(f"Current state: {status}")
```

### Monitor Metrics

```bash
# Worker metrics
temporal workflow list --query 'WorkflowType="PlanPatchPRWorkflow"'

# Activity metrics
temporal activity list --workflow-id plan-patch-pr-12345
```
