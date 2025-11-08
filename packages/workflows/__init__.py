"""
Temporal Workflows for Autonomous Coding System

This package provides durable, fault-tolerant orchestration for complex
software development tasks using Temporal.
"""

from .workflows import (
    PlanPatchPRWorkflow,
    IncrementalPatchWorkflow,
    IncidentSwarmWorkflow,
    ContinuousMonitoringWorkflow,
    CodeMigrationWorkflow,
    QualityGateWorkflow,
    ContinuousQualityWorkflow,
)

from .client import WorkflowClient

__version__ = "0.1.0"

__all__ = [
    # Workflows
    'PlanPatchPRWorkflow',
    'IncrementalPatchWorkflow',
    'IncidentSwarmWorkflow',
    'ContinuousMonitoringWorkflow',
    'CodeMigrationWorkflow',
    'QualityGateWorkflow',
    'ContinuousQualityWorkflow',
    # Client
    'WorkflowClient',
]
