# Quick Start Guide

Get up and running with Temporal workflows in 5 minutes.

## Prerequisites

- Python 3.11+
- Temporal Server (or Temporal CLI for local development)

## Installation

### 1. Install Temporal CLI (for local development)

```bash
# macOS
brew install temporal

# Linux
curl -sSf https://temporal.download/cli.sh | sh

# Windows
Download from https://github.com/temporalio/cli/releases
```

### 2. Install Python Dependencies

```bash
cd packages/workflows
pip install -r requirements.txt
```

## Start Temporal Server

```bash
# Start local Temporal server with Web UI
temporal server start-dev

# Server runs on localhost:7233
# Web UI available at http://localhost:8233
```

## Run Your First Workflow

### 1. Start the Worker

Open a terminal and start the worker:

```bash
python worker.py
```

You should see:

```
INFO - Autonomous Coding System - Temporal Worker
INFO - Connected to Temporal namespace: default
INFO - Worker is ready to process workflows and activities
INFO - Listening on task queue: autonomous-coding-task-queue
```

### 2. Execute a Workflow

Open another terminal and run an example:

```bash
# Plan-Patch-PR example
python client.py plan_patch_pr
```

Expected output:

```
Workflow started: plan-patch-pr-1234567890
Workflow URL: http://localhost:8233/namespaces/default/workflows/plan-patch-pr-1234567890

Workflow completed!
PR URL: https://github.com/org/repo/pull/456
Files changed: 4
Quality score: 92.5
```

### 3. View in Web UI

Open http://localhost:8233 and:

- Navigate to "Workflows"
- Find your workflow by ID
- Click to view execution history
- Inspect activity results and timeline

## Available Examples

```bash
# Feature development workflow
python client.py plan_patch_pr

# Incident response workflow
python client.py incident_response

# Code migration workflow
python client.py migration
```

## Programmatic Usage

### Example: Start a Workflow

```python
import asyncio
from workflows.client import WorkflowClient

async def main():
    # Create client
    client = WorkflowClient()

    # Start workflow
    handle = await client.start_plan_patch_pr(
        requirement="Add user authentication",
        auto_merge=False,
    )

    print(f"Workflow started: {handle.id}")

    # Wait for result
    result = await client.wait_for_result(handle.id)

    print(f"PR created: {result.pr_url}")
    print(f"Quality score: {result.qa_score}")

    # Clean up
    await client.disconnect()

# Run
asyncio.run(main())
```

### Example: Query Workflow Status

```python
async def check_status():
    client = WorkflowClient()

    status = await client.get_workflow_status("plan-patch-pr-1234567890")

    print(f"Design created: {status['has_design']}")
    print(f"Issues: {status['issues_count']}")
    print(f"Patches: {status['patches_count']}")
    print(f"PR created: {status['pr_created']}")

    await client.disconnect()

asyncio.run(check_status())
```

### Example: Send Signal to Workflow

```python
async def cancel_workflow():
    client = WorkflowClient()

    # Cancel a running workflow
    await client.cancel_workflow("plan-patch-pr-1234567890")

    print("Workflow cancelled")

    await client.disconnect()

asyncio.run(cancel_workflow())
```

## Common Workflows

### 1. Plan-Patch-PR (Feature Development)

**Use Case:** Implement a new feature from requirement to PR

```python
handle = await client.start_plan_patch_pr(
    requirement="Add OAuth2 authentication with Google provider",
    auto_merge=False,
)
```

**Duration:** 12-45 minutes depending on complexity

**Output:** Pull request with implementation, tests, and quality report

### 2. Incident Response

**Use Case:** Diagnose and fix production incidents

```python
alert = {
    'id': 'alert-123',
    'severity': 'critical',
    'service': 'api-service',
    'message': 'High error rate detected',
    'timestamp': '2024-01-15T12:00:00Z',
}

handle = await client.start_incident_response(
    alert=alert,
    num_diagnostic_agents=3,
    auto_fix=True,
)
```

**Duration:** 4-30 minutes depending on complexity

**Output:** Hotfix PR and postmortem document

### 3. Code Migration

**Use Case:** Migrate codebase to new version/framework

