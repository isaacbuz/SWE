# MoE Router - Routing Algorithm & Selection Flows

## Algorithm Overview

The MoE Router implements a sophisticated multi-stage selection algorithm that balances cost, quality, performance, and task-specific requirements to select the optimal AI model for each request.

## Routing Algorithm

### Stage 1: Filtering

The first stage filters the model registry to find capable models:

```
INPUT: All registered models (18 total)
       Routing request with requirements

FILTERS:
1. enabled = true
2. circuit_breaker[provider] != "open"
3. quality_score >= quality_requirement
4. context_window >= context_size (if specified)
5. capability requirements:
   - requires_vision → "vision" in capabilities
   - requires_tools → "function_calling" in capabilities
   - requires_json_mode → "json_mode" in capabilities
   - requires_streaming → supports_streaming = true
6. latency_p95_ms <= latency_requirement_ms (if specified)
7. estimated_cost <= cost_budget (if specified)

OUTPUT: List of capable models
```

**Example:**
```
Request: Code generation, quality >= 0.8, budget <= $0.005
18 models → Filter by enabled (18)
         → Filter by quality (12 remain)
         → Filter by budget (8 remain)
Result: 8 capable models
```

### Stage 2: Scoring

Each capable model receives a composite score (0-100 points):

```
SCORE COMPONENTS:

1. Quality Score (0-50 points)
   score += model.quality_score × 50

   Example: claude-opus-4 (0.98) = 49.0 points
            claude-haiku-4 (0.80) = 40.0 points

2. Cost Efficiency (0-20 points)
   cost_efficiency = 1.0 / (1.0 + estimated_cost × 100)
   score += cost_efficiency × 20

   Example: $0.001 cost → 0.909 efficiency → 18.2 points
            $0.010 cost → 0.500 efficiency → 10.0 points

3. Performance History (0-15 points)
   recommendation_weight = success_rate × sample_confidence × recency_decay
   score += recommendation_weight × 15

   Example: 95% success, 100 samples, 1 day old → 0.95 weight → 14.3 points
            70% success, 10 samples, 7 days old → 0.35 weight → 5.3 points

4. Learning Weight (0-10 points)
   learned_weight = EMA of feedback scores
   score += learned_weight × 10

   Example: Consistently good PR outcomes → 0.85 weight → 8.5 points
            Mixed results → 0.50 weight → 5.0 points

5. Task Preference Bonus (0-5 points)
   if model.id in task_preferences[task_type].preferred:
       score += 5

   Example: claude-sonnet-4 is preferred for code_generation → +5 points

6. Vendor Diversity Bonus (0-3 points)
   if vendor_diversity and provider not in last_5_providers:
       score += 3

   Example: Last 5 requests used Anthropic, now selecting OpenAI → +3 points

7. Vendor Preference Bonus (0-2 points)
   if model.provider == vendor_preference:
       score += 2

   Example: User prefers Anthropic, model is Claude → +2 points

TOTAL SCORE: Sum of all components (0-100)
```

**Example Scoring:**

```
Model: claude-sonnet-4
Task: CODE_GENERATION
Budget: $0.01

Quality:       0.95 × 50    = 47.5 points
Cost Eff:      0.85 × 20    = 17.0 points
Performance:   0.88 × 15    = 13.2 points
Learning:      0.75 × 10    =  7.5 points
Preferred:     +5           =  5.0 points
TOTAL:                      = 90.2 points

Model: gpt-4o-mini
Task: CODE_GENERATION
Budget: $0.01

Quality:       0.82 × 50    = 41.0 points
Cost Eff:      0.95 × 20    = 19.0 points (cheaper)
Performance:   0.72 × 15    = 10.8 points
Learning:      0.60 × 10    =  6.0 points
Preferred:     +0           =  0.0 points
TOTAL:                      = 76.8 points

Result: claude-sonnet-4 selected (90.2 > 76.8)
```

### Stage 3: Selection

```
STANDARD ROUTING:
1. Sort models by score (descending)
2. Select top model
3. Identify fallbacks (positions 2-4)
4. Generate cost prediction
5. Build evidence trail
6. Create rationale

PARALLEL ROUTING (if triggered):
1. Select 3 diverse models
   - Prioritize different providers
   - Balance quality and cost
2. Select judge model
   - High quality
   - Not in parallel set
3. Calculate tradeoff analysis
4. Return parallel decision

PARALLEL TRIGGERS:
- enable_parallel = True, OR
- task_type in [SECURITY_AUDIT, CODE_REVIEW, PLANNING, REASONING], OR
- quality_requirement >= 0.9 AND cost_budget >= $0.05, OR
- metadata.critical = True
```

