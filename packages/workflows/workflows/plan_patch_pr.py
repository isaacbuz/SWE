"""
Main development workflow: Plan -> Patch -> PR

This workflow orchestrates the entire development cycle from a user requirement
to a merged pull request, coordinating multiple agents and quality gates.
"""

from datetime import timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from temporalio import workflow, activity
import asyncio

from ..activities.agent_activities import (
    create_design,
    create_issues,
    generate_code,
    review_code,
)
from ..activities.github_activities import (
    create_pull_request,
    merge_pull_request,
    create_branch,
)
from ..activities.tool_activities import (
    run_tests,
    run_linters,
    run_security_scan,
)


@dataclass
class PRResult:
    """Result of the Plan-Patch-PR workflow"""
    pr_number: int
    pr_url: str
    branch_name: str
    files_changed: List[str]
    test_results: Dict[str, Any]
    qa_score: float
    merged: bool
    merge_commit_sha: Optional[str] = None


@dataclass
class Design:
    """Design document from Chief Architect"""
    architecture: str
    components: List[str]
    dependencies: List[str]
    file_structure: Dict[str, str]
    test_strategy: str


@dataclass
class Issue:
    """Development issue/task"""
    id: str
    title: str
    description: str
    component: str
    files_to_modify: List[str]
    dependencies: List[str]
    estimated_complexity: int


@dataclass
class Patch:
    """Code patch for an issue"""
    issue_id: str
    files: Dict[str, str]  # filename -> content
    tests: Dict[str, str]
    description: str


@dataclass
class QAResult:
    """Quality assurance results"""
    tests_passed: bool
    coverage: float
    linting_passed: bool
    security_issues: List[str]
    performance_score: float
    auto_fixed: bool
    patches: List[Patch]


