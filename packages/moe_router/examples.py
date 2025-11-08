"""
MoE Router Examples and Usage Demonstrations

This file demonstrates the routing algorithm and various selection flows.
"""
from router import MoERouter
from models import RoutingRequest, TaskType, Provider, FeedbackData


def example_basic_routing():
    """Example 1: Basic routing with cost constraints"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Budget-Constrained Code Generation")
    print("="*80)

    router = MoERouter(enable_learning=False)

    request = RoutingRequest(
        task_type=TaskType.CODE_GENERATION,
        task_description="Implement a simple REST API endpoint for user registration",
        cost_budget=0.005,
        quality_requirement=0.75,
        requires_tools=True
    )

    decision = router.select_model(request)

    print(f"\n📊 ROUTING DECISION")
    print(f"Selected Model: {decision.selected_model}")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Estimated Cost: ${decision.estimated_cost:.6f}")
    print(f"Estimated Quality: {decision.estimated_quality:.2f}")
    print(f"\n💡 Rationale:")
    print(f"  {decision.rationale}")
    print(f"\n🔄 Fallback Models:")
    for i, fallback in enumerate(decision.fallback_models, 1):
        print(f"  {i}. {fallback}")
    print(f"\n📝 Evidence Trail:")
    for evidence in decision.evidence:
        print(f"  [{evidence.source}] {evidence.description} (weight: {evidence.weight:.2f})")


def example_high_quality_reasoning():
    """Example 2: High-quality reasoning task"""
    print("\n" + "="*80)
    print("EXAMPLE 2: High-Quality Reasoning Task")
    print("="*80)

    router = MoERouter(enable_learning=False)

    request = RoutingRequest(
        task_type=TaskType.REASONING,
        task_description=(
            "Design a comprehensive distributed system architecture for a "
            "real-time analytics platform handling 10M events/sec with 99.99% uptime"
        ),
        quality_requirement=0.95,
        cost_budget=0.15,
        estimated_output_tokens=3000
    )

    decision = router.select_model(request)

    print(f"\n📊 ROUTING DECISION")
    print(f"Selected Model: {decision.selected_model}")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Estimated Cost: ${decision.estimated_cost:.6f}")
    print(f"Strategy: {decision.routing_strategy}")
    print(f"\n💡 Rationale:")
    print(f"  {decision.rationale}")
    print(f"\n🎯 Metadata:")
    for key, value in decision.metadata.items():
        print(f"  {key}: {value}")


def example_parallel_execution():
    """Example 3: Parallel execution for critical security audit"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Parallel Execution for Security Audit")
    print("="*80)

    router = MoERouter(enable_learning=False)

    request = RoutingRequest(
        task_type=TaskType.SECURITY_AUDIT,
        task_description=(
            "Comprehensive security audit of payment processing system "
            "including PCI-DSS compliance check, vulnerability assessment, "
            "and penetration testing recommendations"
        ),
        quality_requirement=0.95,
        cost_budget=0.30,
        enable_parallel=True,
        estimated_input_tokens=5000,
        estimated_output_tokens=2500
    )

    decision = router.select_model(request)

    print(f"\n📊 ROUTING DECISION")
    print(f"Strategy: {decision.routing_strategy}")
    print(f"Parallel Models: {decision.parallel_models}")
    print(f"Judge Model: {decision.metadata.get('judge_model', 'N/A')}")
    print(f"Total Estimated Cost: ${decision.estimated_cost:.6f}")
    print(f"Expected Quality: {decision.estimated_quality:.2f}")
    print(f"\n💡 Rationale:")
    print(f"  {decision.rationale}")

    if 'tradeoff_analysis' in decision.metadata:
        tradeoff = decision.metadata['tradeoff_analysis']
        print(f"\n⚖️  Cost/Quality Tradeoff Analysis:")
        print(f"  Number of Models: {tradeoff['num_models']}")
        print(f"  Total Cost: ${tradeoff['total_cost']:.6f}")
        print(f"  Max Quality: {tradeoff['max_quality']:.2f}")
        print(f"  Quality Improvement: +{tradeoff['quality_improvement']:.2%}")
        print(f"  Within Budget: {tradeoff['within_budget']}")


