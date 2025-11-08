"""
Migration Planner Agent

Plans and executes large-scale code migrations (frameworks, languages, architectures).
Analyzes dependencies, creates incremental migration plans, validates compatibility,
and tracks progress.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base import BaseAgent, Task, Context, AgentResult, TaskType, Priority
from protocol import Evidence


class MigrationType(str, Enum):
    """Migration types"""
    FRAMEWORK = "framework"
    LANGUAGE = "language"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    LIBRARY = "library"


class MigrationPhase(str, Enum):
    """Migration phases"""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    VALIDATION = "validation"
    ROLLBACK = "rollback"
    COMPLETED = "completed"


@dataclass
class MigrationTarget:
    """Target state for migration"""
    from_technology: str
    to_technology: str
    from_version: Optional[str] = None
    to_version: Optional[str] = None
    migration_type: MigrationType = MigrationType.FRAMEWORK


@dataclass
class MigrationStep:
    """Individual migration step"""
    id: str
    phase: MigrationPhase
    description: str
    dependencies: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    validation_criteria: List[str] = field(default_factory=list)
    rollback_procedure: Optional[str] = None
    automated: bool = False
    status: str = "pending"  # pending, in_progress, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationPlan:
    """Complete migration plan"""
    plan_id: str
    target: MigrationTarget
    steps: List[MigrationStep]
    total_estimated_hours: float
    risks: List[str]
    prerequisites: List[str]
    success_criteria: List[str]
    rollback_strategy: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_phase: MigrationPhase = MigrationPhase.PLANNING
    metadata: Dict[str, Any] = field(default_factory=dict)


class MigrationPlanner(BaseAgent):
    """
    Migration Planner for large-scale code migrations

    Features:
    - Dependency analysis
    - Incremental migration planning
    - Risk assessment
    - Compatibility validation
    - Automated migration steps
    - Rollback strategies
    - Progress tracking
    """

    def __init__(
        self,
        agent_id: str = "migration_planner",
        max_parallel_steps: int = 3,
        require_rollback_plan: bool = True,
        **kwargs
    ):
        """
        Initialize migration planner

        Args:
            agent_id: Agent identifier
            max_parallel_steps: Maximum parallel migration steps
            require_rollback_plan: Require rollback plan for each step
            **kwargs: Additional BaseAgent arguments
        """
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.MIGRATION,
            **kwargs
        )

        self.max_parallel_steps = max_parallel_steps
        self.require_rollback_plan = require_rollback_plan

        # Active migrations
        self.active_migrations: Dict[str, MigrationPlan] = {}
        self.completed_migrations: Dict[str, MigrationPlan] = {}

        self.logger = logging.getLogger(f"Agent.{agent_id}")

    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return """You are a Migration Planner agent responsible for planning and
executing large-scale code migrations.

Your responsibilities:
1. Analyze current codebase and dependencies
2. Assess migration complexity and risks
3. Create incremental migration plans
4. Define validation criteria
5. Plan rollback strategies
6. Identify automation opportunities
7. Track migration progress

When planning migrations:
- Break down into small, incremental steps
- Minimize risk and downtime
- Ensure each step is reversible
- Validate at each stage
- Consider backwards compatibility
- Plan for testing at each step

