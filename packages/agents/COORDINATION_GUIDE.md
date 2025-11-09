# Agent Coordination Guide

## Overview

This guide covers the coordination and specialized agents that manage complex multi-agent workflows, resolve conflicts, optimize resources, and handle specialized tasks like technical debt tracking, migrations, and incident response.

## Architecture

### Layer 3: Agent System - Coordination & Specialization

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Registry                          │
│  - Agent registration & discovery                       │
│  - Capability matching                                  │
│  - Load balancing                                       │
│  - Health monitoring                                    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼─────────┐ ┌────▼──────────┐ ┌───▼────────────┐
│  Coordination   │ │  Specialized   │ │   Protocol     │
│     Agents      │ │    Agents      │ │   & Messaging  │
└─────────────────┘ └────────────────┘ └────────────────┘
```

## Components

### 1. Agent Communication Protocol (`protocol.py`)

Standardized message format for inter-agent communication.

#### Message Types

```python
from packages.agents.protocol import (
    AgentMessage, MessageIntent, MessagePriority,
    HandoffRequest, HandoffReason,
    EscalationRequest, MessageBus
)

# Create a request message
message = AgentMessage.create_request(
    from_agent="codegen",
    to_agent="reviewer",
    payload={
        "pr_id": "123",
        "changes": ["file1.py", "file2.py"]
    },
    priority=MessagePriority.HIGH
)

# Create a handoff
handoff = HandoffRequest.create(
    from_agent="codegen",
    to_agent="security_auditor",
    reason=HandoffReason.NEEDS_SPECIALIST,
    context={"pr_id": "123"},
    work_state={"files_modified": ["auth.py"]}
)

# Escalate to human
escalation = EscalationRequest.create(
    from_agent="conflict_resolver",
    severity="high",
    issue="Unresolvable conflict between agents",
    context={"conflict_id": "c123"},
    attempted_resolutions=["Analyzed positions", "Gathered evidence"]
)
```

### 2. Agent Registry (`registry.py`)

Central registry for all agents with capability tracking and load balancing.

#### Registration

```python
from packages.agents.registry import AgentRegistry, AgentCapability
from packages.agents.base import TaskType

registry = AgentRegistry()

# Register an agent
registry.register(
    agent_id="codegen_specialist",
    agent_class=CodegenAgent,
    task_types=[TaskType.CODE_GENERATION],
    description="Specialized code generation agent",
    capabilities=[
        AgentCapability.CODE_GENERATION,
        AgentCapability.REFACTORING
    ],
    max_concurrent_tasks=5,
    priority=100
)
```

#### Capability-Based Selection

```python
# Find agents by capability
agents = await registry.find_agents_by_capability(
    AgentCapability.SECURITY_AUDIT,
    only_available=True
)

# Acquire agent for task
success = await registry.acquire_agent("security_auditor", "task_123")

# Release after completion
await registry.release_agent(
    "security_auditor",
    "task_123",
    success=True,
    execution_time_ms=5000
)
```

## Coordination Agents

### 1. Swarm Coordinator (`coordination/swarm_coordinator.py`)

Manages parallel agent execution for large tasks.

#### Features

- Task decomposition into subtasks
- Intelligent agent assignment
- Progress monitoring
- Failure handling with retry
- Cost and time optimization

#### Example Usage

```python
from packages.agents.coordination import SwarmCoordinator

coordinator = SwarmCoordinator(
    registry=registry,
    max_parallel_agents=10,
    enable_cost_optimization=True
)

# Create task to be decomposed
large_task = Task(
    id="refactor_project",
    type=TaskType.REFACTORING,
    description="Refactor entire authentication module",
    input_data={
        "scope": "auth module",
        "objectives": [
            "Improve security",
            "Reduce complexity",
            "Add tests"
        ]
    }
)

# Execute with swarm
result = await coordinator.execute(large_task, context)

