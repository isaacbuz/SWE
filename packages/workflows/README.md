# Temporal Workflows for Autonomous Coding System

This package implements Temporal workflows for orchestrating autonomous software development tasks, including development flows, incident response, code migrations, and quality gates.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Activities](#activities)
- [Setup](#setup)
- [Usage](#usage)
- [Examples](#examples)
- [Monitoring](#monitoring)

## Overview

The workflows package provides durable, fault-tolerant orchestration for complex software development tasks using [Temporal](https://temporal.io/). Key features:

- **Durable Execution**: Workflows survive crashes and restarts
- **Parallel Execution**: Multiple agents work concurrently
- **Error Handling**: Automatic retries and compensation logic
- **Versioning**: Support for workflow evolution
- **Observability**: Built-in monitoring and debugging

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Temporal Server                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Workflow   │  │   Activity   │  │    Event     │    │
│  │   Histories  │  │    Queue     │  │   History    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
           ▲                    │                    ▲
           │                    │                    │
           │                    ▼                    │
      ┌────┴─────┐      ┌──────────────┐      ┌────┴─────┐
      │  Client  │      │    Worker    │      │  Client  │
      │          │      │              │      │          │
      │ - Start  │      │ - Workflows  │      │ - Query  │
      │ - Signal │      │ - Activities │      │ - Signal │
      │ - Query  │      │ - Polling    │      │ - Cancel │
      └──────────┘      └──────────────┘      └──────────┘
```

## Workflows

### 1. Plan-Patch-PR Workflow

Orchestrates the complete development cycle from requirement to merged PR.

```
┌─────────────────────────────────────────────────────────────┐
│                  Plan-Patch-PR Workflow                     │
└─────────────────────────────────────────────────────────────┘

  User Requirement
        │
        ▼
  ┌─────────────────────┐
  │ Chief Architect     │ ──► Design Document
  │ Creates Design      │
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Planner Breaks      │ ──► List of Issues
  │ Down into Issues    │
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────┐
  │  Parallel Code Generation           │
  │                                     │
  │  ┌────────┐ ┌────────┐ ┌────────┐ │
  │  │Coder 1 │ │Coder 2 │ │Coder 3 │ │ ──► Patches
  │  └────────┘ └────────┘ └────────┘ │
  └─────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────┐
  │  Quality Gates (Parallel)           │
  │                                     │
  │  ┌────────┐ ┌────────┐ ┌────────┐ │
  │  │ Tests  │ │Linting │ │Security│ │ ──► QA Results
  │  └────────┘ └────────┘ └────────┘ │
  └─────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Auto-Fix Issues?    │
  │ (if enabled)        │ ──► Fixed Patches
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Create Pull Request │ ──► PR URL
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Auto-Merge?         │ ──► Merged PR
  │ (if all checks pass)│
  └─────────────────────┘
```

**Key Features:**
- Parallel code generation for multiple issues
- Concurrent quality checks
- Automatic fixes for linting and coverage issues
- Conditional auto-merge based on quality score
- Saga pattern for rollback

**Usage:**
```python
from workflows.client import WorkflowClient

client = WorkflowClient()
handle = await client.start_plan_patch_pr(
    requirement="Add user authentication with OAuth2",
    auto_merge=False,
)
result = await client.wait_for_result(handle.id)
```

### 2. Incident Swarm Workflow

Coordinates multiple agents to diagnose and fix production incidents.

```
┌─────────────────────────────────────────────────────────────┐
│               Incident Swarm Workflow                       │
└─────────────────────────────────────────────────────────────┘

  Production Alert
        │
        ▼
  ┌─────────────────────────────────────┐
  │  Gather Context (Parallel)          │
  │                                     │
  │  ┌──────────┐     ┌──────────┐    │
  │  │ Metrics  │     │   Logs   │    │ ──► Context Data
  │  └──────────┘     └──────────┘    │
  └─────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────┐
  │  Parallel Diagnosis (Swarm)         │
  │                                     │
  │  ┌────────┐ ┌────────┐ ┌────────┐ │
  │  │Agent 1 │ │Agent 2 │ │Agent 3 │ │ ──► Diagnoses
  │  └────────┘ └────────┘ └────────┘ │
  └─────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Build Consensus     │
  │ on Root Cause       │ ──► Consensus (with confidence)
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Confidence > 70%?   │
  └─────────────────────┘
        │
        ├─── Yes ──►┌─────────────────────┐
        │           │ Generate Fix        │ ──► Fix Patch
        │           └─────────────────────┘
        │                    │
        │                    ▼
        │           ┌─────────────────────┐
        │           │ Test Fix            │
        │           └─────────────────────┘
        │                    │
        │                    ▼
        │           ┌─────────────────────┐
        │           │ Create Hotfix PR    │ ──► Hotfix PR URL
        │           └─────────────────────┘
        │
        └─── No ──►┌─────────────────────┐
                   │ Create Manual Issue │ ──► Issue for humans
                   └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Generate Postmortem │ ──► Postmortem Document
  └─────────────────────┘
```

**Key Features:**
- Multiple diagnostic agents run in parallel
- Consensus-based root cause analysis
- Confidence-weighted decision making
- Automatic fix generation and testing
- Postmortem document generation
- Rollback capability via signals

**Usage:**
```python
alert = {
    'id': 'alert-123',
    'severity': 'critical',
    'service': 'api-service',
    'message': 'High error rate detected',
    'timestamp': '2024-01-01T12:00:00Z',
}

handle = await client.start_incident_response(
    alert=alert,
    num_diagnostic_agents=3,
    auto_fix=True,
)
```

### 3. Code Migration Workflow

Manages large-scale code migrations with incremental steps and validation.

```
┌─────────────────────────────────────────────────────────────┐
│               Code Migration Workflow                       │
└─────────────────────────────────────────────────────────────┘

  Migration Request
  (e.g., React 16 → 18)
        │
        ▼
  ┌─────────────────────┐
  │ Analyze Codebase    │ ──► Analysis Report
  │ (patterns, deps)    │     (files affected, complexity)
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Generate Migration  │ ──► Migration Plan
  │ Plan with Steps     │     (ordered steps with deps)
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Create Migration    │
  │ Branch              │
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────┐
  │  Execute Steps (Dependency Graph)   │
  │                                     │
  │         Step 1 (deps: [])           │
  │              │                      │
  │         ┌────┴────┐                │
  │         │         │                │
  │      Step 2    Step 3              │
  │      (deps: [1]) (deps: [1])       │
  │         │         │                │
  │         └────┬────┘                │
  │              │                      │
  │          Step 4                     │
  │      (deps: [2,3])                 │
  └─────────────────────────────────────┘
        │
        │ (For each step)
        ▼
  ┌─────────────────────┐
  │ Generate Changes    │ ──► Code Changes
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Run Tests           │
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Validate Migration  │
  └─────────────────────┘
        │
        ├─── Pass ──► Continue to next step
        │
        └─── Fail ──►┌─────────────────────┐
                     │ Rollback Migration  │
                     │ (if auto_rollback)  │
                     └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Create Migration PR │ ──► PR with all changes
  └─────────────────────┘
```

**Key Features:**
- Dependency-aware step execution
- Validation at each step
- Automatic rollback on failure
- Incremental or batch migration modes
- Pause/resume capability via signals
- Detailed migration report

**Usage:**
```python
handle = await client.start_code_migration(
    migration_type="react-upgrade",
    source_version="16.14.0",
    target_version="18.2.0",
    incremental=True,
    auto_rollback=True,
)
```

### 4. Quality Gate Workflow

Runs comprehensive quality checks on PRs with automated fixes.

```
┌─────────────────────────────────────────────────────────────┐
│                 Quality Gate Workflow                       │
└─────────────────────────────────────────────────────────────┘

  Pull Request
        │
        ▼
  ┌─────────────────────┐
  │ Update PR Status    │ ──► Status: Pending
  │ to "Checking"       │
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Run All Checks in Parallel                             │
  │                                                         │
  │  ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌─────────┐ │
  │  │Unit  │ │ Int. │ │Linting │ │Security│ │Coverage │ │
  │  │Tests │ │Tests │ │        │ │ Scan   │ │  Check  │ │
  │  └──────┘ └──────┘ └────────┘ └────────┘ └─────────┘ │
  │                                                         │
  │  ┌──────┐ ┌────────┐ ┌────────┐                       │
  │  │Perf. │ │  Deps  │ │ Static │                       │
  │  │Tests │ │ Check  │ │Analysis│                       │
  │  └──────┘ └────────┘ └────────┘                       │
  └─────────────────────────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Calculate Overall   │ ──► Quality Score
  │ Quality Score       │     Check Results
  └─────────────────────┘
        │
        ▼
  ┌─────────────────────┐
  │ Auto-fixable Issues?│
  └─────────────────────┘
        │
        ├─── Yes ──►┌─────────────────────┐
        │           │ Apply Auto-fixes    │
        │           │ - Linting           │
        │           │ - Coverage          │
        │           │ - Static Analysis   │
        │           └─────────────────────┘
        │                    │
        │                    ▼
        │           ┌─────────────────────┐
        │           │ Re-run All Checks   │
        │           └─────────────────────┘
        │
        └─── No ──► Continue
        │
        ▼
  ┌─────────────────────┐
  │ Update PR Status    │
  │ and Add Comment     │
  └─────────────────────┘
        │
        ├─── All Checks Pass ──► Status: Success ✅
        │                        Can Merge: Yes
        │
        └─── Some Checks Fail ──► Status: Failure ❌
                                  Can Merge: No
                                  Blocking Issues Listed
```

**Key Features:**
- 8 parallel quality checks
- Automatic fixes for common issues
- Weighted quality scoring
- Required vs. optional checks
- Detailed PR comments
- Auto-fix reporting

**Usage:**
```python
handle = await client.start_quality_gate(
    pr_number=123,
    branch="feature/new-feature",
    attempt_auto_fix=True,
    required_coverage=80.0,
    required_score=85.0,
)
```

## Activities

Activities are the basic units of work executed by workers. They are organized into three categories:

### Agent Activities (`activities/agent_activities.py`)

Invoke various agents for different tasks:

- `create_design(requirement)` - Chief Architect creates design
- `create_issues(design)` - Planner breaks down into issues
- `generate_code(issue)` - Coder generates code
- `review_code(patches)` - Reviewer reviews and fixes code
- `diagnose_issue(alert, agent_id)` - Agent diagnoses incident
- `generate_fix(consensus)` - Generate fix from consensus
- `analyze_codebase(migration_type)` - Analyze code for migration
- `create_migration_plan(analysis)` - Create migration plan
- `generate_migration_step(step)` - Generate migration changes

### GitHub Activities (`activities/github_activities.py`)

Interact with GitHub API:

- `create_branch(name, base)` - Create Git branch
- `create_pull_request(data)` - Create PR
- `merge_pull_request(pr_number)` - Merge PR
- `create_issue(data)` - Create issue
- `update_pr_status(pr_number, state)` - Update status check
- `add_pr_comment(pr_number, comment)` - Add comment
- `create_commit(branch, files, message)` - Create commit
- `push_branch(branch)` - Push to remote

### Tool Activities (`activities/tool_activities.py`)

Execute development tools:

- `run_tests(target, type)` - Run tests
- `run_linters(target)` - Run linters
- `run_security_scan(target)` - Security scanning
- `run_performance_tests(branch)` - Performance tests
- `check_code_coverage(branch)` - Coverage check
- `check_dependencies(branch)` - Dependency vulnerabilities
- `run_static_analysis(branch)` - Static analysis
- `fetch_metrics(service, timestamp)` - Fetch metrics
- `fetch_logs(service, timestamp)` - Fetch logs

## Setup

### Prerequisites

1. **Temporal Server**: Running locally or in the cloud
2. **Python 3.11+**: For async/await support
3. **Dependencies**: Install via pip

### Installation

```bash
# Install Temporal CLI (for local development)
brew install temporal

# Start Temporal server (local)
temporal server start-dev

# Install Python dependencies
pip install temporalio
```

### Project Structure

```
packages/workflows/
├── workflows/
│   ├── __init__.py
│   ├── plan_patch_pr.py        # Main development workflow
│   ├── incident_swarm.py        # Incident response
│   ├── migration.py             # Code migration
│   └── quality_gate.py          # Quality checks
├── activities/
│   ├── __init__.py
│   ├── agent_activities.py      # Agent invocations
│   ├── github_activities.py     # GitHub operations
│   └── tool_activities.py       # Tool executions
├── worker.py                    # Temporal worker
├── client.py                    # Workflow client
└── README.md                    # This file
```

## Usage

### Starting the Worker

The worker polls for tasks and executes workflows/activities:

```bash
# Start a single worker
python worker.py

# Start with custom configuration
python worker.py \
  --host localhost:7233 \
  --namespace default \
  --task-queue autonomous-coding-task-queue

# Start multiple workers for better throughput
python worker.py --workers 3
```

### Using the Client

#### Plan-Patch-PR Workflow

```python
from workflows.client import WorkflowClient

client = WorkflowClient()

# Start workflow
handle = await client.start_plan_patch_pr(
    requirement="Add user authentication with OAuth2 support",
    auto_merge=False,
)

print(f"Workflow started: {handle.id}")

# Query status
status = await client.get_workflow_status(handle.id)
print(f"Progress: {status}")

# Wait for result
result = await client.wait_for_result(handle.id)
print(f"PR created: {result.pr_url}")
print(f"Quality score: {result.qa_score}")
```

#### Incident Response Workflow

```python
# Create alert
alert = {
    'id': 'alert-123',
    'severity': 'critical',
    'service': 'api-service',
    'message': 'Database connection pool exhausted',
    'timestamp': '2024-01-01T12:00:00Z',
    'metrics': {'error_rate': 15.5},
    'logs': [],
}

# Start incident response
handle = await client.start_incident_response(
    alert=alert,
    num_diagnostic_agents=3,
    auto_fix=True,
)

# Wait for resolution
result = await client.wait_for_result(handle.id)
print(f"Root cause: {result.consensus.root_cause}")
print(f"Confidence: {result.consensus.confidence:.1%}")
print(f"Resolution time: {result.resolution_time_minutes:.1f} min")

if result.fix_applied:
    print(f"Hotfix PR: {result.hotfix_pr_url}")
```

#### Code Migration Workflow

```python
# Start migration
handle = await client.start_code_migration(
    migration_type="react-upgrade",
    source_version="16.14.0",
    target_version="18.2.0",
    incremental=True,
    auto_rollback=True,
)

# Poll for progress
import asyncio

while True:
    status = await client.get_workflow_status(handle.id)
    completed = status.get('completed_steps', 0)
    total = status.get('total_steps', 0)
    print(f"Progress: {completed}/{total} steps")

    if completed == total:
        break

    await asyncio.sleep(5)

# Get final result
result = await client.wait_for_result(handle.id)
print(f"Migration completed: {result.completed_steps}/{result.total_steps}")
print(f"PR: {result.final_pr_url}")
```

#### Quality Gate Workflow

```python
# Run quality gate on a PR
handle = await client.start_quality_gate(
    pr_number=123,
    branch="feature/new-feature",
    attempt_auto_fix=True,
    required_coverage=80.0,
    required_score=85.0,
)

# Wait for result
result = await client.wait_for_result(handle.id)

print(f"Quality score: {result.overall_score:.1f}%")
print(f"Can merge: {result.can_merge}")
print(f"Auto-fixes applied: {result.auto_fixes_applied}")

if result.blocking_issues:
    print("Blocking issues:")
    for issue in result.blocking_issues:
        print(f"  - {issue}")
```

### Workflow Signals

Send signals to running workflows:

```python
# Cancel a workflow
await client.signal_workflow(workflow_id, "cancel_workflow")

# Pause a migration
await client.signal_workflow(migration_id, "pause_migration")

# Resume a migration
await client.signal_workflow(migration_id, "resume_migration")

# Rollback an incident fix
await client.signal_workflow(incident_id, "rollback")
```

## Examples

Complete examples are provided in `client.py`:

```bash
# Plan-Patch-PR example
python client.py plan_patch_pr

# Incident response example
python client.py incident_response

# Code migration example
python client.py migration
```

## Monitoring

### Temporal Web UI

Access the Temporal Web UI at `http://localhost:8233` to:

- View workflow execution history
- Inspect activity results
- Debug failures
- Replay workflows

### Workflow Queries

Query workflow state without completing it:

```python
status = await client.get_workflow_status(workflow_id)

# For Plan-Patch-PR:
# {
#   'has_design': True,
#   'issues_count': 3,
#   'patches_count': 3,
#   'qa_completed': True,
#   'pr_created': True,
#   'pr_url': 'https://github.com/...'
# }

# For Incident:
# {
#   'alert_id': 'alert-123',
#   'diagnoses_count': 3,
#   'consensus_reached': True,
#   'consensus_confidence': 0.85,
#   'fix_applied': True
# }
```

### Logging

All workflows and activities emit structured logs:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Logs include:
# - Workflow start/completion
# - Activity execution
# - Errors and retries
# - Status updates
```

## Error Handling

### Automatic Retries

Activities are automatically retried on failure:

```python
@activity.defn
async def generate_code(issue):
    # Temporal will retry this activity if it fails
    # Default: exponential backoff, max 3 attempts
    ...
```

### Custom Retry Policies

Configure retry behavior per activity:

```python
await workflow.execute_activity(
    create_design,
    args=[requirement],
    start_to_close_timeout=timedelta(minutes=10),
    retry_policy=workflow.RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=10),
        backoff_coefficient=2.0,
    ),
)
```

### Saga Pattern

Workflows implement compensation logic:

```python
async def _rollback_migration(self):
    """Rollback all completed migration steps"""
    for result in reversed(self.step_results):
        if result.success and result.rollback_available:
            # Apply rollback changes
            await rollback_step(result.step_id)
```

## Advanced Features

### Child Workflows

Spawn child workflows from parent workflows:

```python
# Continuous monitoring spawns incident workflows
await workflow.execute_child_workflow(
    IncidentSwarmWorkflow.run,
    args=[alert],
    id=f"incident-{alert.id}",
)
```

### Activity Heartbeats

Long-running activities send heartbeats:

```python
@activity.defn
async def analyze_codebase(migration_type):
    activity.heartbeat("Scanning codebase")
    # ... scan files ...
    activity.heartbeat("Analyzing dependencies")
    # ... analyze deps ...
    return analysis
```

### Versioning

Support workflow evolution:

```python
# Check workflow version
version = workflow.get_version("v2", 1, 2)

if version == 1:
    # Old behavior
    pass
else:
    # New behavior
    pass
```

## Production Considerations

### Scaling

- Run multiple workers for higher throughput
- Use separate task queues for different workflow types
- Configure worker concurrency limits

### Monitoring

- Integrate with Prometheus/Grafana
- Set up alerts for workflow failures
- Monitor queue backlogs

### Security

- Use TLS for Temporal connections
- Implement authentication/authorization
- Encrypt sensitive workflow data

### Testing

- Use Temporal's test framework
- Mock activities for unit tests
- Run integration tests against test server

## License

MIT

## Support

For issues and questions:
- GitHub Issues: [link]
- Temporal Community: https://community.temporal.io
- Documentation: https://docs.temporal.io
