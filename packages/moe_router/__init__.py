"""
MoE Router Package

Intelligent model selection for AI agents using Mixture-of-Experts routing.
"""
from .router import MoERouter
from .models import (
    ModelDefinition,
    RoutingRequest,
    RoutingDecision,
    TaskType,
    Provider,
    Evidence,
    PerformanceMetrics,
    FeedbackData,
    CostPrediction
)
from .strategies.cost_predictor import CostPredictor
from .strategies.performance_tracker import PerformanceTracker
from .strategies.hybrid_router import HybridRouter, ConsensusStrategy
from .strategies.learning_loop import LearningLoop

__version__ = "1.0.0"

__all__ = [
    # Main router
    "MoERouter",

    # Models and types
    "ModelDefinition",
    "RoutingRequest",
    "RoutingDecision",
    "TaskType",
    "Provider",
    "Evidence",
    "PerformanceMetrics",
    "FeedbackData",
    "CostPrediction",

    # Strategies
    "CostPredictor",
    "PerformanceTracker",
    "HybridRouter",
    "ConsensusStrategy",
    "LearningLoop",
]