# Result includes:
# - All subtask results
# - Aggregated outputs
# - Cost and time metrics
# - Success/failure rates
```

#### Execution Strategies

1. **Parallel**: All independent tasks run simultaneously
2. **Sequential**: Tasks run one after another
3. **DAG**: Respects dependency graph

### 2. Conflict Resolver (`coordination/conflict_resolver.py`)

Mediates disagreements between agents.

#### Features

- Conflict detection
- Position analysis
- Evidence gathering
- Resolution proposal
- Escalation to humans

#### Example Usage

```python
from packages.agents.coordination import ConflictResolver

resolver = ConflictResolver(
    registry=registry,
    escalation_threshold=0.7,
    auto_resolve_enabled=True
)

# Conflict scenario: Reviewer blocks Codegen
conflict_task = Task(
    id="resolve_conflict_1",
    type=TaskType.REVIEW,
    description="Resolve code review conflict",
    input_data={
        "conflict": {
            "type": "code_quality",
            "severity": "high",
            "positions": [
                {
                    "agent_id": "codegen",
                    "position": "Code is acceptable",
                    "rationale": "Meets functional requirements",
                    "confidence": 0.8,
                    "evidence": [...]
                },
                {
                    "agent_id": "reviewer",
                    "position": "Code needs refactoring",
                    "rationale": "Complexity too high, violates standards",
                    "confidence": 0.9,
                    "evidence": [...]
                }
            ],
            "context": {"pr_id": "123"}
        }
    }
)

result = await resolver.execute(conflict_task, context)

# Result includes:
# - Resolution decision
# - Rationale
# - Action items
# - Whether escalated
```

### 3. Resource Optimizer (`coordination/resource_optimizer.py`)

Tracks workload and optimizes resource allocation.

#### Features

- Real-time workload tracking
- Bottleneck detection
- Load balancing
- Scaling recommendations
- Cost optimization

#### Example Usage

```python
from packages.agents.coordination import ResourceOptimizer, OptimizationGoal

optimizer = ResourceOptimizer(
    registry=registry,
    optimization_goal=OptimizationGoal.BALANCE,
    max_utilization_threshold=0.8
)

# Run periodic optimization
optimization_task = Task(
    id="optimize_resources",
    type=TaskType.PLANNING,
    description="Optimize agent resource allocation",
    input_data={}
)

result = await optimizer.execute(optimization_task, context)

# Result includes:
# - Current metrics for all agents
# - Detected bottlenecks
# - Scaling recommendations
# - Distribution optimization
# - Cost savings opportunities
```

## Specialized Agents

### 1. Tech Debt Tracker (`specialized/tech_debt_tracker.py`)

Scans codebase for technical debt and recommends refactoring.

#### Features

- Code smell detection
- Complexity analysis
- Duplication detection
- TODO/FIXME tracking
- Refactoring prioritization
- Trend analysis

#### Example Usage

```python
from packages.agents.specialized import TechDebtTracker

tracker = TechDebtTracker(
    complexity_threshold=15,
    duplication_threshold=50
)

scan_task = Task(
    id="scan_tech_debt",
    type=TaskType.REFACTORING,
    description="Scan codebase for technical debt",
    input_data={}
)

result = await tracker.execute(scan_task, context)

# Result includes:
# - All debt items (by severity/category)
# - Refactoring opportunities
# - Metrics and trends
# - Prioritized action plan
```

### 2. Migration Planner (`specialized/migration_planner.py`)

Plans large-scale code migrations.

#### Features

- Dependency analysis
- Incremental planning
- Risk assessment
- Compatibility validation
- Rollback strategies

#### Example Usage

```python
from packages.agents.specialized import MigrationPlanner

planner = MigrationPlanner(
    max_parallel_steps=3,
    require_rollback_plan=True
)

