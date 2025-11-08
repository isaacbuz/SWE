"""
Configuration for Temporal workflows

Centralized configuration for workflow timeouts, retry policies,
and other workflow settings.
"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, Any


# Task queue configuration
TASK_QUEUE = "autonomous-coding-task-queue"
NAMESPACE = "default"


# Temporal server configuration
class TemporalConfig:
    """Temporal server connection configuration"""

    def __init__(
        self,
        host: str = "localhost:7233",
        namespace: str = NAMESPACE,
        task_queue: str = TASK_QUEUE,
    ):
        self.host = host
        self.namespace = namespace
        self.task_queue = task_queue


# Workflow timeout configurations
class WorkflowTimeouts:
    """Default timeout configurations for workflows"""

    PLAN_PATCH_PR = timedelta(hours=2)
    INCREMENTAL_PATCH = timedelta(minutes=30)
    INCIDENT_SWARM = timedelta(hours=1)
    CONTINUOUS_MONITORING = timedelta(days=365)  # Long-running
    CODE_MIGRATION = timedelta(hours=4)
    QUALITY_GATE = timedelta(minutes=30)
    CONTINUOUS_QUALITY = timedelta(days=365)  # Long-running


# Activity timeout configurations
class ActivityTimeouts:
    """Default timeout configurations for activities"""

    # Agent activities
    CREATE_DESIGN = timedelta(minutes=10)
    CREATE_ISSUES = timedelta(minutes=5)
    GENERATE_CODE = timedelta(minutes=15)
    REVIEW_CODE = timedelta(minutes=10)
    DIAGNOSE_ISSUE = timedelta(minutes=10)
    ANALYZE_CODEBASE = timedelta(minutes=15)
    CREATE_MIGRATION_PLAN = timedelta(minutes=10)

    # GitHub activities
    GITHUB_API = timedelta(minutes=3)
    CREATE_PR = timedelta(minutes=3)
    MERGE_PR = timedelta(minutes=2)

    # Tool activities
    RUN_TESTS = timedelta(minutes=10)
    RUN_LINTERS = timedelta(minutes=5)
    RUN_SECURITY_SCAN = timedelta(minutes=5)
    RUN_PERFORMANCE_TESTS = timedelta(minutes=10)


# Activity heartbeat configurations
class ActivityHeartbeats:
    """Heartbeat timeout configurations for long-running activities"""

    GENERATE_CODE = timedelta(minutes=2)
    ANALYZE_CODEBASE = timedelta(minutes=3)
    DIAGNOSE_ISSUE = timedelta(minutes=2)
    MIGRATION_STEP = timedelta(minutes=2)


# Retry policy configurations
class RetryPolicies:
    """Common retry policies for activities"""

    @staticmethod
    def default() -> workflow.RetryPolicy:
        """Default retry policy"""
        return workflow.RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
        )

    @staticmethod
    def aggressive() -> workflow.RetryPolicy:
        """Aggressive retry policy for critical operations"""
        return workflow.RetryPolicy(
            maximum_attempts=5,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
        )

    @staticmethod
    def no_retry() -> workflow.RetryPolicy:
        """No retry policy for non-idempotent operations"""
        return workflow.RetryPolicy(
            maximum_attempts=1,
        )

    @staticmethod
    def github_api() -> workflow.RetryPolicy:
        """Retry policy for GitHub API calls"""
        return workflow.RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=20),
            backoff_coefficient=2.0,
        )


# Quality gate thresholds
class QualityThresholds:
    """Quality gate threshold configurations"""

    # Coverage thresholds
    MIN_COVERAGE = 80.0
    IDEAL_COVERAGE = 90.0

    # Quality score thresholds
    MIN_QUALITY_SCORE = 85.0
    IDEAL_QUALITY_SCORE = 95.0

    # Performance thresholds
    MIN_PERFORMANCE_SCORE = 80.0
    MAX_RESPONSE_TIME_P95 = 500  # milliseconds

    # Security thresholds
    MAX_CRITICAL_VULNERABILITIES = 0
    MAX_HIGH_VULNERABILITIES = 2


# Incident response configuration
class IncidentConfig:
    """Incident response workflow configuration"""

    # Number of diagnostic agents to run in parallel
    DEFAULT_DIAGNOSTIC_AGENTS = 3
    MAX_DIAGNOSTIC_AGENTS = 5

    # Confidence threshold for auto-fix
    AUTO_FIX_CONFIDENCE_THRESHOLD = 0.70

    # Severity levels
    SEVERITY_CRITICAL = "critical"
    SEVERITY_HIGH = "high"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_LOW = "low"


# Migration configuration
class MigrationConfig:
    """Code migration workflow configuration"""

    # Execution modes
    MODE_INCREMENTAL = "incremental"
    MODE_BATCH = "batch"

    # Risk levels
    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"

    # Auto-rollback settings
    AUTO_ROLLBACK_ENABLED = True


# Worker configuration
class WorkerConfig:
    """Worker configuration"""

    # Concurrency settings
    MAX_CONCURRENT_ACTIVITIES = 10
    MAX_CONCURRENT_WORKFLOW_TASKS = 10

    # Worker count for multi-worker setup
    DEFAULT_WORKER_COUNT = 3
    MAX_WORKER_COUNT = 10


# Feature flags
class FeatureFlags:
    """Feature flags for enabling/disabling capabilities"""

    # Auto-merge in Plan-Patch-PR
    ENABLE_AUTO_MERGE = False

    # Auto-fix in incident response
    ENABLE_AUTO_FIX = True

    # Auto-fix in quality gate
    ENABLE_QUALITY_AUTO_FIX = True

    # Auto-rollback in migration
    ENABLE_AUTO_ROLLBACK = True

    # Continuous workflows
    ENABLE_CONTINUOUS_MONITORING = False
    ENABLE_CONTINUOUS_QUALITY = False


def get_workflow_config(workflow_type: str) -> Dict[str, Any]:
    """
    Get configuration for a specific workflow type

    Args:
        workflow_type: Type of workflow

    Returns:
        Configuration dictionary
    """
    configs = {
        "plan_patch_pr": {
            "timeout": WorkflowTimeouts.PLAN_PATCH_PR,
            "retry_policy": RetryPolicies.default(),
            "auto_merge": FeatureFlags.ENABLE_AUTO_MERGE,
        },
        "incremental_patch": {
            "timeout": WorkflowTimeouts.INCREMENTAL_PATCH,
            "retry_policy": RetryPolicies.default(),
        },
        "incident_swarm": {
            "timeout": WorkflowTimeouts.INCIDENT_SWARM,
            "retry_policy": RetryPolicies.aggressive(),
            "num_agents": IncidentConfig.DEFAULT_DIAGNOSTIC_AGENTS,
            "auto_fix": FeatureFlags.ENABLE_AUTO_FIX,
            "confidence_threshold": IncidentConfig.AUTO_FIX_CONFIDENCE_THRESHOLD,
        },
        "code_migration": {
            "timeout": WorkflowTimeouts.CODE_MIGRATION,
            "retry_policy": RetryPolicies.default(),
            "auto_rollback": FeatureFlags.ENABLE_AUTO_ROLLBACK,
        },
        "quality_gate": {
            "timeout": WorkflowTimeouts.QUALITY_GATE,
            "retry_policy": RetryPolicies.default(),
            "auto_fix": FeatureFlags.ENABLE_QUALITY_AUTO_FIX,
            "min_coverage": QualityThresholds.MIN_COVERAGE,
            "min_score": QualityThresholds.MIN_QUALITY_SCORE,
        },
    }

    return configs.get(workflow_type, {})


def get_activity_config(activity_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific activity

    Args:
        activity_name: Name of activity

    Returns:
        Configuration dictionary
    """
    configs = {
        "create_design": {
            "timeout": ActivityTimeouts.CREATE_DESIGN,
            "retry_policy": RetryPolicies.default(),
        },
        "generate_code": {
            "timeout": ActivityTimeouts.GENERATE_CODE,
            "heartbeat_timeout": ActivityHeartbeats.GENERATE_CODE,
            "retry_policy": RetryPolicies.default(),
        },
        "run_tests": {
            "timeout": ActivityTimeouts.RUN_TESTS,
            "retry_policy": RetryPolicies.default(),
        },
        "create_pull_request": {
            "timeout": ActivityTimeouts.CREATE_PR,
            "retry_policy": RetryPolicies.github_api(),
        },
    }

    return configs.get(activity_name, {
        "timeout": timedelta(minutes=5),
        "retry_policy": RetryPolicies.default(),
    })
