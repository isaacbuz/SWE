# MoE Router - Mixture-of-Experts Model Router

Intelligent model selection system for AI agents that optimizes for cost, quality, latency, and task-specific performance.

## Features

- **Multi-Factor Routing**: Considers cost, quality, latency, capabilities, and historical performance
- **Performance Tracking**: Redis-backed tracking of success rates and quality metrics per model+task
- **Learning Loop**: Continuous improvement based on PR outcomes and user feedback
- **Hybrid Execution**: Parallel model execution for critical tasks with consensus mechanisms
- **Circuit Breaker**: Automatic failover when providers experience failures
- **A/B Testing**: Built-in framework for comparing model performance
- **Cost Prediction**: Accurate cost estimation and budget validation
- **Evidence-Based**: All routing decisions include evidence and rationale

## Architecture

```
MoE Router
├── Router Core
│   ├── Model Selection Algorithm
│   ├── Circuit Breaker
│   └── Fallback Logic
├── Strategies
│   ├── Cost Predictor
│   ├── Performance Tracker
│   ├── Hybrid Router
│   └── Learning Loop
└── Model Registry
    └── models.yaml (18 models across 5 providers)
```

## Quick Start

### Basic Usage

```python
from moe_router import MoERouter, RoutingRequest, TaskType

# Initialize router
router = MoERouter(
    redis_url="redis://localhost:6379",
    enable_learning=True
)

# Create routing request
request = RoutingRequest(
    task_type=TaskType.CODE_GENERATION,
    task_description="Implement a REST API endpoint for user authentication",
    cost_budget=0.01,  # $0.01 max
    quality_requirement=0.8,
    requires_tools=True
)

# Get model selection
decision = router.select_model(request)

print(f"Selected: {decision.selected_model}")
print(f"Rationale: {decision.rationale}")
print(f"Estimated Cost: ${decision.estimated_cost:.6f}")
print(f"Confidence: {decision.confidence:.2f}")
print(f"Fallbacks: {decision.fallback_models}")
```

### Parallel Execution

```python
# Request parallel execution for critical task
request = RoutingRequest(
    task_type=TaskType.SECURITY_AUDIT,
    task_description="Audit authentication system for vulnerabilities",
    quality_requirement=0.95,
    enable_parallel=True
)

decision = router.select_model(request)

# Decision includes multiple models
print(f"Parallel Models: {decision.parallel_models}")
print(f"Judge Model: {decision.metadata['judge_model']}")
```

### Recording Feedback

```python
from moe_router import FeedbackData

# After task completion, record feedback
feedback = FeedbackData(
    request_id="req_123",
    model_id="claude-sonnet-4",
    task_type=TaskType.CODE_GENERATION,
    outcome="success",
    quality_score=0.92,
    actual_cost=0.00234,
    actual_latency_ms=1200,
    pr_merged=True,
    user_rating=5
)

router.learning_loop.collect_feedback(feedback)
```

## Routing Algorithm

### Selection Process

The router uses a multi-stage selection algorithm:

1. **Filter Stage**
   - Remove disabled models
   - Check circuit breaker status
   - Verify capability requirements (tools, vision, JSON mode, streaming)
   - Validate context window size
   - Check quality threshold
   - Validate latency requirements

2. **Scoring Stage** (0-100 points)
   - Quality Score (0-50 points): Base model quality rating
   - Cost Efficiency (0-20 points): Cost per token normalized
   - Performance History (0-15 points): Success rate from performance tracker
   - Learning Weight (0-10 points): Learned preference from feedback loop
   - Task Preference (0-5 points): Bonus for preferred models per task
   - Vendor Diversity (0-3 points): Bonus for different provider
   - Vendor Preference (0-2 points): User-specified provider preference

3. **Selection Stage**
   - Sort models by score descending
   - Select top model
   - Identify fallback models (top 3 alternatives)

4. **Validation Stage**
   - Verify budget constraints
   - Calculate cost prediction
   - Build evidence trail
   - Generate human-readable rationale

