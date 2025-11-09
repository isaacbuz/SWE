# Agent System

A comprehensive framework for AI-powered software development agents with intelligent model routing, evidence tracking, and specialized capabilities.

## Overview

The Agent System provides a robust foundation for building and orchestrating AI agents that can handle complex software development tasks. It includes:

- **Base Agent Framework**: Abstract base class with MoE Router integration
- **Agent Registry**: Centralized agent management and orchestration
- **Executive Agents**: Strategic planning and architecture
- **Development Agents**: Code implementation and quality
- **Evidence Tracking**: All decisions backed by traceable evidence
- **Multi-Model Support**: Anthropic Claude and OpenAI integration

## Architecture

```
packages/agents/
├── base.py                          # Base agent framework
├── registry.py                      # Agent registry and orchestration
├── executive/                       # Strategic agents
│   ├── chief_architect.py          # Architecture design
│   ├── planner.py                  # Project planning
│   └── technical_director.py       # Technical leadership
├── development/                     # Implementation agents
│   ├── codegen.py                  # Code generation
│   ├── refactor.py                 # Code refactoring
│   └── migration_specialist.py     # Complex migrations
└── prompts/                         # Agent prompts and documentation
    ├── architect_prompt.md
    ├── planner_prompt.md
    └── codegen_prompt.md
```

## Agent Capabilities

### Executive Agents

#### 1. Chief Architect

**Purpose**: Translate requirements into concrete, evolvable architectures

**Capabilities**:

- Architecture design and decision making
- ADR (Architecture Decision Record) generation
- Mermaid diagram creation (C4, sequence, ER, deployment)
- API boundary definition
- Technology stack recommendations
- Non-functional requirements specification

**Outputs**:

- Architecture documents
- ADRs with context, decisions, consequences, alternatives
- Mermaid diagrams
- API contracts (JSON/YAML)
- Migration and rollback strategies

**Example Usage**:

```python
from agents import ChiefArchitectAgent, Task, Context, TaskType

# Initialize agent
architect = ChiefArchitectAgent(
    agent_id="chief_architect",
    moe_router=moe_router,
    anthropic_client=anthropic_client
)

# Create task
task = Task(
    id="arch-001",
    type=TaskType.PLANNING,
    description="Design authentication system architecture",
    input_data={
        "requirements": "Build secure user authentication with OAuth",
        "project_type": "web_application",
        "constraints": {
            "must_support_oauth": True,
            "max_latency_ms": 500
        }
    }
)

# Execute
context = Context(project_path="/path/to/project")
result = await architect.execute_with_tracking(task, context)

# Access outputs
print(result.output["architecture_document"])
for artifact in result.artifacts:
    print(f"Created: {artifact}")
```

#### 2. Planner

**Purpose**: Break architecture into actionable epics and stories

**Capabilities**:

- Epic creation with business value
- Story breakdown with acceptance criteria
- Effort estimation
- Dependency identification
- GitHub issue generation
- Milestone planning

**Outputs**:

- Epics with business value
- User stories with acceptance criteria
- Project backlog (JSON)
- Milestone timeline
- Dependency graph

**Example Usage**:

```python
from agents import PlannerAgent

planner = PlannerAgent(
    agent_id="planner",
    moe_router=moe_router
)

task = Task(
    id="plan-001",
    type=TaskType.PLANNING,
    description="Create implementation plan for auth system",
    input_data={
        "architecture_document": arch_result.output["architecture_document"],
        "adrs": ["ADR-0001: OAuth Integration", "ADR-0002: Session Management"],
        "requirements": original_requirements,
        "timeline": "4 weeks"
    }
)

result = await planner.execute_with_tracking(task, context)

# Access plan
epics = result.output["epics"]
stories = result.output["stories"]
print(f"Created {len(epics)} epics and {len(stories)} stories")
```

#### 3. Technical Director

**Purpose**: Technical leadership and governance

**Capabilities**:

- Decision review and approval
- Conflict resolution
- Technical standards setting
- Quality assurance oversight
- Risk management

**Outputs**:

- Decision reviews (approve/reject/revise)
- Technical standards
- Review reports
- Modification recommendations