### Stage 4: Evidence Generation

Every decision includes complete evidence trail:

```
EVIDENCE TYPES:

1. Filtering Evidence
   - "Filtered to 8 models matching requirements"

2. Scoring Evidence (per model)
   - "claude-sonnet-4 score: 90.2 (quality=47.5, cost=17.0, perf=13.2, ...)"

3. Circuit Breaker Evidence
   - "Circuit breaker open for anthropic"

4. Parallel Selection Evidence
   - "Selected 3 models for parallel execution: [claude-opus-4, o1, gpt-5]"

5. Judge Selection Evidence
   - "Judge model: claude-sonnet-4"

Each evidence item includes:
- Unique ID
- Source (router, scoring, circuit_breaker, etc.)
- Description (human-readable)
- Weight (0-1, importance)
- Timestamp
```

## Selection Flow Examples

### Example 1: Budget-Constrained Code Generation

```
REQUEST:
  task_type: CODE_GENERATION
  description: "Implement REST API endpoint"
  cost_budget: $0.001 (very tight)
  quality_requirement: 0.70

STAGE 1 - FILTERING:
  18 models → 12 (quality >= 0.70)
           → 3 (cost <= $0.001)

  Remaining: claude-haiku-4, gemini-flash-1.5, mistral-small-2

STAGE 2 - SCORING:
  claude-haiku-4:
    Quality:    40.0 (0.80 × 50)
    Cost Eff:   18.5 (very cheap)
    Perf:       11.2 (good history)
    Preferred:   5.0 (in budget list)
    TOTAL:      74.7

  gemini-flash-1.5:
    Quality:    40.5 (0.81 × 50)
    Cost Eff:   19.0 (cheapest)
    Perf:        8.3 (moderate history)
    TOTAL:      67.8

  mistral-small-2:
    Quality:    39.0 (0.78 × 50)
    Cost Eff:   18.0
    Perf:        7.5
    TOTAL:      64.5

STAGE 3 - SELECTION:
  Selected: claude-haiku-4 (74.7 points)
  Fallbacks: [gemini-flash-1.5, mistral-small-2]
  Estimated Cost: $0.000425
  Confidence: 0.75

RATIONALE:
  "Selected claude-haiku-4 for code_generation based on:
   quality score 0.80, estimated cost $0.000425,
   preferred for code_generation, strong historical performance.
   Overall score: 74.7/100."
```

### Example 2: High-Quality Reasoning

```
REQUEST:
  task_type: REASONING
  description: "Design distributed system architecture"
  quality_requirement: 0.95
  cost_budget: $0.15

STAGE 1 - FILTERING:
  18 models → 5 (quality >= 0.95)

  Remaining: claude-opus-4, o1, gpt-5, claude-sonnet-4 (0.95)

STAGE 2 - SCORING:
  claude-opus-4:
    Quality:    49.0 (0.98 × 50)
    Cost Eff:   10.0 (expensive)
    Perf:       14.5 (excellent)
    Learning:    9.2 (learned preference)
    Preferred:   5.0 (top for reasoning)
    TOTAL:      87.7

  o1:
    Quality:    48.5 (0.97 × 50)
    Cost Eff:    9.5 (expensive)
    Perf:       14.8 (excellent for reasoning)
    Learning:    8.8
    Preferred:   5.0
    TOTAL:      86.6

  gpt-5:
    Quality:    47.0 (0.94 × 50)
    Cost Eff:   12.0 (moderate cost)
    Perf:       13.5
    Learning:    7.5
    TOTAL:      80.0

STAGE 3 - SELECTION:
  Selected: claude-opus-4 (87.7 points)
  Fallbacks: [o1, gpt-5]
  Estimated Cost: $0.045
  Confidence: 0.88

RATIONALE:
  "Selected claude-opus-4 for reasoning based on:
   quality score 0.98, estimated cost $0.045,
   preferred for reasoning, strong historical performance (0.97).
   Overall score: 87.7/100."
```

### Example 3: Parallel Security Audit