### Parallel Execution Decision

Parallel execution is triggered when:
- Explicitly requested (`enable_parallel=True`)
- Task type is critical (security_audit, code_review, planning, reasoning)
- High quality requirement (≥0.9) with sufficient budget (≥$0.05)
- Metadata flag `critical=true`

When parallel execution is used:
1. Select 3 diverse models (preferring different providers)
2. Select judge model (high-quality model not in parallel set)
3. Execute all models in parallel
4. Apply consensus strategy (judge, voting, quality-weighted, or first-success)

## Model Registry

The router includes 18 pre-configured models:

### Anthropic
- **claude-opus-4**: Highest quality (0.98), premium cost
- **claude-sonnet-4**: Balanced quality (0.95), good value
- **claude-haiku-4**: Fast & cheap (0.80), 300ms P50 latency

### OpenAI
- **gpt-5**: Premium quality (0.94), good reasoning
- **gpt-4o**: Fast multimodal (0.92), 600ms latency
- **gpt-4o-mini**: Budget option (0.82), very fast
- **o1**: Best reasoning (0.97), slow (15s P50)
- **o1-mini**: Good reasoning (0.90), faster (8s P50)

### Google
- **gemini-2.0-flash-thinking**: FREE, 1M context, experimental
- **gemini-pro-1.5**: 2M context window, good quality (0.89)
- **gemini-flash-1.5**: 1M context, fast & cheap

### Mistral
- **mistral-large-2**: European option, good quality (0.87)
- **mistral-small-2**: Budget European option

### Cohere
- **command-r-plus**: RAG-optimized, good quality (0.86)
- **command-r**: Budget RAG option

## Task Preferences

The router includes optimized model preferences for each task type:

### Code Generation
- Preferred: claude-sonnet-4, gpt-4o, gemini-pro-1.5
- Budget: claude-haiku-4, gpt-4o-mini, mistral-small-2

### Reasoning
- Preferred: claude-opus-4, o1, claude-sonnet-4
- Budget: o1-mini, claude-sonnet-4, mistral-large-2

### Security Audit
- Preferred: claude-opus-4, o1, claude-sonnet-4
- Budget: claude-sonnet-4, gpt-5

### Long Context
- Preferred: gemini-pro-1.5, claude-sonnet-4, gemini-2.0-flash-thinking
- Budget: gemini-flash-1.5, claude-haiku-4

## Performance Tracking

The router tracks performance metrics for each model+task combination:

```python
# Get performance metrics
metrics = router.performance_tracker.get_metrics(
    model_id="claude-sonnet-4",
    task_type=TaskType.CODE_GENERATION
)

print(f"Success Rate: {metrics.success_rate:.2%}")
print(f"Avg Latency: {metrics.avg_latency_ms}ms")
print(f"Avg Cost: ${metrics.avg_cost:.6f}")
print(f"Total Requests: {metrics.total_requests}")

# Get recommendation weight
weight = router.performance_tracker.get_recommendation_weight(
    model_id="claude-sonnet-4",
    task_type=TaskType.CODE_GENERATION
)
print(f"Recommendation Weight: {weight:.2f}")  # 0-1 scale
```

### Confidence Calculation

Confidence scores combine sample size and recency:
- Sample confidence: min(1.0, total_requests / 100)
- Recency decay: 0.5^(age_hours / 168)  # Half-life of 1 week
- Final confidence: sample_confidence × recency_decay

## Learning Loop

The learning loop continuously improves routing decisions:

### Feedback Collection

```python
# Record feedback with PR outcome
feedback = FeedbackData(
    request_id="req_456",
    model_id="gpt-4o",
    task_type=TaskType.CODE_REVIEW,
    outcome="success",
    quality_score=0.88,
    pr_merged=True,
    pr_reverted=False,
    user_rating=4
)

router.learning_loop.collect_feedback(feedback)
```

