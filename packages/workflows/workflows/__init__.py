"""
Workflow definitions for the autonomous coding system
"""

from .plan_patch_pr import (
    PlanPatchPRWorkflow,
    IncrementalPatchWorkflow,
    PRResult,
    Design,
    Issue,
    Patch,
    QAResult,
)
from .incident_swarm import (
    IncidentSwarmWorkflow,
    ContinuousMonitoringWorkflow,
    Alert,
    Diagnosis,
    ConsensusResult,
    IncidentResult,
)
from .migration import (
    CodeMigrationWorkflow,
    MigrationStep,
    MigrationPlan,
    StepResult,
    MigrationResult,
)
from .quality_gate import (
    QualityGateWorkflow,
    ContinuousQualityWorkflow,
    QualityCheck,
    QualityGateResult,
)

__all__ = [
    # Plan-Patch-PR
    'PlanPatchPRWorkflow',
    'IncrementalPatchWorkflow',
    'PRResult',
    'Design',
    'Issue',
    'Patch',
    'QAResult',
    # Incident Response
    'IncidentSwarmWorkflow',
    'ContinuousMonitoringWorkflow',
    'Alert',
    'Diagnosis',
    'ConsensusResult',
    'IncidentResult',
    # Migration
    'CodeMigrationWorkflow',
    'MigrationStep',
    'MigrationPlan',
    'StepResult',
    'MigrationResult',
    # Quality Gate
    'QualityGateWorkflow',
    'ContinuousQualityWorkflow',
    'QualityCheck',
    'QualityGateResult',
]
