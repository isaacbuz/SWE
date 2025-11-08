"""
Coordination Agents Package

Provides coordination agents for managing parallel execution,
resolving conflicts, and optimizing resources.
"""
from .swarm_coordinator import SwarmCoordinator, SwarmExecution, SubTask
from .conflict_resolver import ConflictResolver, Conflict, AgentPosition
from .resource_optimizer import (
    ResourceOptimizer,
    WorkloadMetrics,
    BottleneckAnalysis,
    ScalingRecommendation,
    OptimizationGoal
)

__all__ = [
    "SwarmCoordinator",
    "SwarmExecution",
    "SubTask",
    "ConflictResolver",
    "Conflict",
    "AgentPosition",
    "ResourceOptimizer",
    "WorkloadMetrics",
    "BottleneckAnalysis",
    "ScalingRecommendation",
    "OptimizationGoal",
]