### Feedback Scoring

Feedback is scored based on:
- Outcome: success=1.0, partial=0.5, failure=0.0
- Quality score: 0-1 (averaged with outcome)
- PR merged: +0.2 bonus
- PR reverted: -0.5 penalty
- User rating: 1-5 normalized to 0-1

Model weights are updated using exponential moving average (α=0.1).

### A/B Testing

```python
# Start A/B test
test_id = router.learning_loop.start_ab_test(
    model_a="claude-sonnet-4",
    model_b="gpt-4o",
    task_type=TaskType.CODE_GENERATION,
    traffic_split=0.5,
    min_samples=30,
    duration_days=7
)

# ... let test run ...

# Analyze results
results = router.learning_loop.analyze_ab_test(test_id)
print(f"Winner: {results['winner']}")
print(f"Confidence: {results['confidence']:.1%}")
print(f"Recommendation: {results['recommendation']}")
```

## Circuit Breaker

The circuit breaker protects against cascading failures:

### States
- **Closed**: Normal operation
- **Open**: Provider blocked after 5 consecutive failures
- **Half-Open**: Testing if provider has recovered

### Configuration
- Failure Threshold: 5 consecutive failures
- Retry Timeout: 60 seconds
- Automatic state transitions

```python
# Check circuit breaker status
status = router.get_circuit_breaker_status()
print(status)

# Manually reset if needed
router.reset_circuit_breaker("anthropic")
```

## Cost Prediction

Accurate cost estimation before execution:

```python
from moe_router import CostPredictor

predictor = CostPredictor()

# Estimate tokens from description
input_tokens, output_tokens = predictor.estimate_tokens_from_description(
    description="Implement user authentication with JWT",
    task_type=TaskType.CODE_GENERATION
)

# Predict cost for specific model
model = router._get_model_by_id("claude-sonnet-4")
prediction = predictor.predict_cost(model, request)

print(f"Estimated Input: {prediction.estimated_input_tokens} tokens")
print(f"Estimated Output: {prediction.estimated_output_tokens} tokens")
print(f"Cost Range: ${prediction.min_cost:.6f} - ${prediction.max_cost:.6f}")
print(f"Expected Cost: ${prediction.expected_cost:.6f}")
print(f"Within Budget: {prediction.within_budget}")
```

## Example Selection Flows

### Example 1: Budget-Constrained Code Generation

```python
request = RoutingRequest(
    task_type=TaskType.CODE_GENERATION,
    task_description="Add logging to existing API endpoint",
    cost_budget=0.001,  # Very tight budget
    quality_requirement=0.7
)

decision = router.select_model(request)
# Result: claude-haiku-4 or gemini-flash-1.5
# Rationale: "Selected claude-haiku-4 for code_generation based on:
#   quality score 0.80, estimated cost $0.000425, preferred for code_generation.
#   Overall score: 67.3/100."
```

### Example 2: High-Quality Reasoning Task

```python
request = RoutingRequest(
    task_type=TaskType.REASONING,
    task_description="Design a distributed system architecture for high availability",
    quality_requirement=0.95,
    cost_budget=0.10
)

decision = router.select_model(request)
# Result: claude-opus-4 or o1
# Rationale: "Selected claude-opus-4 for reasoning based on:
#   quality score 0.98, estimated cost $0.045, preferred for reasoning,
#   strong historical performance (weight: 0.85). Overall score: 88.2/100."
```

### Example 3: Critical Security Audit (Parallel)

```python
request = RoutingRequest(
    task_type=TaskType.SECURITY_AUDIT,
    task_description="Comprehensive security audit of payment processing system",
    quality_requirement=0.95,
    enable_parallel=True
)

decision = router.select_model(request)
# Result: Parallel execution with claude-opus-4, o1, claude-sonnet-4
# Judge: gpt-5
# Rationale: "Parallel execution with 3 models (claude-opus-4, o1, claude-sonnet-4)
#   to maximize quality (expected: 0.98) at estimated cost $0.125.
#   Judge model gpt-5 will select best output."
```