def example_long_context():
    """Example 4: Long context analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Long Context Code Analysis")
    print("="*80)

    router = MoERouter(enable_learning=False)

    request = RoutingRequest(
        task_type=TaskType.LONG_CONTEXT,
        task_description=(
            "Analyze entire codebase (50k lines) for technical debt, "
            "code smells, and refactoring opportunities"
        ),
        context_size=150000,  # 150k token context
        quality_requirement=0.85,
        cost_budget=0.10,
        estimated_output_tokens=4000
    )

    decision = router.select_model(request)

    print(f"\n📊 ROUTING DECISION")
    print(f"Selected Model: {decision.selected_model}")
    print(f"Context Requirement: 150,000 tokens")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Estimated Cost: ${decision.estimated_cost:.6f}")
    print(f"\n💡 Rationale:")
    print(f"  {decision.rationale}")

    # Show which models were filtered out due to context size
    print(f"\n🔍 Model Filtering:")
    print(f"  Total models in registry: {len(router.models)}")
    print(f"  Candidates after filtering: {decision.metadata.get('num_candidates', 'N/A')}")


def example_multimodal_fast():
    """Example 5: Fast multimodal task"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Fast Multimodal Vision Task")
    print("="*80)

    router = MoERouter(enable_learning=False)

    request = RoutingRequest(
        task_type=TaskType.MULTIMODAL,
        task_description=(
            "Analyze UI screenshot for accessibility issues and generate "
            "WCAG 2.1 compliance report with specific recommendations"
        ),
        requires_vision=True,
        latency_requirement_ms=3000,  # 3 second max
        quality_requirement=0.85,
        cost_budget=0.01,
        estimated_input_tokens=2000,  # Including image tokens
        estimated_output_tokens=800
    )

    decision = router.select_model(request)

    print(f"\n📊 ROUTING DECISION")
    print(f"Selected Model: {decision.selected_model}")
    print(f"Requirements: Vision support, <3s latency")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Estimated Cost: ${decision.estimated_cost:.6f}")
    print(f"\n💡 Rationale:")
    print(f"  {decision.rationale}")


def example_vendor_diversity():
    """Example 6: Vendor diversity preference"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Vendor Diversity for Risk Mitigation")
    print("="*80)

    router = MoERouter(enable_learning=False)

    # Make several requests with vendor diversity
    print("\nMaking 5 sequential requests with vendor_diversity=True\n")

    for i in range(5):
        request = RoutingRequest(
            task_type=TaskType.CODE_GENERATION,
            task_description=f"Generate unit tests for module {i+1}",
            quality_requirement=0.80,
            vendor_diversity=True
        )

        decision = router.select_model(request)
        model = router._get_model_by_id(decision.selected_model)

        print(f"Request {i+1}: {decision.selected_model} ({model.provider.value})")

    print("\n💡 Notice how different providers are selected to maintain diversity")


def example_learning_loop():
    """Example 7: Learning loop with feedback"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Learning Loop with Feedback")
    print("="*80)

    router = MoERouter(enable_learning=True)

    # Initial request
    request = RoutingRequest(
        task_type=TaskType.CODE_REVIEW,
        task_description="Review pull request for security vulnerabilities",
        quality_requirement=0.85
    )

    print("\n📝 Initial Model Weights (before feedback):")
    models_to_check = ["claude-sonnet-4", "gpt-5", "claude-opus-4"]
    for model_id in models_to_check:
        weight = router.learning_loop.get_model_weight(model_id, TaskType.CODE_REVIEW)
        print(f"  {model_id}: {weight:.4f}")

    # Simulate feedback from multiple requests
    print("\n📊 Simulating feedback from 10 requests...")

    feedback_data = [
        # Claude Sonnet performs well
        ("claude-sonnet-4", "success", 0.92, True, False, 5),
        ("claude-sonnet-4", "success", 0.88, True, False, 4),
        ("claude-sonnet-4", "success", 0.90, True, False, 5),

        # GPT-5 has mixed results
        ("gpt-5", "success", 0.85, True, False, 4),
        ("gpt-5", "partial", 0.70, False, False, 3),
        ("gpt-5", "success", 0.82, True, False, 4),

        # Claude Opus excellent but one PR reverted
        ("claude-opus-4", "success", 0.95, True, False, 5),
        ("claude-opus-4", "success", 0.93, True, True, 3),  # Reverted!
        ("claude-opus-4", "success", 0.96, True, False, 5),
        ("claude-opus-4", "success", 0.94, True, False, 5),
    ]

    for i, (model_id, outcome, quality, merged, reverted, rating) in enumerate(feedback_data):
        feedback = FeedbackData(
            request_id=f"req_{i}",
            model_id=model_id,
            task_type=TaskType.CODE_REVIEW,
            outcome=outcome,
            quality_score=quality,
            pr_merged=merged,
            pr_reverted=reverted,
            user_rating=rating
        )
        router.learning_loop.collect_feedback(feedback)

    print("\n📊 Updated Model Weights (after feedback):")
    for model_id in models_to_check:
        weight = router.learning_loop.get_model_weight(model_id, TaskType.CODE_REVIEW)
        print(f"  {model_id}: {weight:.4f}")

    print("\n💡 Notice how weights adjusted based on performance:")
    print("   - Claude Sonnet: High success rate → increased weight")
    print("   - GPT-5: Mixed results → moderate weight")
    print("   - Claude Opus: High quality but PR revert → penalty applied")