### Development Agents

#### 4. Code Generator

**Purpose**: Implement user stories with high-quality code

**Capabilities**:

- Test-driven development (TDD)
- SOLID principles adherence
- Security best practices
- Multi-file code generation
- Documentation updates

**Outputs**:

- Implementation code
- Test files (unit, integration)
- Documentation updates
- Implementation summary

**Example Usage**:

```python
from agents import CodegenAgent

codegen = CodegenAgent(
    agent_id="codegen",
    moe_router=moe_router,
    anthropic_client=anthropic_client
)

task = Task(
    id="impl-001",
    type=TaskType.CODE_GENERATION,
    description="Implement user registration story",
    input_data={
        "story": {
            "id": "AUTH-101",
            "title": "User Registration with Email Verification",
            "description": "Implement user registration endpoint",
            "acceptance_criteria": [
                "User can register with email and password",
                "Verification email is sent",
                "Account activated on verification",
                "Passwords are securely hashed"
            ]
        },
        "architecture_refs": ["ADR-0003: Password Hashing"],
        "existing_code": {
            "models/user.py": existing_user_model_code
        }
    }
)

result = await codegen.execute_with_tracking(task, context)

# Files created
print(f"Files created: {result.output['files_created']}")
print(f"Tests created: {result.output['tests_created']}")
```

#### 5. Refactor Agent

**Purpose**: Improve code quality through systematic refactoring

**Capabilities**:

- Code smell detection
- Refactoring plan generation
- Safe, incremental refactoring
- Test coverage maintenance
- Quality metrics tracking

**Outputs**:

- Code smell reports
- Refactoring plans with risk assessment
- Refactored code
- Updated tests
- Refactoring report

**Example Usage**:

```python
from agents import RefactorAgent

refactor = RefactorAgent(
    agent_id="refactor",
    moe_router=moe_router
)

task = Task(
    id="refactor-001",
    type=TaskType.REFACTORING,
    description="Refactor authentication module",
    input_data={
        "target_files": ["auth/handlers.py", "auth/validators.py"],
        "refactoring_type": "extract_method",
        "existing_code": {
            "auth/handlers.py": current_code
        },
        "test_coverage": {"auth/handlers.py": 0.75}
    }
)

result = await refactor.execute_with_tracking(task, context)

# Refactoring results
print(f"Code smells found: {len(result.output['code_smells'])}")
print(f"Refactorings applied: {result.output['refactorings_applied']}")
```

#### 6. Migration Specialist

**Purpose**: Handle complex migrations safely

**Capabilities**:

- Migration scope analysis
- Incremental migration planning
- Schema, data, and code migrations
- Validation at each step
- Rollback procedures

**Outputs**:

- Migration scope analysis
- Step-by-step migration plan
- Migration scripts (schema, data, code)
- Validation tests
- Comprehensive migration guide

**Example Usage**:

```python
from agents import MigrationSpecialistAgent

migration = MigrationSpecialistAgent(
    agent_id="migration",
    moe_router=moe_router
)

task = Task(
    id="migrate-001",
    type=TaskType.CODE_GENERATION,
    description="Migrate from SQLite to PostgreSQL",
    input_data={
        "migration_type": "database_migration",
        "from_version": "SQLite 3.x",
        "to_version": "PostgreSQL 14",
        "requirements": "Zero-downtime migration with data validation",
        "constraints": {
            "max_downtime_minutes": 5,
            "data_size_gb": 100
        }
    }
)

result = await migration.execute_with_tracking(task, context)

# Migration plan
print(f"Complexity: {result.metadata['complexity']}")
print(f"Steps: {result.metadata['steps_count']}")
```

## Agent Registry

The Agent Registry manages agent lifecycle and orchestration:

```python
from agents import AgentRegistry, TaskType, AgentCapability

# Initialize registry
registry = AgentRegistry(
    moe_router=moe_router,
    anthropic_client=anthropic_client,
    openai_client=openai_client
)

# Register agents
registry.register(
    agent_id="chief_architect",
    agent_class=ChiefArchitectAgent,
    task_types=[TaskType.PLANNING],
    description="Architecture design and decision making",
    priority=90,
    capabilities=[AgentCapability.ARCHITECTURE, AgentCapability.PLANNING]
)

registry.register(
    agent_id="codegen",
    agent_class=CodegenAgent,
    task_types=[TaskType.CODE_GENERATION],
    description="Code implementation specialist",
    priority=80,
    capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.TESTING]
)

# Execute task (automatic routing)
task = Task(
    id="task-001",
    type=TaskType.CODE_GENERATION,
    description="Implement feature"
)

result = await registry.execute_task(task, context)

# Execute workflow
tasks = [task1, task2, task3]
results = await registry.execute_workflow(tasks, context, parallel=False)

# Get statistics
stats = registry.get_registry_stats()
print(f"Active agents: {stats['active_instances']}")
print(f"Task coverage: {stats['task_type_coverage']}")
```

## Evidence Tracking

All agent decisions include evidence IDs and traceable rationale:

```python
# Agent creates evidence
evidence = agent.create_evidence(
    source="architecture_analysis",
    description="Selected PostgreSQL based on ACID requirements",
    weight=0.95
)

# Evidence included in result
result = await agent.execute(task, context)
for evidence in result.evidence:
    print(f"{evidence.source}: {evidence.description} (weight: {evidence.weight})")
```

## MoE Router Integration

Agents use the MoE Router for intelligent model selection:

```python
# Router automatically selects best model
response = await agent.invoke_model(
    prompt="Design authentication system",
    task=task,
    context=context,
    requires_tools=True,
    max_tokens=4096
)

# Routing decision included
print(f"Model used: {response['model_used']}")
print(f"Confidence: {response['routing_decision'].confidence}")
print(f"Cost: ${response['cost']:.6f}")
```

## Workflow Examples

### Full Development Workflow

```python
import asyncio
from agents import (
    AgentRegistry,
    ChiefArchitectAgent,
    PlannerAgent,
    CodegenAgent,
    Task,
    Context,
    TaskType,
    Priority
)

async def full_workflow_example():
    # Setup
    registry = AgentRegistry(moe_router=moe_router)
    context = Context(project_path="/path/to/project")

    # 1. Architecture
    arch_task = Task(
        id="arch-001",
        type=TaskType.PLANNING,
        description="Design e-commerce platform architecture",
        priority=Priority.CRITICAL,
        input_data={
            "requirements": "Build scalable e-commerce platform...",
            "project_type": "web_application"
        }
    )

    arch_result = await registry.execute_task(arch_task, context)

    # 2. Planning
    plan_task = Task(
        id="plan-001",
        type=TaskType.PLANNING,
        description="Create implementation plan",
        input_data={
            "architecture_document": arch_result.output["architecture_document"],
            "adrs": arch_result.artifacts
        },
        dependencies=["arch-001"]
    )

    plan_result = await registry.execute_task(plan_task, context)

    # 3. Implementation (parallel)
    stories = plan_result.output["stories"][:5]  # First 5 stories
    impl_tasks = []

    for story in stories:
        task = Task(
            id=f"impl-{story['id']}",
            type=TaskType.CODE_GENERATION,
            description=f"Implement {story['title']}",
            input_data={"story": story},
            dependencies=["plan-001"]
        )
        impl_tasks.append(task)

    # Execute implementations in parallel
    impl_results = await registry.execute_workflow(
        impl_tasks,
        context,
        parallel=True
    )

    print(f"Architecture: {len(arch_result.artifacts)} artifacts")
    print(f"Planning: {len(plan_result.output['stories'])} stories")
    print(f"Implementation: {len(impl_results)} stories completed")

# Run workflow
asyncio.run(full_workflow_example())
```

### Migration Workflow

```python
async def migration_workflow():
    registry = AgentRegistry(moe_router=moe_router)
    context = Context(project_path="/path/to/project")

    # 1. Analyze migration
    analysis_task = Task(
        id="migrate-001",
        type=TaskType.CODE_GENERATION,
        description="Plan MongoDB to PostgreSQL migration",
        input_data={
            "migration_type": "database_migration",
            "from_version": "MongoDB 4.x",
            "to_version": "PostgreSQL 14"
        }
    )

    result = await registry.execute_task(analysis_task, context)

    # Review migration guide
    guide_path = [a for a in result.artifacts if "migration-guide" in a][0]
    print(f"Migration guide: {guide_path}")
    print(f"Steps: {result.metadata['steps_count']}")
    print(f"Scripts: {result.metadata['scripts_count']}")

asyncio.run(migration_workflow())
```

