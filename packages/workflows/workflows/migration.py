"""
Code migration workflow

Orchestrates large-scale code migrations with incremental steps,
validation at each stage, and rollback capability.
"""

from datetime import timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from temporalio import workflow
import asyncio

from ..activities.agent_activities import (
    analyze_codebase,
    create_migration_plan,
    generate_migration_step,
    validate_migration_step,
)
from ..activities.github_activities import (
    create_pull_request,
    create_branch,
)
from ..activities.tool_activities import (
    run_tests,
    run_linters,
)


@dataclass
class MigrationStep:
    """Single step in migration process"""
    id: str
    description: str
    files_to_change: List[str]
    changes: Dict[str, str]  # file -> new content
    dependencies: List[str]  # IDs of steps that must complete first
    validation_criteria: Dict[str, Any]
    rollback_changes: Dict[str, str]  # for reverting


@dataclass
class MigrationPlan:
    """Complete migration plan"""
    name: str
    description: str
    source_pattern: str  # e.g., "React 16" or "Python 2.7"
    target_pattern: str  # e.g., "React 18" or "Python 3.11"
    steps: List[MigrationStep]
    estimated_duration_hours: float
    risk_level: str  # low, medium, high


@dataclass
class StepResult:
    """Result of executing a migration step"""
    step_id: str
    success: bool
    files_changed: List[str]
    tests_passed: bool
    validation_passed: bool
    errors: List[str]
    rollback_available: bool


@dataclass
class MigrationResult:
    """Final migration result"""
    plan_name: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    step_results: List[StepResult]
    final_pr_url: Optional[str]
    rollback_performed: bool
    duration_minutes: float