```
REQUEST:
  task_type: SECURITY_AUDIT
  description: "Audit payment processing system"
  quality_requirement: 0.95
  enable_parallel: True

STAGE 1 - FILTERING:
  18 models → 6 (quality >= 0.95, suitable for security)

  Remaining: claude-opus-4, o1, claude-sonnet-4, gpt-5, o1-mini

PARALLEL TRIGGER: Task type is SECURITY_AUDIT (critical)

STAGE 2 - PARALLEL MODEL SELECTION:
  Select 3 diverse models:

  Round 1 (different providers):
    claude-opus-4 (anthropic, score: 88.2)
    o1 (openai, score: 86.5)

  Round 2 (fill remaining):
    claude-sonnet-4 (anthropic, score: 85.0)

  Selected: [claude-opus-4, o1, claude-sonnet-4]

STAGE 3 - JUDGE SELECTION:
  Candidates: gpt-5, o1-mini (not in parallel set)
  Selected: gpt-5 (highest quality of remaining)

COST/QUALITY TRADEOFF:
  Total Cost: $0.125
  Max Quality: 0.98 (claude-opus-4)
  Avg Quality: 0.97
  Quality Improvement: +1.0% vs single model

DECISION:
  Strategy: parallel
  Models: [claude-opus-4, o1, claude-sonnet-4]
  Judge: gpt-5
  Consensus: JUDGE strategy
  Confidence: 0.95

RATIONALE:
  "Parallel execution with 3 models (claude-opus-4, o1, claude-sonnet-4)
   to maximize quality (expected: 0.98) at estimated cost $0.125.
   Judge model gpt-5 will select best output."
```

### Example 4: Long Context Analysis

```
REQUEST:
  task_type: LONG_CONTEXT
  description: "Analyze 50k lines of code"
  context_size: 150,000 tokens
  quality_requirement: 0.85

STAGE 1 - FILTERING:
  18 models → 16 (quality >= 0.85)
           → 6 (context_window >= 150,000)

  Remaining: gemini-pro-1.5 (2M), gemini-flash-1.5 (1M),
             claude-opus-4 (200k), claude-sonnet-4 (200k),
             claude-haiku-4 (200k), gemini-2.0-flash-thinking (1M)

STAGE 2 - SCORING:
  gemini-pro-1.5:
    Quality:    44.5 (0.89 × 50)
    Cost Eff:   15.0
    Perf:       12.0
    Preferred:   5.0 (top for long_context)
    TOTAL:      76.5

  claude-sonnet-4:
    Quality:    47.5 (0.95 × 50)
    Cost Eff:   12.0
    Perf:       13.5
    TOTAL:      73.0

  gemini-2.0-flash-thinking:
    Quality:    44.0 (0.88 × 50)
    Cost Eff:   20.0 (FREE!)
    Perf:        5.0 (limited history)
    Preferred:   5.0
    TOTAL:      74.0

STAGE 3 - SELECTION:
  Selected: gemini-pro-1.5 (76.5 points)
  Fallbacks: [gemini-2.0-flash-thinking, claude-sonnet-4]
  Estimated Cost: $0.052
  Confidence: 0.77

RATIONALE:
  "Selected gemini-pro-1.5 for long_context based on:
   quality score 0.89, estimated cost $0.052,
   supports 2M context window, preferred for long_context.
   Overall score: 76.5/100."
```

### Example 5: Fast Multimodal with Vision

```
REQUEST:
  task_type: MULTIMODAL
  description: "Analyze UI screenshot for accessibility"
  requires_vision: True
  latency_requirement_ms: 3000
  quality_requirement: 0.85

STAGE 1 - FILTERING:
  18 models → 14 (quality >= 0.85)
           → 9 (vision capability)
           → 6 (latency <= 3000ms)

  Remaining: gpt-4o (600ms), claude-haiku-4 (300ms),
             gpt-4o-mini (400ms), gemini-flash-1.5 (500ms),
             gemini-pro-1.5 (900ms), claude-sonnet-4 (800ms)

STAGE 2 - SCORING:
  gpt-4o:
    Quality:    46.0 (0.92 × 50)
    Cost Eff:   16.0
    Perf:       12.5
    Preferred:   5.0
    TOTAL:      79.5

  claude-sonnet-4:
    Quality:    47.5 (0.95 × 50)
    Cost Eff:   15.0
    Perf:       13.0
    Preferred:   5.0
    TOTAL:      80.5

  claude-haiku-4:
    Quality:    40.0 (0.80 × 50) [Filtered: quality too low]

STAGE 3 - SELECTION:
  Selected: claude-sonnet-4 (80.5 points)
  Fallbacks: [gpt-4o, gemini-pro-1.5]
  Estimated Cost: $0.0034
  Confidence: 0.81

RATIONALE:
  "Selected claude-sonnet-4 for multimodal based on:
   quality score 0.95, estimated cost $0.0034,
   supports vision, low latency (P95: 2000ms),
   preferred for multimodal. Overall score: 80.5/100."
```

### Example 6: Vendor Diversity Pattern

