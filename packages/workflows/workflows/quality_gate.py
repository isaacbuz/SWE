"""
Quality gate workflow for pre-merge checks

Runs comprehensive quality checks on PRs and can automatically
fix issues or block merge if critical failures occur.
"""

from datetime import timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from temporalio import workflow
import asyncio

from ..activities.tool_activities import (
    run_tests,
    run_linters,
    run_security_scan,
    run_performance_tests,
    check_code_coverage,
    check_dependencies,
    run_static_analysis,
)
from ..activities.agent_activities import (
    review_code,
    fix_linting_issues,
    improve_coverage,
)
from ..activities.github_activities import (
    update_pr_status,
    add_pr_comment,
)


@dataclass
class QualityCheck:
    """Individual quality check result"""
    name: str
    passed: bool
    required: bool  # Whether this check is required for merge
    score: float  # 0-100
    issues: List[str]
    auto_fixable: bool
    details: Dict[str, Any]


@dataclass
class QualityGateResult:
    """Overall quality gate result"""
    pr_number: int
    all_checks_passed: bool
    required_checks_passed: bool
    can_merge: bool
    checks: List[QualityCheck]
    overall_score: float
    auto_fixes_applied: bool
    blocking_issues: List[str]


@workflow.defn
class QualityGateWorkflow:
    """
    Quality gate workflow that:
    1. Runs all quality checks in parallel
    2. Identifies auto-fixable issues
    3. Attempts automated fixes
    4. Re-runs checks after fixes
    5. Updates PR status
    6. Blocks merge if critical failures
    """

    def __init__(self):
        self.checks: List[QualityCheck] = []
        self.auto_fixes_applied = False

    @workflow.run
    async def run(
        self,
        pr_number: int,
        branch: str,
        attempt_auto_fix: bool = True,
        required_coverage: float = 80.0,
        required_score: float = 85.0,
    ) -> QualityGateResult:
        """
        Execute quality gate checks

        Args:
            pr_number: Pull request number
            branch: Branch to check
            attempt_auto_fix: Whether to attempt automated fixes
            required_coverage: Minimum required code coverage (%)
            required_score: Minimum required overall quality score

        Returns:
            QualityGateResult with all check results
        """
        workflow.logger.info(f"Starting quality gate for PR #{pr_number}")

        # Update PR status to "checking"
        await workflow.execute_activity(
            update_pr_status,
            args=[pr_number, 'pending', 'Quality checks in progress'],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 1: Run all quality checks in parallel
        workflow.logger.info("Step 1: Running quality checks in parallel")
        self.checks = await self._run_all_checks(branch, required_coverage)

        # Step 2: Attempt auto-fixes if enabled and needed
        if attempt_auto_fix and self._has_auto_fixable_issues():
            workflow.logger.info("Step 2: Attempting automated fixes")
            await self._apply_auto_fixes(branch)

            # Re-run checks after fixes
            workflow.logger.info("Re-running checks after auto-fixes")
            self.checks = await self._run_all_checks(branch, required_coverage)

        # Step 3: Calculate overall results
        result = self._calculate_results(pr_number, required_score)

        # Step 4: Update PR status
        await self._update_pr_status(pr_number, result)

        workflow.logger.info(
            f"Quality gate completed: {'PASSED' if result.can_merge else 'FAILED'} "
            f"(score: {result.overall_score:.1f})"
        )

        return result

    async def _run_all_checks(
        self,
        branch: str,
        required_coverage: float,
    ) -> List[QualityCheck]:
        """Run all quality checks in parallel"""

        # Execute all checks concurrently
        results = await asyncio.gather(
            # Unit tests
            workflow.execute_activity(
                run_tests,
                args=[branch, 'unit'],
                start_to_close_timeout=timedelta(minutes=10),
            ),
            # Integration tests
            workflow.execute_activity(
                run_tests,
                args=[branch, 'integration'],
                start_to_close_timeout=timedelta(minutes=15),
            ),
            # Linting
            workflow.execute_activity(
                run_linters,
                args=[branch],
                start_to_close_timeout=timedelta(minutes=5),
            ),
            # Security scan
            workflow.execute_activity(
                run_security_scan,
                args=[branch],
                start_to_close_timeout=timedelta(minutes=5),
            ),
            # Code coverage
            workflow.execute_activity(
                check_code_coverage,
                args=[branch],
                start_to_close_timeout=timedelta(minutes=5),
            ),
            # Performance tests
            workflow.execute_activity(
                run_performance_tests,
                args=[branch],
                start_to_close_timeout=timedelta(minutes=10),
            ),
            # Dependency check
            workflow.execute_activity(
                check_dependencies,
                args=[branch],
                start_to_close_timeout=timedelta(minutes=3),
            ),
            # Static analysis
            workflow.execute_activity(
                run_static_analysis,
                args=[branch],
                start_to_close_timeout=timedelta(minutes=5),
            ),
        )

        (
            unit_tests,
            integration_tests,
            linting,
            security,
            coverage,
            performance,
            dependencies,
            static_analysis,
        ) = results

        # Convert results to QualityCheck objects
        checks = [
            QualityCheck(
                name='Unit Tests',
                passed=unit_tests['passed'],
                required=True,
                score=100.0 if unit_tests['passed'] else 0.0,
                issues=unit_tests.get('failures', []),
                auto_fixable=False,
                details=unit_tests,
            ),
            QualityCheck(
                name='Integration Tests',
                passed=integration_tests['passed'],
                required=True,
                score=100.0 if integration_tests['passed'] else 0.0,
                issues=integration_tests.get('failures', []),
                auto_fixable=False,
                details=integration_tests,
            ),
            QualityCheck(
                name='Linting',
                passed=linting['passed'],
                required=False,
                score=linting['score'],
                issues=linting.get('issues', []),
                auto_fixable=linting.get('auto_fixable', True),
                details=linting,
            ),
            QualityCheck(
                name='Security Scan',
                passed=len(security['issues']) == 0,
                required=security.get('has_critical', False),
                score=100.0 - (len(security['issues']) * 10),
                issues=security['issues'],
                auto_fixable=security.get('auto_fixable', False),
                details=security,
            ),
            QualityCheck(
                name='Code Coverage',
                passed=coverage['percentage'] >= required_coverage,
                required=True,
                score=coverage['percentage'],
                issues=[f"Coverage {coverage['percentage']:.1f}% < required {required_coverage}%"]
                if coverage['percentage'] < required_coverage else [],
                auto_fixable=True,
                details=coverage,
            ),
            QualityCheck(
                name='Performance Tests',
                passed=performance['passed'],
                required=False,
                score=performance['score'],
                issues=performance.get('regressions', []),
                auto_fixable=False,
                details=performance,
            ),
            QualityCheck(
                name='Dependencies',
                passed=len(dependencies['vulnerabilities']) == 0,
                required=dependencies.get('has_critical', False),
                score=100.0 - (len(dependencies['vulnerabilities']) * 5),
                issues=dependencies['vulnerabilities'],
                auto_fixable=False,
                details=dependencies,
            ),
            QualityCheck(
                name='Static Analysis',
                passed=static_analysis['passed'],
                required=False,
                score=static_analysis['score'],
                issues=static_analysis.get('issues', []),
                auto_fixable=static_analysis.get('auto_fixable', True),
                details=static_analysis,
            ),
        ]

        return checks

    def _has_auto_fixable_issues(self) -> bool:
        """Check if there are any auto-fixable issues"""
        return any(
            not check.passed and check.auto_fixable
            for check in self.checks
        )

    async def _apply_auto_fixes(self, branch: str):
        """Apply automated fixes for fixable issues"""

        fix_tasks = []

        for check in self.checks:
            if not check.passed and check.auto_fixable:
                if check.name == 'Linting':
                    fix_tasks.append(
                        workflow.execute_activity(
                            fix_linting_issues,
                            args=[branch, check.issues],
                            start_to_close_timeout=timedelta(minutes=5),
                        )
                    )
                elif check.name == 'Code Coverage':
                    fix_tasks.append(
                        workflow.execute_activity(
                            improve_coverage,
                            args=[branch, check.details],
                            start_to_close_timeout=timedelta(minutes=10),
                        )
                    )
                elif check.name == 'Static Analysis':
                    fix_tasks.append(
                        workflow.execute_activity(
                            review_code,
                            args=[branch, check.issues],
                            start_to_close_timeout=timedelta(minutes=10),
                        )
                    )

        if fix_tasks:
            await asyncio.gather(*fix_tasks)
            self.auto_fixes_applied = True

    def _calculate_results(
        self,
        pr_number: int,
        required_score: float,
    ) -> QualityGateResult:
        """Calculate overall quality gate results"""

        all_passed = all(check.passed for check in self.checks)
        required_passed = all(
            check.passed for check in self.checks if check.required
        )

        # Calculate weighted overall score
        total_weight = len(self.checks)
        overall_score = sum(check.score for check in self.checks) / total_weight

        # Collect blocking issues
        blocking_issues = []
        for check in self.checks:
            if check.required and not check.passed:
                blocking_issues.extend(
                    f"[{check.name}] {issue}" for issue in check.issues
                )

        # Can merge if required checks pass and score is high enough
        can_merge = required_passed and overall_score >= required_score

        return QualityGateResult(
            pr_number=pr_number,
            all_checks_passed=all_passed,
            required_checks_passed=required_passed,
            can_merge=can_merge,
            checks=self.checks,
            overall_score=overall_score,
            auto_fixes_applied=self.auto_fixes_applied,
            blocking_issues=blocking_issues,
        )

    async def _update_pr_status(self, pr_number: int, result: QualityGateResult):
        """Update PR with quality gate results"""

        # Update status check
        status = 'success' if result.can_merge else 'failure'
        description = (
            f"Quality score: {result.overall_score:.1f}% - "
            f"{len([c for c in result.checks if c.passed])}/{len(result.checks)} checks passed"
        )

        await workflow.execute_activity(
            update_pr_status,
            args=[pr_number, status, description],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Add detailed comment
        comment = self._generate_comment(result)
        await workflow.execute_activity(
            add_pr_comment,
            args=[pr_number, comment],
            start_to_close_timeout=timedelta(seconds=30),
        )

    def _generate_comment(self, result: QualityGateResult) -> str:
        """Generate detailed PR comment with results"""

        comment = f"""## Quality Gate Results

**Overall Score:** {result.overall_score:.1f}%
**Status:** {'✅ PASSED' if result.can_merge else '❌ FAILED'}
{'**Auto-fixes applied:** Yes' if result.auto_fixes_applied else ''}

### Checks

| Check | Status | Score | Issues |
|-------|--------|-------|--------|
"""

        for check in result.checks:
            status_icon = '✅' if check.passed else '❌'
            required_text = ' (required)' if check.required else ''
            issues_count = len(check.issues)

            comment += f"| {check.name}{required_text} | {status_icon} | {check.score:.1f}% | {issues_count} |\n"

        if result.blocking_issues:
            comment += "\n### Blocking Issues\n\n"
            for issue in result.blocking_issues:
                comment += f"- {issue}\n"

        if result.can_merge:
            comment += "\n✅ **This PR meets all quality requirements and can be merged.**\n"
        else:
            comment += "\n❌ **This PR does not meet quality requirements. Please address the issues above.**\n"

        return comment

    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Get current quality gate status"""
        return {
            'checks_count': len(self.checks),
            'passed_checks': len([c for c in self.checks if c.passed]),
            'auto_fixes_applied': self.auto_fixes_applied,
        }


@workflow.defn
class ContinuousQualityWorkflow:
    """
    Long-running workflow that monitors PRs and automatically
    runs quality gates on new commits
    """

    @workflow.run
    async def run(self, repository: str):
        """
        Monitor repository and run quality gates on PRs

        Args:
            repository: Repository name to monitor
        """
        workflow.logger.info(f"Starting continuous quality monitoring for {repository}")

        while True:
            await asyncio.sleep(60)  # Check every minute

            # In production, fetch open PRs from GitHub
            # For each PR with new commits, spawn QualityGateWorkflow

            # Placeholder for demonstration
            await asyncio.sleep(1)