### Example 4: Long Context Analysis

```python
request = RoutingRequest(
    task_type=TaskType.LONG_CONTEXT,
    task_description="Analyze 50k lines of code for technical debt",
    context_size=150000,  # 150k tokens
    quality_requirement=0.85
)

decision = router.select_model(request)
# Result: gemini-pro-1.5 (2M context window)
# Rationale: "Selected gemini-pro-1.5 for long_context based on:
#   quality score 0.89, estimated cost $0.052, supports 2M context window,
#   preferred for long_context. Overall score: 76.8/100."
```

### Example 5: Fast Multimodal Task

```python
request = RoutingRequest(
    task_type=TaskType.MULTIMODAL,
    task_description="Analyze UI screenshot and generate accessibility report",
    requires_vision=True,
    latency_requirement_ms=2000,
    quality_requirement=0.85
)

decision = router.select_model(request)
# Result: gpt-4o or claude-haiku-4
# Rationale: "Selected gpt-4o for multimodal based on:
#   quality score 0.92, estimated cost $0.0034, supports vision,
#   low latency (P95: 1500ms). Overall score: 79.4/100."
```

## Analytics

### Routing Statistics

```python
stats = router.get_routing_stats()
print(stats)
# {
#   "total_requests": 156,
#   "unique_models_used": 8,
#   "model_distribution": {
#     "claude-sonnet-4": 45,
#     "gpt-4o": 38,
#     "claude-haiku-4": 27,
#     ...
#   },
#   "strategy_distribution": {
#     "standard": 142,
#     "parallel": 14
#   },
#   "total_estimated_cost": 2.456,
#   "avg_estimated_cost": 0.015744,
#   "avg_confidence": 0.847
# }
```

### Performance Report

```python
report = router.learning_loop.get_model_performance_report(
    model_id="claude-sonnet-4",
    task_type=TaskType.CODE_GENERATION
)
print(report)
# {
#   "model_id": "claude-sonnet-4",
#   "task_type": "code_generation",
#   "total_requests": 45,
#   "success_rate": 0.9333,
#   "pr_merge_rate": 0.8667,
#   "pr_revert_rate": 0.0222,
#   "avg_cost": 0.00456,
#   "avg_latency_ms": 1245.3,
#   "avg_quality": 0.89,
#   "avg_rating": 4.2,
#   "learned_weight": 0.78
# }
```

## Dependencies

```
pydantic>=2.0.0
pyyaml>=6.0
numpy>=1.24.0
redis>=4.5.0  # Optional, for performance tracking
```

## Configuration

### Environment Variables

```bash
# Redis connection (optional)
REDIS_URL=redis://localhost:6379

# Router settings
MOE_ENABLE_LEARNING=true
MOE_ENABLE_CIRCUIT_BREAKER=true
MOE_CONFIG_PATH=/path/to/models.yaml
```

### Custom Model Registry

```yaml
# custom_models.yaml
models:
  - id: custom-model-1
    provider: custom
    capabilities:
      - code
      - reasoning
    cost_per_1k_input: 0.001
    cost_per_1k_output: 0.003
    context_window: 100000
    quality_score: 0.85
    enabled: true
```

```python
router = MoERouter(config_path="custom_models.yaml")
```

## Best Practices

1. **Always Provide Context Size**: Helps router filter models with insufficient context windows
2. **Set Realistic Budgets**: Too tight budgets may exclude optimal models
3. **Record Feedback**: Essential for learning loop to improve over time
4. **Use Parallel for Critical Tasks**: Security audits, production code reviews
5. **Monitor Circuit Breakers**: Alert on open circuits for provider issues
6. **Run A/B Tests**: Validate assumptions about model performance
7. **Review Evidence**: Understand why specific models were selected

## License

MIT License

## Contributing

See CONTRIBUTING.md for development setup and guidelines.