```
REQUEST SEQUENCE (5 requests, vendor_diversity=True):

Request 1: CODE_GENERATION
  Last 5 providers: []
  Selected: claude-sonnet-4 (anthropic)
  Score: 85.0 (no diversity bonus)

Request 2: CODE_GENERATION
  Last 5 providers: [anthropic]
  Scoring:
    gpt-4o (openai): 80.0 + 3.0 (diversity) = 83.0
    claude-sonnet-4 (anthropic): 85.0
  Selected: claude-sonnet-4 (anthropic)
  Score: 85.0 (still highest even without bonus)

Request 3: CODE_GENERATION
  Last 5 providers: [anthropic, anthropic]
  Scoring:
    gpt-4o (openai): 80.0 + 3.0 = 83.0
    gemini-pro-1.5 (google): 76.0 + 3.0 = 79.0
    claude-sonnet-4 (anthropic): 85.0
  Selected: claude-sonnet-4 (anthropic)

Request 4: CODE_GENERATION (adjusted quality requirement)
  Last 5 providers: [anthropic, anthropic, anthropic]
  Scoring:
    gpt-4o (openai): 80.0 + 3.0 = 83.0
    claude-sonnet-4 (anthropic): 82.0
  Selected: gpt-4o (openai)
  Score: 83.0 (diversity bonus tipped the scale)

Request 5: CODE_GENERATION
  Last 5 providers: [anthropic, anthropic, anthropic, openai]
  Scoring:
    gemini-pro-1.5 (google): 76.0 + 3.0 = 79.0
    mistral-large-2 (mistral): 75.0 + 3.0 = 78.0
    gpt-4o (openai): 80.0
    claude-sonnet-4 (anthropic): 85.0
  Selected: claude-sonnet-4 (anthropic)

RESULT: Provider distribution: 4 Anthropic, 1 OpenAI
Note: Diversity bonus helps but doesn't override significant quality differences
```

## Circuit Breaker State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                   │
└─────────────────────────────────────────────────────────────┘

     ┌─────────────────┐
     │     CLOSED      │ ◄──────────────────┐
     │  (Normal Ops)   │                    │
     └────────┬────────┘                    │
              │                             │
              │ 5 consecutive failures      │ Success in
              │                             │ half-open
              ▼                             │
     ┌─────────────────┐                    │
     │      OPEN       │                    │
     │ (Blocked: 60s)  │                    │
     └────────┬────────┘                    │
              │                             │
              │ 60 seconds elapsed          │
              │                             │
              ▼                             │
     ┌─────────────────┐                    │
     │   HALF-OPEN     │────────────────────┘
     │   (Testing)     │
     └────────┬────────┘
              │
              │ Failure
              │
              ▼
           (back to OPEN)

TRANSITION RULES:
- CLOSED → OPEN: 5 consecutive failures
- OPEN → HALF-OPEN: 60 seconds timeout
- HALF-OPEN → CLOSED: Any success
- HALF-OPEN → OPEN: Any failure
- Any state: Success resets failure counter
```

## Performance Confidence Calculation

```
CONFIDENCE FORMULA:

confidence = sample_confidence × recency_decay

Where:
  sample_confidence = min(1.0, total_requests / 100)
  recency_decay = 0.5 ^ (age_hours / 168)

EXAMPLES:

Scenario 1: New model, limited data
  total_requests = 5
  age = 1 day (24 hours)
  sample_confidence = min(1.0, 5/100) = 0.05
  recency_decay = 0.5 ^ (24/168) = 0.91
  confidence = 0.05 × 0.91 = 0.046 (very low)

Scenario 2: Established model, recent data
  total_requests = 100
  age = 1 day
  sample_confidence = min(1.0, 100/100) = 1.0
  recency_decay = 0.5 ^ (24/168) = 0.91
  confidence = 1.0 × 0.91 = 0.91 (high)

Scenario 3: Established model, old data
  total_requests = 100
  age = 7 days (168 hours)
  sample_confidence = 1.0
  recency_decay = 0.5 ^ (168/168) = 0.5
  confidence = 1.0 × 0.5 = 0.50 (moderate)

Scenario 4: Lots of data, very old
  total_requests = 500
  age = 30 days (720 hours)
  sample_confidence = 1.0
  recency_decay = 0.5 ^ (720/168) = 0.04
  confidence = 1.0 × 0.04 = 0.04 (low despite volume)

IMPACT ON ROUTING:
- confidence < 0.5: Limited weight in decision (0-7.5 points)
- confidence >= 0.5: Moderate weight (7.5-15 points)
- confidence >= 0.8: High weight (12-15 points)
```

## Learning Loop Feedback Scoring

```
FEEDBACK SCORE CALCULATION:

base_score = OUTCOME_WEIGHTS[outcome]
  success: 1.0
  partial: 0.5
  failure: 0.0

