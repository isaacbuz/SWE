# Skills Execution Engine

Production-ready execution engine for Claude Skills with validation, caching, and MoE router integration.

## Overview

The Skills Execution Engine provides a complete runtime for executing Skills (reusable AI prompts with structured inputs/outputs). It handles:

- **Input Validation**: Validates inputs against JSON Schema
- **Prompt Rendering**: Renders Jinja2 templates with user inputs
- **Model Selection**: Uses MoE Router for intelligent model selection
- **Output Validation**: Parses and validates outputs against JSON Schema
- **Validation Rules**: Executes custom validation rules
- **Caching**: Caches results in Redis for performance
- **Performance Tracking**: Tracks latency, tokens, and cost

## Quick Start

```python
from packages.skills_engine import SkillExecutionEngine, Skill, ExecutionContext
from packages.moe_router import MoERouter
from packages.db.redis import RedisClient

# Initialize components
moe_router = MoERouter()
redis_client = RedisClient()
engine = SkillExecutionEngine(moe_router, redis_client)

# Define a skill
skill = Skill(
    id="test-skill-1",
    name="Test Skill",
    slug="test-skill",
    version="1.0.0",
    description="A test skill",
    prompt_template="Generate a greeting for {{name}}",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "greeting": {"type": "string"}
        }
    },
    category="CODE_GENERATION"
)

# Execute skill
result = await engine.execute_skill(
    skill=skill,
    inputs={"name": "Alice"},
    context=ExecutionContext(user_id="user-123")
)

print(f"Status: {result.status}")
print(f"Outputs: {result.outputs}")
print(f"Cost: ${result.cost_usd}")
```

## Architecture

```
┌─────────────────────────────────────┐
│   SkillExecutionEngine              │
├─────────────────────────────────────┤
│ 1. Validate Inputs (JSON Schema)   │
│ 2. Check Cache (Redis)              │
│ 3. Render Prompt (Jinja2)           │
│ 4. Select Model (MoE Router)        │
│ 5. Invoke Model (AI Provider)       │
│ 6. Validate Outputs (JSON Schema)  │
│ 7. Run Validation Rules            │
│ 8. Cache Result (Redis)             │
└─────────────────────────────────────┘
```

## Components

### SkillExecutionEngine

Main execution engine that orchestrates the entire skill execution flow.

### InputValidator

Validates inputs against JSON Schema before execution.

### OutputValidator

Parses and validates model outputs. Supports:
- JSON parsing
- YAML parsing
- Markdown code block extraction
- Free-form text wrapping

### ValidationRuleExecutor

Executes custom validation rules:
- `required_fields`: Check required fields exist
- `type_check`: Validate field types
- `range_check`: Validate numeric ranges
- `regex`: Validate string patterns
- `custom`: Custom validation logic

### SkillCache

Manages caching of execution results:
- Automatic cache key generation
- TTL-based expiration
- Cache invalidation by skill ID

## Error Handling

The engine raises specific exceptions:

- `SkillInputValidationError`: Input validation failed
- `SkillOutputValidationError`: Output validation failed
- `SkillExecutionError`: General execution error

All errors are captured in the `SkillResult` with appropriate status codes.

## Performance

- **Caching**: Results cached for 1 hour by default (configurable)
- **Latency Tracking**: Automatic latency measurement
- **Cost Tracking**: Tracks token usage and cost per execution
- **Cache Hits**: Significantly faster execution for repeated inputs

## Testing

```bash
# Run tests
pytest packages/skills_engine/tests/

# With coverage
pytest packages/skills_engine/tests/ --cov=packages.skills_engine --cov-report=html
```

## Integration

The Skills Engine integrates with:

- **MoE Router**: For intelligent model selection
- **AI Providers**: Anthropic, OpenAI, Google, IBM, Local
- **Redis**: For caching and performance tracking
- **Database**: For execution logging (via external services)

## See Also

- [Claude Skills Architecture](../docs/architecture/CLAUDE_SKILLS.md)
- [MoE Router](../moe_router/README.md)
- [AI Providers](../integrations/ai_providers/README.md)