migration_task = Task(
    id="plan_react_migration",
    type=TaskType.MIGRATION,
    description="Plan migration from React 17 to React 18",
    input_data={
        "action": "plan",
        "target": {
            "from_technology": "React 17",
            "to_technology": "React 18",
            "type": "framework"
        }
    }
)

result = await planner.execute(migration_task, context)

# Result includes:
# - Complete migration plan
# - Step-by-step procedures
# - Risk assessment
# - Rollback strategy
# - Time estimates
```

### 3. Incident Responder (`specialized/incident_responder.py`)

Handles production incidents and outages.

#### Features

- Rapid incident assessment
- Incident swarm coordination
- Hotfix generation
- Post-incident analysis
- Metrics tracking (MTTR)

#### Example Usage

```python
from packages.agents.specialized import IncidentResponder

responder = IncidentResponder(
    registry=registry,
    auto_create_hotfix=True,
    auto_deploy_sev1=False  # Safety first!
)

# Assess incident
assess_task = Task(
    id="assess_incident",
    type=TaskType.INCIDENT_RESPONSE,
    description="Assess production outage",
    input_data={
        "action": "assess",
        "incident": {
            "title": "API Gateway Down",
            "description": "500 errors on all endpoints",
            "symptoms": ["High error rate", "Slow response times"],
            "affected_systems": ["api-gateway", "user-service"],
            "errors": ["ConnectionTimeout", "ServiceUnavailable"]
        }
    }
)

assessment = await responder.execute(assess_task, context)

# Create hotfix
hotfix_task = Task(
    id="create_hotfix",
    type=TaskType.INCIDENT_RESPONSE,
    description="Create hotfix patch",
    input_data={
        "action": "create_hotfix",
        "incident_id": assessment.output["incident_id"]
    }
)

hotfix = await responder.execute(hotfix_task, context)

# Conduct post-mortem
postmortem_task = Task(
    id="post_mortem",
    type=TaskType.INCIDENT_RESPONSE,
    description="Conduct post-incident analysis",
    input_data={
        "action": "post_mortem",
        "incident_id": assessment.output["incident_id"]
    }
)

analysis = await responder.execute(postmortem_task, context)
```

## Coordination Patterns

### Pattern 1: Parallel Task Execution

```python
# Large feature implementation
feature_task = Task(
    id="implement_auth",
    type=TaskType.CODE_GENERATION,
    description="Implement OAuth2 authentication",
    input_data={...}
)

# Swarm coordinator decomposes into:
# - Backend API implementation
# - Frontend integration
# - Database migrations
# - Documentation
# - Test suite
# All executed in parallel
```

### Pattern 2: Conflict Resolution Flow

```
Codegen creates PR
    ↓
Reviewer finds issues
    ↓
Conflict detected
    ↓
Conflict Resolver analyzes both positions
    ↓
├─ Auto-resolve → Apply resolution
└─ Escalate → Human decision
```

### Pattern 3: Incident Response Flow

```
Incident detected
    ↓
Incident Responder assesses severity
    ↓
├─ SEV1/SEV2: Assemble incident swarm
│   ├─ Incident Responder (coordinator)
│   ├─ Codegen (hotfix)
│   ├─ Tester (validation)
│   └─ Security Auditor (if needed)
│
└─ SEV3/SEV4: Standard process
    ↓
Hotfix created and validated
    ↓
Deploy to production
    ↓
Monitor for recurrence
    ↓
Post-mortem analysis
```

### Pattern 4: Resource Optimization Loop

```
Monitor agent metrics (continuous)
    ↓
Detect bottlenecks
    ↓
Generate recommendations
    ↓
Apply optimizations
    ↓
Measure impact
    ↓
Repeat
```

## Example Scenarios

### Scenario 1: Large Codebase Refactoring

```python
# 1. Scan for tech debt
debt_scan = await tech_debt_tracker.execute(scan_task, context)

# 2. Create refactoring opportunities
opportunities = debt_scan.output["refactoring_opportunities"]