```python
handle = await client.start_code_migration(
    migration_type="react-upgrade",
    source_version="16.14.0",
    target_version="18.2.0",
    incremental=True,
    auto_rollback=True,
)
```

**Duration:** 20 minutes - 4 hours depending on size

**Output:** Migration PR with all changes

### 4. Quality Gate

**Use Case:** Run quality checks on a pull request

```python
handle = await client.start_quality_gate(
    pr_number=123,
    branch="feature/new-feature",
    attempt_auto_fix=True,
    required_coverage=80.0,
    required_score=85.0,
)
```

**Duration:** 3-20 minutes depending on test suite

**Output:** Quality report with pass/fail status

## Configuration

### Custom Temporal Server

```python
client = WorkflowClient(
    temporal_host="temporal.example.com:7233",
    namespace="production",
    task_queue="my-custom-queue",
)
```

### Multiple Workers

For better throughput, run multiple workers:

```bash
python worker.py --workers 3
```

### Environment Variables

```bash
export TEMPORAL_HOST="localhost:7233"
export TEMPORAL_NAMESPACE="default"
export TEMPORAL_TASK_QUEUE="autonomous-coding-task-queue"
```

## Troubleshooting

### Worker Not Connecting

**Problem:** Worker fails to connect to Temporal

**Solution:**

1. Ensure Temporal server is running: `temporal server start-dev`
2. Check connection: `telnet localhost 7233`
3. Verify namespace exists

### Workflow Times Out

**Problem:** Workflow exceeds timeout

**Solution:**

1. Increase timeout in `config.py`
2. Check activity execution times
3. Review worker logs for bottlenecks

### Activity Fails

**Problem:** Activity fails with error

**Solution:**

1. Check worker logs for error details
2. Verify retry policy in `config.py`
3. Review activity implementation

### Workflow Stuck

**Problem:** Workflow appears stuck

**Solution:**

1. Check Temporal Web UI for workflow history
2. Look for pending activities
3. Check worker health and availability

## Next Steps

1. **Read Documentation:** See [README.md](README.md) for full documentation
2. **Explore Examples:** Check [WORKFLOW_EXAMPLES.md](WORKFLOW_EXAMPLES.md) for detailed examples
3. **Customize Workflows:** Modify workflow implementations for your use case
4. **Implement Activities:** Replace stub activities with real implementations
5. **Configure Settings:** Adjust timeouts and thresholds in `config.py`

## Useful Commands

### Temporal CLI Commands

```bash
# List workflows
temporal workflow list

# Show workflow details
temporal workflow show --workflow-id plan-patch-pr-123

# Describe workflow
temporal workflow describe --workflow-id plan-patch-pr-123

# Cancel workflow
temporal workflow cancel --workflow-id plan-patch-pr-123

# Terminate workflow
temporal workflow terminate --workflow-id plan-patch-pr-123

# Query workflow
temporal workflow query \
  --workflow-id plan-patch-pr-123 \
  --type get_status

# Signal workflow
temporal workflow signal \
  --workflow-id plan-patch-pr-123 \
  --name cancel_workflow
```

### Worker Management

```bash
# Start single worker
python worker.py

# Start with custom host
python worker.py --host temporal.example.com:7233

# Start multiple workers
python worker.py --workers 3

# Start with custom namespace
python worker.py --namespace production

# Start with custom task queue
python worker.py --task-queue custom-queue
```

## Production Checklist

Before deploying to production:

- [ ] Configure production Temporal server
- [ ] Set appropriate timeouts in `config.py`
- [ ] Implement real agent activities
- [ ] Add authentication/authorization
- [ ] Set up monitoring and alerts
- [ ] Configure logging aggregation
- [ ] Test error scenarios
- [ ] Document runbooks
- [ ] Set up high availability (multiple workers)
- [ ] Enable TLS for Temporal connection

## Support and Resources

- **Documentation:** [README.md](README.md)
- **Examples:** [WORKFLOW_EXAMPLES.md](WORKFLOW_EXAMPLES.md)
- **Implementation Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Temporal Docs:** https://docs.temporal.io
- **Temporal Community:** https://community.temporal.io
- **Temporal Samples:** https://github.com/temporalio/samples-python

## License

MIT