## Configuration

### Agent Initialization Options

```python
agent = CodegenAgent(
    agent_id="codegen",
    moe_router=moe_router,              # MoE Router for model selection
    anthropic_client=anthropic_client,  # Anthropic API client
    openai_client=openai_client,        # OpenAI API client
    quality_requirement=0.85,           # Minimum quality score
    cost_budget=0.10,                   # Max cost per execution
    tools=[custom_tool]                 # Additional tools
)
```

### Custom Tools

```python
from agents import Tool

custom_tool = Tool(
    name="analyze_dependencies",
    description="Analyze project dependencies",
    input_schema={
        "type": "object",
        "properties": {
            "package_file": {"type": "string"}
        },
        "required": ["package_file"]
    },
    handler=analyze_dependencies_handler
)
```

## Performance Tracking

Agents track execution metrics:

```python
# Get agent statistics
stats = agent.get_stats()

print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Avg execution time: {stats['avg_execution_time_ms']}ms")
print(f"Total cost: ${stats['total_cost']:.4f}")
```

## Best Practices

### 1. Task Design

- Make tasks focused and specific
- Include all necessary context in input_data
- Define clear success criteria
- Use appropriate task types

### 2. Evidence Tracking

- Review evidence for all decisions
- Use evidence weights to indicate importance
- Trace decisions back to requirements

### 3. Error Handling

- Check result.success before using outputs
- Review result.error for failure details
- Implement retry logic for transient failures

### 4. Cost Management

- Set appropriate cost budgets
- Monitor total costs across workflows
- Use quality_requirement to balance cost/quality

### 5. Workflow Orchestration

- Define dependencies clearly
- Use parallel execution where appropriate
- Monitor workflow progress

## Integration with Other Systems

### GitHub Integration

```python
# Use Planner output to create GitHub issues
plan_result = await planner.execute_with_tracking(task, context)

for story in plan_result.output["stories"]:
    # Create GitHub issue via API
    create_github_issue(
        title=story["title"],
        body=story["description"],
        labels=story["labels"],
        milestone=story.get("milestone")
    )
```

### CI/CD Integration

```python
# Use Codegen output in CI pipeline
impl_result = await codegen.execute_with_tracking(task, context)

# Run tests on generated code
test_files = impl_result.output["tests_created"]
run_tests(test_files)

# If tests pass, commit changes
if tests_passed:
    commit_files(impl_result.artifacts)
```

## Testing

```python
import pytest
from agents import CodegenAgent, Task, Context, TaskType

@pytest.mark.asyncio
async def test_codegen_agent():
    agent = CodegenAgent(agent_id="test_codegen")

    task = Task(
        id="test-001",
        type=TaskType.CODE_GENERATION,
        description="Test implementation",
        input_data={
            "story": {
                "title": "Test Story",
                "acceptance_criteria": ["Criterion 1"]
            }
        }
    )

    context = Context(project_path="/tmp/test")
    result = await agent.execute_with_tracking(task, context)

    assert result.success
    assert len(result.artifacts) > 0
```

## Troubleshooting

### Common Issues

**Issue**: Agent not producing expected outputs

- Check input_data has all required fields
- Review agent's system prompt requirements
- Verify quality_requirement isn't too high

**Issue**: High costs

- Reduce max_tokens
- Increase quality_requirement to use cheaper models
- Set cost_budget limits

**Issue**: Slow execution

- Use parallel execution for independent tasks
- Check network latency to API providers
- Review model selection (faster models available?)

## Contributing

See main project CONTRIBUTING.md for guidelines.

## License

See main project LICENSE file.

## Support

- Documentation: `/packages/agents/prompts/`
- Issues: GitHub Issues
- Discussions: GitHub Discussions