if quality_score provided:
  base_score = (base_score + quality_score) / 2

if pr_merged:
  base_score += 0.2

if pr_reverted:
  base_score -= 0.5

if user_rating provided:
  rating_score = (user_rating - 1) / 4  # 1-5 → 0-1
  base_score = (base_score + rating_score) / 2

final_score = clamp(base_score, 0.0, 1.0)

EXAMPLES:

Scenario 1: Perfect execution
  outcome = success (1.0)
  quality_score = 0.95
  pr_merged = True
  user_rating = 5

  base = (1.0 + 0.95) / 2 = 0.975
  + pr_merged = 0.975 + 0.2 = 1.175
  rating = (5-1)/4 = 1.0
  final = (1.175 + 1.0) / 2 = 1.0875 → clamped to 1.0

Scenario 2: Success but PR reverted
  outcome = success (1.0)
  quality_score = 0.80
  pr_merged = True
  pr_reverted = True
  user_rating = 3

  base = (1.0 + 0.80) / 2 = 0.90
  + pr_merged = 0.90 + 0.2 = 1.10
  - pr_reverted = 1.10 - 0.5 = 0.60
  rating = (3-1)/4 = 0.5
  final = (0.60 + 0.5) / 2 = 0.55

Scenario 3: Partial success
  outcome = partial (0.5)
  quality_score = 0.60
  user_rating = 3

  base = (0.5 + 0.60) / 2 = 0.55
  rating = 0.5
  final = (0.55 + 0.5) / 2 = 0.525

Scenario 4: Complete failure
  outcome = failure (0.0)
  quality_score = 0.30

  base = (0.0 + 0.30) / 2 = 0.15
  final = 0.15

WEIGHT UPDATE:
  new_weight = 0.1 × final_score + 0.9 × old_weight

  Example: old_weight = 0.70, final_score = 1.0
    new_weight = 0.1 × 1.0 + 0.9 × 0.70 = 0.73

  Example: old_weight = 0.70, final_score = 0.15
    new_weight = 0.1 × 0.15 + 0.9 × 0.70 = 0.645
```

## Cost Prediction Algorithm

```
TOKEN ESTIMATION:

1. From description:
   word_count = len(description.split())
   base_tokens = word_count × 1.3 (avg tokens per word)

2. Task-type multipliers:
   CODE_GENERATION: input×1.0, output×3.0
   REASONING: input×1.2, output×2.5
   CODE_REVIEW: input×2.0, output×1.5
   LONG_CONTEXT: input×5.0, output×1.5

3. Complexity indicators:
   "detailed", "comprehensive" → output×2
   "simple", "brief" → output×0.6

4. Final estimation:
   input_tokens = base_tokens × input_multiplier
   output_tokens = base_output × output_multiplier

COST CALCULATION:

input_cost = (input_tokens / 1000) × cost_per_1k_input
output_cost = (output_tokens / 1000) × cost_per_1k_output
expected_cost = input_cost + output_cost

Variance (30%):
min_cost = expected_cost × 0.7
max_cost = expected_cost × 1.3

EXAMPLE:

Description: "Implement comprehensive REST API with authentication"
Task: CODE_GENERATION

Step 1: Base estimation
  word_count = 7
  base_tokens = 7 × 1.3 = 9.1 → 10 tokens

Step 2: Task multiplier
  input = 10 × 1.0 = 10 tokens
  base_output = 500 tokens (default)
  output = 500 × 3.0 = 1500 tokens

Step 3: Complexity
  "comprehensive" detected → 1500 × 2 = 3000 tokens

Step 4: Cost for claude-sonnet-4
  input_cost = (10 / 1000) × 0.003 = $0.000030
  output_cost = (3000 / 1000) × 0.015 = $0.045000
  expected = $0.045030

  min = $0.045030 × 0.7 = $0.031521
  max = $0.045030 × 1.3 = $0.058539

Step 5: Budget check
  If budget = $0.01 → NOT within_budget (max > budget)
  If budget = $0.10 → within_budget
```

## Summary

The MoE Router implements a comprehensive, evidence-based selection algorithm that:

1. **Filters** models by hard requirements (capabilities, quality, budget, latency)
2. **Scores** models using 7 weighted factors (quality, cost, performance, learning, preferences)
3. **Selects** the optimal model or triggers parallel execution for critical tasks
4. **Learns** from feedback to continuously improve routing decisions
5. **Protects** against failures using circuit breakers
6. **Documents** every decision with complete evidence trails

The algorithm balances multiple competing objectives to deliver optimal model selection for each unique request while maintaining cost efficiency, quality standards, and system reliability.