def example_ab_testing():
    """Example 8: A/B testing framework"""
    print("\n" + "="*80)
    print("EXAMPLE 8: A/B Testing Two Models")
    print("="*80)

    router = MoERouter(enable_learning=True)

    # Start A/B test
    print("\n🧪 Starting A/B test: claude-sonnet-4 vs gpt-4o for code generation")

    test_id = router.learning_loop.start_ab_test(
        model_a="claude-sonnet-4",
        model_b="gpt-4o",
        task_type=TaskType.CODE_GENERATION,
        traffic_split=0.5,
        min_samples=20,
        duration_days=7
    )

    print(f"Test ID: {test_id}")

    # Simulate test results
    print("\n📊 Simulating 40 requests (20 per variant)...")

    # Variant A (claude-sonnet-4) - slightly better
    for i in range(20):
        outcome = "success" if i < 17 else "partial"  # 85% success
        quality = 0.88 + (i % 5) * 0.02
        merged = i < 16  # 80% merged

        feedback = FeedbackData(
            request_id=f"test_a_{i}",
            model_id="claude-sonnet-4",
            task_type=TaskType.CODE_GENERATION,
            outcome=outcome,
            quality_score=quality,
            pr_merged=merged,
            user_rating=4 if outcome == "success" else 3
        )
        router.learning_loop.collect_feedback(feedback)

    # Variant B (gpt-4o) - slightly worse
    for i in range(20):
        outcome = "success" if i < 15 else "partial"  # 75% success
        quality = 0.84 + (i % 5) * 0.02
        merged = i < 14  # 70% merged

        feedback = FeedbackData(
            request_id=f"test_b_{i}",
            model_id="gpt-4o",
            task_type=TaskType.CODE_GENERATION,
            outcome=outcome,
            quality_score=quality,
            pr_merged=merged,
            user_rating=4 if outcome == "success" else 3
        )
        router.learning_loop.collect_feedback(feedback)

    # Analyze results
    print("\n📈 A/B Test Results:")
    results = router.learning_loop.analyze_ab_test(test_id)

    print(f"\nTest: {results['model_a']} vs {results['model_b']}")
    print(f"Status: {results['status']}")
    print(f"\nVariant A ({results['variant_a']['model']}):")
    print(f"  Samples: {results['variant_a']['samples']}")
    print(f"  Success Rate: {results['variant_a']['success_rate']:.1%}")
    print(f"  Avg Score: {results['variant_a']['avg_score']:.4f}")
    print(f"\nVariant B ({results['variant_b']['model']}):")
    print(f"  Samples: {results['variant_b']['samples']}")
    print(f"  Success Rate: {results['variant_b']['success_rate']:.1%}")
    print(f"  Avg Score: {results['variant_b']['avg_score']:.4f}")
    print(f"\n🏆 Winner: {results['winner']}")
    print(f"📊 Confidence: {results['confidence']:.1%}")
    print(f"\n💡 Recommendation:")
    print(f"  {results['recommendation']}")