# 3. Use swarm coordinator to parallelize
for opp in opportunities[:5]:  # Top 5
    refactor_task = Task(
        id=f"refactor_{opp['id']}",
        type=TaskType.REFACTORING,
        description=opp["description"],
        input_data={"opportunity": opp}
    )

    # Swarm handles parallel execution
    result = await swarm_coordinator.execute(refactor_task, context)
```

### Scenario 2: Framework Migration

```python
# 1. Create migration plan
plan = await migration_planner.execute(plan_task, context)

# 2. Execute migration steps with swarm
migration_execution = Task(
    id="execute_migration",
    type=TaskType.MIGRATION,
    description="Execute migration plan",
    input_data={
        "plan_id": plan.output["plan_id"],
        "steps": plan.output["steps"]
    }
)

# Swarm coordinator executes steps
result = await swarm_coordinator.execute(migration_execution, context)
```

### Scenario 3: Production Incident

```python
# 1. Detect and assess
incident = await incident_responder.execute(assess_task, context)

# 2. Assemble response team if severe
if incident.output["severity"] in ["sev1", "sev2"]:
    response = await incident_responder.execute(respond_task, context)

# 3. Create hotfix
hotfix = await incident_responder.execute(hotfix_task, context)

# 4. Validate and deploy (manual for safety)
# ...

# 5. Post-mortem
analysis = await incident_responder.execute(postmortem_task, context)
```

## Best Practices

### 1. Agent Communication

- Always use structured messages via protocol
- Include evidence for all decisions
- Document handoffs clearly
- Use appropriate priority levels

### 2. Conflict Resolution

- Let agents attempt resolution first
- Escalate when confidence is low
- Document all resolution rationale
- Learn from conflicts to prevent recurrence

### 3. Resource Management

- Monitor continuously
- React to bottlenecks proactively
- Balance cost vs. performance
- Plan for peak loads

### 4. Incident Response

- Define clear severity levels
- Maintain runbooks for common incidents
- Always have rollback procedures
- Conduct thorough post-mortems

### 5. Specialized Agents

- Run tech debt scans regularly
- Plan migrations incrementally
- Test everything before deployment
- Document decisions and trade-offs

## Metrics & Monitoring

### Key Metrics

```python
# Registry stats
stats = registry.get_registry_stats()
# - Total agents
# - Available/busy/offline
# - Task completion rates
# - Success rates

# Resource optimizer
health = optimizer.calculate_system_health()
# - Overall health score
# - Utilization levels
# - Bottlenecks
# - Recommendations

# Incident responder
metrics = responder.get_incident_metrics()
# - MTTR (Mean Time To Resolution)
# - Incidents by severity
# - Total hotfixes
# - Resolution rates

# Conflict resolver
conflict_stats = resolver.get_conflict_stats()
# - Total/active/resolved conflicts
# - Escalation rate
# - Conflicts by type
```

## Troubleshooting

### Common Issues

1. **Agents Not Available**
   - Check registry status
   - Verify heartbeats
   - Check capacity limits

2. **Conflicts Not Resolving**
   - Review evidence quality
   - Check confidence thresholds
   - Consider escalation criteria

3. **High Resource Usage**
   - Check for bottlenecks
   - Review scaling recommendations
   - Optimize task distribution

4. **Slow Incident Response**
   - Review severity classification
   - Check swarm assembly
   - Verify agent availability

## Future Enhancements

- Distributed agent registry with Redis
- Machine learning for conflict resolution
- Automated scaling actions
- Predictive resource optimization
- Automated incident remediation
- Advanced migration validation

## References

- Architecture Overview: `/docs/architecture/OVERVIEW.md`
- Layer 3 Agents: `/docs/architecture/layers/LAYER_3_AGENTS.md`
- Base Agent Framework: `base.py`
- Agent Protocol: `protocol.py`
- Agent Registry: `registry.py`