@workflow.defn
class PlanPatchPRWorkflow:
    """
    Main development workflow that coordinates:
    1. Chief Architect creates design
    2. Planner breaks down into issues
    3. Parallel code generation
    4. Quality gates
    5. PR creation and merge
    """

    def __init__(self):
        self.design: Optional[Design] = None
        self.issues: List[Issue] = []
        self.patches: List[Patch] = []
        self.qa_result: Optional[QAResult] = None
        self.pr_result: Optional[PRResult] = None

    @workflow.run
    async def run(self, requirement: str, auto_merge: bool = False) -> PRResult:
        """
        Execute the full Plan-Patch-PR workflow

        Args:
            requirement: User requirement/feature request
            auto_merge: Whether to auto-merge if all checks pass

        Returns:
            PRResult with details of the created PR
        """
        workflow.logger.info(f"Starting Plan-Patch-PR workflow for: {requirement[:100]}")

        # Step 1: Chief Architect creates design
        workflow.logger.info("Step 1: Creating design with Chief Architect")
        self.design = await workflow.execute_activity(
            create_design,
            args=[requirement],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        # Step 2: Planner creates issues
        workflow.logger.info(f"Step 2: Breaking down design into issues")
        self.issues = await workflow.execute_activity(
            create_issues,
            args=[self.design],
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.logger.info(f"Created {len(self.issues)} issues to implement")

        # Step 3: Create feature branch
        branch_name = f"feature/{requirement[:30].replace(' ', '-').lower()}"
        await workflow.execute_activity(
            create_branch,
            args=[branch_name],
            start_to_close_timeout=timedelta(minutes=1),
        )

        # Step 4: Parallel code generation for each issue
        workflow.logger.info("Step 3: Generating code for all issues in parallel")
        self.patches = await asyncio.gather(*[
            workflow.execute_activity(
                generate_code,
                args=[issue],
                start_to_close_timeout=timedelta(minutes=15),
                heartbeat_timeout=timedelta(minutes=2),
            )
            for issue in self.issues
        ])

        workflow.logger.info(f"Generated {len(self.patches)} patches")

        # Step 5: Quality gates (tests, linting, security)
        workflow.logger.info("Step 4: Running quality gates")
        self.qa_result = await self._run_quality_gates(self.patches)

        # Step 6: If QA failed, attempt automated fixes
        if not self.qa_result.tests_passed or not self.qa_result.linting_passed:
            workflow.logger.info("QA issues detected, attempting auto-fix")
            self.qa_result = await self._attempt_auto_fix(self.qa_result)

        # Step 7: Create pull request
        workflow.logger.info("Step 5: Creating pull request")
        self.pr_result = await workflow.execute_activity(
            create_pull_request,
            args=[{
                'branch': branch_name,
                'title': requirement,
                'design': self.design,
                'patches': self.patches,
                'qa_result': self.qa_result,
            }],
            start_to_close_timeout=timedelta(minutes=3),
        )

        # Step 8: Auto-merge if requested and all checks pass
        if auto_merge and self._should_auto_merge():
            workflow.logger.info("Auto-merging PR (all checks passed)")
            merge_result = await workflow.execute_activity(
                merge_pull_request,
                args=[self.pr_result.pr_number],
                start_to_close_timeout=timedelta(minutes=2),
            )
            self.pr_result.merged = True
            self.pr_result.merge_commit_sha = merge_result['sha']

        workflow.logger.info(f"Workflow completed: {self.pr_result.pr_url}")
        return self.pr_result

    async def _run_quality_gates(self, patches: List[Patch]) -> QAResult:
        """Run all quality gates in parallel"""

        # Run tests, linting, and security scan concurrently
        test_result, lint_result, security_result = await asyncio.gather(
            workflow.execute_activity(
                run_tests,
                args=[patches],
                start_to_close_timeout=timedelta(minutes=10),
            ),
            workflow.execute_activity(
                run_linters,
                args=[patches],
                start_to_close_timeout=timedelta(minutes=5),
            ),
            workflow.execute_activity(
                run_security_scan,
                args=[patches],
                start_to_close_timeout=timedelta(minutes=5),
            ),
        )

        return QAResult(
            tests_passed=test_result['passed'],
            coverage=test_result['coverage'],
            linting_passed=lint_result['passed'],
            security_issues=security_result['issues'],
            performance_score=test_result.get('performance_score', 100.0),
            auto_fixed=False,
            patches=patches,
        )

    async def _attempt_auto_fix(self, qa_result: QAResult) -> QAResult:
        """Attempt to automatically fix QA issues"""

        fixed_patches = await workflow.execute_activity(
            review_code,
            args=[qa_result.patches, qa_result],
            start_to_close_timeout=timedelta(minutes=10),
        )

        # Re-run quality gates on fixed code
        new_qa_result = await self._run_quality_gates(fixed_patches)
        new_qa_result.auto_fixed = True

        return new_qa_result

    def _should_auto_merge(self) -> bool:
        """Determine if PR should be auto-merged"""
        if not self.qa_result:
            return False

        return (
            self.qa_result.tests_passed
            and self.qa_result.linting_passed
            and len(self.qa_result.security_issues) == 0
            and self.qa_result.coverage >= 80.0
            and self.qa_result.performance_score >= 80.0
        )

    @workflow.signal
    async def cancel_workflow(self):
        """Signal to cancel the workflow"""
        workflow.logger.info("Workflow cancellation requested")
        raise workflow.CancelledError("Workflow cancelled by user")

    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query current workflow status"""
        return {
            'has_design': self.design is not None,
            'issues_count': len(self.issues),
            'patches_count': len(self.patches),
            'qa_completed': self.qa_result is not None,
            'pr_created': self.pr_result is not None,
            'pr_url': self.pr_result.pr_url if self.pr_result else None,
        }


@workflow.defn
class IncrementalPatchWorkflow:
    """
    Simpler workflow for incremental patches (bug fixes, small features)
    Skips architecture design and goes straight to code generation
    """

    @workflow.run
    async def run(self, description: str, files_to_modify: List[str]) -> PRResult:
        """
        Execute incremental patch workflow

        Args:
            description: Description of the change
            files_to_modify: List of files to modify

        Returns:
            PRResult with details of the created PR
        """
        workflow.logger.info(f"Starting incremental patch: {description}")

        # Create single issue
        issue = Issue(
            id="patch-1",
            title=description,
            description=description,
            component="patch",
            files_to_modify=files_to_modify,
            dependencies=[],
            estimated_complexity=1,
        )

        # Generate code
        patch = await workflow.execute_activity(
            generate_code,
            args=[issue],
            start_to_close_timeout=timedelta(minutes=10),
        )

        # Run quality gates
        test_result = await workflow.execute_activity(
            run_tests,
            args=[[patch]],
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Create PR
        branch_name = f"patch/{description[:30].replace(' ', '-').lower()}"
        await workflow.execute_activity(
            create_branch,
            args=[branch_name],
            start_to_close_timeout=timedelta(minutes=1),
        )

        pr_result = await workflow.execute_activity(
            create_pull_request,
            args=[{
                'branch': branch_name,
                'title': description,
                'patches': [patch],
                'test_result': test_result,
            }],
            start_to_close_timeout=timedelta(minutes=2),
        )

        return pr_result