def example_circuit_breaker():
    """Example 9: Circuit breaker in action"""
    print("\n" + "="*80)
    print("EXAMPLE 9: Circuit Breaker Protection")
    print("="*80)

    router = MoERouter(enable_circuit_breaker=True)

    print("\n⚡ Simulating provider failures...")

    # Simulate 5 consecutive failures for Anthropic
    for i in range(5):
        router.record_request_outcome(
            model_id="claude-sonnet-4",
            success=False,
            error=f"Connection timeout #{i+1}"
        )

    print("\n🔴 Circuit Breaker Status:")
    status = router.get_circuit_breaker_status()
    for provider, state in status.items():
        print(f"\n  {provider}:")
        print(f"    State: {state['state']}")
        print(f"    Failures: {state['failure_count']}")
        print(f"    Next Retry: {state['next_retry']}")

    # Try to route with circuit breaker open
    print("\n📝 Attempting to route with Anthropic circuit breaker open...")

    request = RoutingRequest(
        task_type=TaskType.CODE_GENERATION,
        task_description="Generate API endpoint",
        vendor_preference=Provider.ANTHROPIC
    )

    decision = router.select_model(request)

    print(f"\n📊 Routing Decision:")
    print(f"  Selected: {decision.selected_model}")
    model = router._get_model_by_id(decision.selected_model)
    if model:
        print(f"  Provider: {model.provider.value}")
        print(f"  💡 Router avoided Anthropic due to open circuit breaker")


def example_cost_comparison():
    """Example 10: Cost comparison across models"""
    print("\n" + "="*80)
    print("EXAMPLE 10: Cost Comparison Analysis")
    print("="*80)

    router = MoERouter()

    request = RoutingRequest(
        task_type=TaskType.CODE_GENERATION,
        task_description="Implement comprehensive test suite for authentication module",
        estimated_input_tokens=2000,
        estimated_output_tokens=5000,
        quality_requirement=0.80
    )

    # Get all capable models
    capable_models = router._filter_available_models(request, [])

    print(f"\n💰 Cost Comparison for {len(capable_models)} Models:")
    print(f"   Input: {request.estimated_input_tokens} tokens")
    print(f"   Output: {request.estimated_output_tokens} tokens")

    # Compare costs
    comparison = router.cost_predictor.compare_model_costs(capable_models, request)

    print(f"\n📊 Statistics:")
    print(f"   Cheapest: {comparison['cheapest_model']} (${comparison['cheapest_cost']:.6f})")
    print(f"   Most Expensive: {comparison['most_expensive_model']} (${comparison['most_expensive_cost']:.6f})")
    print(f"   Average: ${comparison['avg_cost']:.6f}")
    print(f"   Median: ${comparison['median_cost']:.6f}")
    print(f"   Range: ${comparison['cost_range']:.6f}")

    print(f"\n📋 Top 10 by Cost:")
    for i, pred in enumerate(comparison['predictions'][:10], 1):
        model = router._get_model_by_id(pred.model_id)
        print(f"   {i:2d}. {pred.model_id:25s} ${pred.expected_cost:.6f} (quality: {model.quality_score:.2f})")


def routing_algorithm_description():
    """Print detailed routing algorithm description"""
    print("\n" + "="*80)
    print("MoE ROUTER - ROUTING ALGORITHM DESCRIPTION")
    print("="*80)

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ROUTING ALGORITHM OVERVIEW                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

The MoE Router uses a multi-stage intelligent selection algorithm:

┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: FILTERING                                                           │
└──────────────────────────────────────────────────────────────────────────────┘

  1. Remove disabled models (enabled=false in config)
  2. Check circuit breaker status (open = skip provider)
  3. Verify quality threshold (model.quality_score >= requirement)
  4. Validate context window (model.context_window >= required)
  5. Check capability requirements:
     - Vision: requires vision capability
     - Tools: requires function_calling capability
     - JSON Mode: requires json_mode capability
     - Streaming: requires streaming support
  6. Validate latency requirements (model.p95_latency <= requirement)
  7. Verify budget constraints (estimated_cost <= budget)

  Output: List of capable models

┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: SCORING (0-100 points)                                              │
└──────────────────────────────────────────────────────────────────────────────┘

  Each model receives a composite score:

  1. Quality Score (0-50 points)
     - Base model quality rating
     - Formula: model.quality_score × 50

  2. Cost Efficiency (0-20 points)
     - Lower cost = higher score
     - Formula: (1 / (1 + cost × 100)) × 20

  3. Performance History (0-15 points)
     - Success rate from performance tracker
     - Includes time decay (half-life: 1 week)
     - Formula: recommendation_weight × 15

  4. Learning Weight (0-10 points)
     - Learned preference from feedback loop
     - Based on PR outcomes, user ratings
     - Formula: learned_weight × 10

  5. Task Preference Bonus (0-5 points)
     - Model appears in task_preferences.preferred list
     - Flat +5 points

  6. Vendor Diversity Bonus (0-3 points)
     - Different provider from last 5 requests
     - Flat +3 points

  7. Vendor Preference Bonus (0-2 points)
     - Matches user-specified provider preference
     - Flat +2 points

  Output: Sorted list of (model, score) tuples

┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: SELECTION                                                           │
└──────────────────────────────────────────────────────────────────────────────┘

  Standard Mode:
    - Select highest scoring model
    - Identify top 3 fallbacks (2nd, 3rd, 4th highest scores)
    - Generate cost prediction
    - Build evidence trail

  Parallel Mode (if triggered):
    - Select 3 diverse models (prefer different providers)
    - Select judge model (high quality, not in parallel set)
    - Calculate cost/quality tradeoff
    - Return parallel execution decision

  Output: RoutingDecision with rationale and evidence

┌──────────────────────────────────────────────────────────────────────────────┐
│ PARALLEL EXECUTION TRIGGERS                                                  │
└──────────────────────────────────────────────────────────────────────────────┘

  Parallel execution is activated when ANY of:
    ✓ request.enable_parallel = True
    ✓ task_type in [SECURITY_AUDIT, CODE_REVIEW, PLANNING, REASONING]
    ✓ quality_requirement >= 0.9 AND cost_budget >= $0.05
    ✓ metadata.critical = True

  Parallel Process:
    1. Execute all models concurrently
    2. Collect responses with timeout (60s default)
    3. Apply consensus strategy:
       - JUDGE: Judge model evaluates and selects best
       - QUALITY_WEIGHTED: Highest quality model wins
       - VOTING: Majority voting (requires comparable outputs)
       - FIRST_SUCCESS: Use first successful response

┌──────────────────────────────────────────────────────────────────────────────┐
│ CIRCUIT BREAKER STATES                                                       │
└──────────────────────────────────────────────────────────────────────────────┘

  CLOSED (Normal):
    - All requests allowed
    - Tracking failure count

  OPEN (Failing):
    - All requests blocked
    - Triggered by 5 consecutive failures
    - Automatic retry after 60 seconds

  HALF-OPEN (Testing):
    - Limited requests allowed
    - Testing if provider recovered
    - Single success → CLOSED
    - Single failure → OPEN

┌──────────────────────────────────────────────────────────────────────────────┐
│ LEARNING LOOP                                                                │
└──────────────────────────────────────────────────────────────────────────────┘

  Feedback Scoring:
    - Base: outcome (success=1.0, partial=0.5, failure=0.0)
    - Quality: averaged with outcome
    - PR merged: +0.2 bonus
    - PR reverted: -0.5 penalty
    - User rating: 1-5 normalized to 0-1

  Weight Updates:
    - Exponential moving average (α=0.1)
    - new_weight = 0.1 × feedback_score + 0.9 × old_weight
    - Clamped to [0, 1]

  A/B Testing:
    - Random assignment based on traffic split
    - Minimum 30 samples per variant
    - Statistical comparison with 5% threshold
    - Automatic winner determination

╔══════════════════════════════════════════════════════════════════════════════╗
║                          EVIDENCE & RATIONALE                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Every routing decision includes:
  ✓ Selected model with rationale
  ✓ Confidence score (0-1)
  ✓ Cost prediction (min/max/expected)
  ✓ Quality estimate
  ✓ Fallback models (ordered)
  ✓ Evidence trail with sources
  ✓ Metadata (scores, analysis)

This ensures transparency and auditability of all routing decisions.
""")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("MoE ROUTER - COMPREHENSIVE EXAMPLES")
    print("="*80)

    # Print algorithm description
    routing_algorithm_description()

    # Run examples
    example_basic_routing()
    example_high_quality_reasoning()
    example_parallel_execution()
    example_long_context()
    example_multimodal_fast()
    example_vendor_diversity()
    example_learning_loop()
    example_ab_testing()
    example_circuit_breaker()
    example_cost_comparison()

    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80)
    print("\nFor more information, see README.md")
    print()


if __name__ == "__main__":
    main()