Provide migration plan in JSON format:
{
  "migration_steps": [
    {
      "phase": "preparation|execution|validation",
      "description": "step description",
      "dependencies": ["step_id1"],
      "affected_files": ["file1", "file2"],
      "estimated_hours": 4.0,
      "validation_criteria": ["criteria 1"],
      "rollback_procedure": "rollback steps",
      "automated": true|false
    }
  ],
  "total_estimated_hours": 40.0,
  "risks": ["risk 1", "risk 2"],
  "prerequisites": ["prereq 1"],
  "success_criteria": ["criteria 1"],
  "rollback_strategy": "overall rollback approach"
}"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute migration planning or execution

        Args:
            task: Task specifying migration target
            context: Execution context

        Returns:
            Migration plan or execution results
        """
        try:
            # Parse migration target from task
            target = self._parse_migration_target(task)

            if not target:
                return AgentResult(
                    success=False,
                    output={},
                    evidence=[],
                    error="Failed to parse migration target"
                )

            # Check if this is planning or execution
            action = task.input_data.get("action", "plan")

            if action == "plan":
                return await self._create_migration_plan(target, task, context)
            elif action == "execute":
                plan_id = task.input_data.get("plan_id")
                if not plan_id or plan_id not in self.active_migrations:
                    return AgentResult(
                        success=False,
                        output={},
                        evidence=[],
                        error="Invalid or missing plan_id"
                    )
                return await self._execute_migration(plan_id, context)
            else:
                return AgentResult(
                    success=False,
                    output={},
                    evidence=[],
                    error=f"Unknown action: {action}"
                )

        except Exception as e:
            self.logger.error(f"Migration operation failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    def _parse_migration_target(self, task: Task) -> Optional[MigrationTarget]:
        """Parse migration target from task"""
        try:
            target_data = task.input_data.get("target", {})

            return MigrationTarget(
                from_technology=target_data["from_technology"],
                to_technology=target_data["to_technology"],
                from_version=target_data.get("from_version"),
                to_version=target_data.get("to_version"),
                migration_type=MigrationType(target_data.get("type", "framework"))
            )
        except Exception as e:
            self.logger.error(f"Failed to parse migration target: {e}")
            return None

    async def _create_migration_plan(
        self,
        target: MigrationTarget,
        task: Task,
        context: Context
    ) -> AgentResult:
        """
        Create migration plan

        Args:
            target: Migration target
            task: Task
            context: Execution context

        Returns:
            Migration plan
        """
        self.logger.info(
            f"Creating migration plan: {target.from_technology} -> {target.to_technology}"
        )

        # Step 1: Analyze current codebase
        analysis = await self._analyze_codebase(target, context)

        # Step 2: Assess compatibility
        compatibility = await self._assess_compatibility(target, analysis, context)

        # Step 3: Identify dependencies
        dependencies = await self._analyze_dependencies(target, context)

        # Step 4: Generate migration steps
        steps = await self._generate_migration_steps(
            target,
            analysis,
            compatibility,
            dependencies,
            task,
            context
        )

        # Step 5: Assess risks
        risks = await self._assess_risks(target, steps, context)

        # Step 6: Create rollback strategy
        rollback_strategy = await self._create_rollback_strategy(target, steps, context)

        # Create plan
        plan = MigrationPlan(
            plan_id=f"migration_{target.migration_type.value}_{datetime.utcnow().timestamp()}",
            target=target,
            steps=steps,
            total_estimated_hours=sum(step.estimated_hours for step in steps),
            risks=risks,
            prerequisites=analysis.get("prerequisites", []),
            success_criteria=self._define_success_criteria(target),
            rollback_strategy=rollback_strategy
        )

        # Store plan
        self.active_migrations[plan.plan_id] = plan

        evidence = [
            self.create_evidence(
                "migration_plan",
                f"Created migration plan with {len(steps)} steps"
            )
        ]

        return AgentResult(
            success=True,
            output={
                "plan_id": plan.plan_id,
                "target": {
                    "from": target.from_technology,
                    "to": target.to_technology,
                    "type": target.migration_type.value
                },
                "steps": [self._step_to_dict(step) for step in steps],
                "total_estimated_hours": plan.total_estimated_hours,
                "risks": plan.risks,
                "prerequisites": plan.prerequisites,
                "success_criteria": plan.success_criteria,
                "rollback_strategy": plan.rollback_strategy,
                "analysis": analysis,
                "compatibility": compatibility
            },
            evidence=evidence,
            metadata={
                "migration_type": target.migration_type.value,
                "total_steps": len(steps)
            }
        )

    async def _analyze_codebase(
        self,
        target: MigrationTarget,
        context: Context
    ) -> Dict[str, Any]:
        """Analyze current codebase"""
        # Simplified analysis - in production, would do deep code analysis

        analysis = {
            "total_files": 0,
            "affected_files": [],
            "dependencies": [],
            "prerequisites": [
                f"Backup current codebase",
                f"Set up {target.to_technology} development environment",
                "Create test suite for validation"
            ],
            "estimated_complexity": "medium"
        }

        # TODO: Implement actual codebase analysis
        # - Count files using target technology
        # - Analyze import statements
        # - Check configuration files
        # - Identify custom implementations

        return analysis

    async def _assess_compatibility(
        self,
        target: MigrationTarget,
        analysis: Dict[str, Any],
        context: Context
    ) -> Dict[str, Any]:
        """Assess compatibility between technologies"""
        # TODO: Implement compatibility assessment
        # - Check breaking changes
        # - Identify deprecated features
        # - Find alternative APIs
        # - Assess data migration needs

        return {
            "compatibility_score": 0.8,
            "breaking_changes": [],
            "deprecated_features": [],
            "recommended_alternatives": {},
            "data_migration_required": False
        }

    async def _analyze_dependencies(
        self,
        target: MigrationTarget,
        context: Context
    ) -> Dict[str, Any]:
        """Analyze dependencies"""
        # TODO: Implement dependency analysis
        # - Parse package.json, requirements.txt, etc.
        # - Identify version conflicts
        # - Check for available alternatives

        return {
            "current_dependencies": [],
            "new_dependencies": [],
            "conflicts": [],
            "alternatives": {}
        }

    async def _generate_migration_steps(
        self,
        target: MigrationTarget,
        analysis: Dict[str, Any],
        compatibility: Dict[str, Any],
        dependencies: Dict[str, Any],
        task: Task,
        context: Context
    ) -> List[MigrationStep]:
        """Generate migration steps using LLM"""
        prompt = f"""Create a detailed migration plan for the following:

Migration: {target.from_technology} -> {target.to_technology}
Type: {target.migration_type.value}
From Version: {target.from_version or 'N/A'}
To Version: {target.to_version or 'N/A'}

Codebase Analysis:
{analysis}

Compatibility Assessment:
{compatibility}

Dependencies:
{dependencies}