@workflow.defn
class CodeMigrationWorkflow:
    """
    Orchestrates large-scale code migrations:
    1. Analyze codebase
    2. Generate migration plan
    3. Execute steps incrementally
    4. Validate at each stage
    5. Rollback on failure if needed
    6. Create PR with all changes
    """

    def __init__(self):
        self.plan: Optional[MigrationPlan] = None
        self.step_results: List[StepResult] = []
        self.rollback_performed = False
        self.current_step: Optional[str] = None

    @workflow.run
    async def run(
        self,
        migration_type: str,  # e.g., "react-upgrade", "python3-migration"
        source_version: str,
        target_version: str,
        incremental: bool = True,
        auto_rollback: bool = True,
    ) -> MigrationResult:
        """
        Execute code migration workflow

        Args:
            migration_type: Type of migration to perform
            source_version: Current version/pattern
            target_version: Target version/pattern
            incremental: Execute steps incrementally with validation
            auto_rollback: Automatically rollback on failure

        Returns:
            MigrationResult with detailed outcome
        """
        start_time = workflow.now()
        workflow.logger.info(
            f"Starting {migration_type} migration: {source_version} -> {target_version}"
        )

        # Step 1: Analyze codebase
        workflow.logger.info("Step 1: Analyzing codebase")
        analysis = await workflow.execute_activity(
            analyze_codebase,
            args=[migration_type, source_version],
            start_to_close_timeout=timedelta(minutes=15),
            heartbeat_timeout=timedelta(minutes=3),
        )

        workflow.logger.info(
            f"Analysis complete: {analysis['files_affected']} files affected"
        )

        # Step 2: Generate migration plan
        workflow.logger.info("Step 2: Generating migration plan")
        self.plan = await workflow.execute_activity(
            create_migration_plan,
            args=[analysis, source_version, target_version],
            start_to_close_timeout=timedelta(minutes=10),
        )

        workflow.logger.info(
            f"Migration plan created with {len(self.plan.steps)} steps"
        )

        # Step 3: Create migration branch
        branch_name = f"migration/{migration_type}-{target_version}"
        await workflow.execute_activity(
            create_branch,
            args=[branch_name],
            start_to_close_timeout=timedelta(minutes=1),
        )

        # Step 4: Execute migration steps
        if incremental:
            success = await self._execute_incremental_migration(auto_rollback)
        else:
            success = await self._execute_batch_migration()

        # Step 5: Create PR if successful
        pr_url = None
        if success:
            workflow.logger.info("Migration successful, creating PR")
            pr_result = await workflow.execute_activity(
                create_pull_request,
                args=[{
                    'branch': branch_name,
                    'title': f"[MIGRATION] {migration_type}: {source_version} -> {target_version}",
                    'description': self._generate_pr_description(),
                    'labels': ['migration', 'automated'],
                }],
                start_to_close_timeout=timedelta(minutes=3),
            )
            pr_url = pr_result.pr_url
        else:
            workflow.logger.warning("Migration failed or rolled back")

        duration = (workflow.now() - start_time).total_seconds() / 60

        result = MigrationResult(
            plan_name=self.plan.name,
            total_steps=len(self.plan.steps),
            completed_steps=sum(1 for r in self.step_results if r.success),
            failed_steps=sum(1 for r in self.step_results if not r.success),
            step_results=self.step_results,
            final_pr_url=pr_url,
            rollback_performed=self.rollback_performed,
            duration_minutes=duration,
        )

        workflow.logger.info(
            f"Migration completed in {duration:.1f} minutes. "
            f"{result.completed_steps}/{result.total_steps} steps successful"
        )

        return result

    async def _execute_incremental_migration(self, auto_rollback: bool) -> bool:
        """Execute migration steps incrementally with validation"""

        # Build dependency graph
        step_map = {step.id: step for step in self.plan.steps}
        completed = set()

        while len(completed) < len(self.plan.steps):
            # Find steps ready to execute (dependencies satisfied)
            ready_steps = [
                step for step in self.plan.steps
                if step.id not in completed
                and all(dep in completed for dep in step.dependencies)
            ]

            if not ready_steps:
                workflow.logger.error("No ready steps but migration incomplete (circular dependency?)")
                return False

            # Execute ready steps in parallel
            results = await asyncio.gather(*[
                self._execute_step(step)
                for step in ready_steps
            ])

            # Check results
            for step, result in zip(ready_steps, results):
                self.step_results.append(result)

                if result.success:
                    completed.add(step.id)
                    workflow.logger.info(f"Step {step.id} completed successfully")
                else:
                    workflow.logger.error(f"Step {step.id} failed: {result.errors}")

                    if auto_rollback:
                        await self._rollback_migration()
                        return False
                    else:
                        # Continue with remaining steps even if one fails
                        completed.add(step.id)

        return True

    async def _execute_batch_migration(self) -> bool:
        """Execute all migration steps in parallel (faster but riskier)"""

        workflow.logger.info("Executing batch migration (all steps in parallel)")

        results = await asyncio.gather(*[
            self._execute_step(step)
            for step in self.plan.steps
        ])

        self.step_results = results

        # Check if all succeeded
        return all(r.success for r in results)

    async def _execute_step(self, step: MigrationStep) -> StepResult:
        """Execute a single migration step with validation"""

        self.current_step = step.id
        workflow.logger.info(f"Executing step: {step.description}")

        try:
            # Generate the actual code changes
            changes = await workflow.execute_activity(
                generate_migration_step,
                args=[step],
                start_to_close_timeout=timedelta(minutes=10),
                heartbeat_timeout=timedelta(minutes=2),
            )

            # Run tests on the changes
            test_result = await workflow.execute_activity(
                run_tests,
                args=[changes],
                start_to_close_timeout=timedelta(minutes=10),
            )

            # Validate migration-specific criteria
            validation_result = await workflow.execute_activity(
                validate_migration_step,
                args=[step, changes],
                start_to_close_timeout=timedelta(minutes=5),
            )

            success = test_result['passed'] and validation_result['passed']

            return StepResult(
                step_id=step.id,
                success=success,
                files_changed=list(changes.keys()),
                tests_passed=test_result['passed'],
                validation_passed=validation_result['passed'],
                errors=test_result.get('errors', []) + validation_result.get('errors', []),
                rollback_available=True,
            )

        except Exception as e:
            workflow.logger.error(f"Step {step.id} failed with exception: {e}")
            return StepResult(
                step_id=step.id,
                success=False,
                files_changed=[],
                tests_passed=False,
                validation_passed=False,
                errors=[str(e)],
                rollback_available=True,
            )

    async def _rollback_migration(self):
        """Rollback all completed migration steps"""

        workflow.logger.info("Starting migration rollback")
        self.rollback_performed = True

        # Rollback in reverse order
        for result in reversed(self.step_results):
            if result.success and result.rollback_available:
                step = next(s for s in self.plan.steps if s.id == result.step_id)

                workflow.logger.info(f"Rolling back step: {step.id}")

                # Apply rollback changes
                # In production, this would revert the files
                await asyncio.sleep(1)  # Placeholder

        workflow.logger.info("Rollback completed")

    def _generate_pr_description(self) -> str:
        """Generate detailed PR description"""

        successful = [r for r in self.step_results if r.success]
        failed = [r for r in self.step_results if not r.success]

        description = f"""
# Migration: {self.plan.name}

{self.plan.description}

**Source:** {self.plan.source_pattern}
**Target:** {self.plan.target_pattern}

## Summary

- Total Steps: {len(self.plan.steps)}
- Successful: {len(successful)}
- Failed: {len(failed)}
- Risk Level: {self.plan.risk_level}

## Completed Steps

"""
        for result in successful:
            step = next(s for s in self.plan.steps if s.id == result.step_id)
            description += f"- [{result.step_id}] {step.description}\n"

        if failed:
            description += "\n## Failed Steps\n\n"
            for result in failed:
                step = next(s for s in self.plan.steps if s.id == result.step_id)
                description += f"- [{result.step_id}] {step.description}\n"
                description += f"  Errors: {', '.join(result.errors)}\n"

        return description

    @workflow.signal
    async def pause_migration(self):
        """Pause the migration after current step"""
        workflow.logger.info("Migration pause requested")
        # In production, set a flag to pause after current step

    @workflow.signal
    async def resume_migration(self):
        """Resume a paused migration"""
        workflow.logger.info("Migration resume requested")
        # In production, clear the pause flag

    @workflow.query
    def get_progress(self) -> Dict[str, Any]:
        """Get current migration progress"""
        return {
            'total_steps': len(self.plan.steps) if self.plan else 0,
            'completed_steps': len([r for r in self.step_results if r.success]),
            'failed_steps': len([r for r in self.step_results if not r.success]),
            'current_step': self.current_step,
            'rollback_performed': self.rollback_performed,
        }