Create an incremental migration plan with specific steps.
Each step should be:
- Small and focused
- Independently testable
- Reversible
- Well-documented

Break the migration into these phases:
1. Preparation (setup, dependencies)
2. Execution (actual code changes)
3. Validation (testing, verification)"""

        try:
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_json=True,
                max_tokens=4096
            )

            import json
            plan_data = json.loads(response["content"])

            steps = []
            for i, step_data in enumerate(plan_data.get("migration_steps", [])):
                step = MigrationStep(
                    id=f"step_{i}",
                    phase=MigrationPhase(step_data.get("phase", "execution")),
                    description=step_data["description"],
                    dependencies=step_data.get("dependencies", []),
                    affected_files=step_data.get("affected_files", []),
                    estimated_hours=step_data.get("estimated_hours", 2.0),
                    validation_criteria=step_data.get("validation_criteria", []),
                    rollback_procedure=step_data.get("rollback_procedure"),
                    automated=step_data.get("automated", False)
                )
                steps.append(step)

            return steps

        except Exception as e:
            self.logger.error(f"Failed to generate migration steps: {e}")
            # Return basic steps as fallback
            return self._get_fallback_steps(target)

    def _get_fallback_steps(self, target: MigrationTarget) -> List[MigrationStep]:
        """Get fallback migration steps"""
        return [
            MigrationStep(
                id="step_0",
                phase=MigrationPhase.PREPARATION,
                description=f"Set up {target.to_technology} environment",
                estimated_hours=2.0,
                validation_criteria=["Environment configured"],
                automated=False
            ),
            MigrationStep(
                id="step_1",
                phase=MigrationPhase.EXECUTION,
                description=f"Migrate core functionality to {target.to_technology}",
                dependencies=["step_0"],
                estimated_hours=16.0,
                validation_criteria=["Core tests passing"],
                automated=False
            ),
            MigrationStep(
                id="step_2",
                phase=MigrationPhase.VALIDATION,
                description="Run comprehensive test suite",
                dependencies=["step_1"],
                estimated_hours=4.0,
                validation_criteria=["All tests passing", "No regressions detected"],
                automated=True
            )
        ]

    async def _assess_risks(
        self,
        target: MigrationTarget,
        steps: List[MigrationStep],
        context: Context
    ) -> List[str]:
        """Assess migration risks"""
        risks = [
            "Breaking changes in production",
            "Data loss or corruption",
            "Performance degradation",
            "Third-party integration failures",
            "Incomplete rollback",
            "Extended downtime"
        ]

        # Add specific risks based on migration type
        if target.migration_type == MigrationType.DATABASE:
            risks.extend([
                "Data migration errors",
                "Schema compatibility issues",
                "Query performance changes"
            ])
        elif target.migration_type == MigrationType.FRAMEWORK:
            risks.extend([
                "API incompatibilities",
                "Deprecated feature usage",
                "Configuration mismatches"
            ])

        return risks

    async def _create_rollback_strategy(
        self,
        target: MigrationTarget,
        steps: List[MigrationStep],
        context: Context
    ) -> str:
        """Create rollback strategy"""
        return f"""Rollback Strategy for {target.from_technology} -> {target.to_technology}:

1. Maintain full backup of pre-migration state
2. Use version control tags for each migration step
3. Implement feature flags for gradual rollout
4. Monitor key metrics during migration
5. Define rollback triggers (error rates, performance degradation)
6. Test rollback procedure in staging environment
7. Keep rollback window within 24 hours
8. Document rollback procedures for each step

Emergency Rollback:
- Stop migration immediately
- Revert to previous version using backup
- Restore database from backup if needed
- Notify team and stakeholders
- Conduct post-mortem analysis"""

    def _define_success_criteria(self, target: MigrationTarget) -> List[str]:
        """Define success criteria"""
        return [
            "All automated tests passing",
            "No increase in error rates",
            "Performance metrics within acceptable range",
            f"All features working on {target.to_technology}",
            "Zero data loss",
            "Successful deployment to production",
            "Positive validation from stakeholders"
        ]

    async def _execute_migration(
        self,
        plan_id: str,
        context: Context
    ) -> AgentResult:
        """Execute migration plan"""
        plan = self.active_migrations.get(plan_id)
        if not plan:
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=f"Migration plan {plan_id} not found"
            )

        # TODO: Implement actual migration execution
        # This would orchestrate running each step
        # For now, return plan status

        return AgentResult(
            success=True,
            output={
                "plan_id": plan_id,
                "status": "ready_for_execution",
                "message": "Migration plan ready. Manual execution required."
            },
            evidence=[],
            metadata={"plan_id": plan_id}
        )

    def _step_to_dict(self, step: MigrationStep) -> Dict[str, Any]:
        """Convert migration step to dictionary"""
        return {
            "id": step.id,
            "phase": step.phase.value,
            "description": step.description,
            "dependencies": step.dependencies,
            "affected_files": step.affected_files,
            "estimated_hours": step.estimated_hours,
            "validation_criteria": step.validation_criteria,
            "rollback_procedure": step.rollback_procedure,
            "automated": step.automated,
            "status": step.status
        }
