"""
Integration utilities for quality assurance tools

Provides wrappers and integrations for:
- Testing frameworks (pytest, jest, vitest)
- Security tools (bandit, semgrep, snyk)
- Code coverage tools
- Linting and formatting tools
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TestFrameworkIntegration:
    """Integration with testing frameworks"""

    @staticmethod
    async def run_pytest(
        test_paths: List[str],
        coverage: bool = True,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Run pytest tests

        Args:
            test_paths: Paths to test files/directories
            coverage: Enable coverage collection
            verbose: Verbose output

        Returns:
            Test results and coverage data
        """
        logger.info(f"Running pytest on {len(test_paths)} paths")

        cmd = ["pytest"]

        if coverage:
            cmd.extend(["--cov", "--cov-report=json"])

        if verbose:
            cmd.append("-v")

        cmd.extend(test_paths)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            # Parse pytest output
            test_results = {
                'exit_code': result.returncode,
                'stdout': stdout.decode(),
                'stderr': stderr.decode(),
                'success': result.returncode == 0,
            }

            # Parse coverage if enabled
            if coverage and Path('.coverage').exists():
                coverage_data = TestFrameworkIntegration._parse_coverage()
                test_results['coverage'] = coverage_data

            return test_results

        except Exception as e:
            logger.error(f"Error running pytest: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def run_jest(
        test_paths: List[str],
        coverage: bool = True,
    ) -> Dict[str, Any]:
        """
        Run Jest tests

        Args:
            test_paths: Paths to test files
            coverage: Enable coverage

        Returns:
            Test results
        """
        logger.info(f"Running jest on {len(test_paths)} paths")

        cmd = ["jest"]

        if coverage:
            cmd.append("--coverage")

        cmd.append("--json")
        cmd.extend(test_paths)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            # Parse JSON output
            test_results = json.loads(stdout.decode())
            test_results['success'] = result.returncode == 0

            return test_results

        except Exception as e:
            logger.error(f"Error running jest: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _parse_coverage() -> Dict[str, Any]:
        """Parse coverage.py output"""
        try:
            with open('coverage.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error parsing coverage: {e}")
            return {}


class SecurityToolIntegration:
    """Integration with security scanning tools"""

    @staticmethod
    async def run_bandit(
        paths: List[str],
        severity_level: str = "medium",
    ) -> Dict[str, Any]:
        """
        Run Bandit security scanner (Python)

        Args:
            paths: Paths to scan
            severity_level: Minimum severity (low, medium, high)

        Returns:
            Security findings
        """
        logger.info(f"Running Bandit on {len(paths)} paths")

        cmd = [
            "bandit",
            "-r",
            "-f", "json",
            "-ll",  # Only medium and high severity
            *paths,
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            # Parse JSON output
            findings = json.loads(stdout.decode())

            return {
                'success': True,
                'findings': findings.get('results', []),
                'metrics': findings.get('metrics', {}),
            }

        except Exception as e:
            logger.error(f"Error running Bandit: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def run_semgrep(
        paths: List[str],
        config: str = "auto",
    ) -> Dict[str, Any]:
        """
        Run Semgrep security scanner

        Args:
            paths: Paths to scan
            config: Semgrep config (auto, p/security-audit, etc.)

        Returns:
            Security findings
        """
        logger.info(f"Running Semgrep on {len(paths)} paths")

        cmd = [
            "semgrep",
            "--config", config,
            "--json",
            *paths,
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            findings = json.loads(stdout.decode())

            return {
                'success': True,
                'findings': findings.get('results', []),
                'errors': findings.get('errors', []),
            }

        except Exception as e:
            logger.error(f"Error running Semgrep: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def run_snyk(
        package_file: str = "package.json",
    ) -> Dict[str, Any]:
        """
        Run Snyk dependency scanner

        Args:
            package_file: Package file to scan

        Returns:
            Vulnerability findings
        """
        logger.info(f"Running Snyk on {package_file}")

        cmd = [
            "snyk", "test",
            "--json",
            f"--file={package_file}",
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            vulnerabilities = json.loads(stdout.decode())

            return {
                'success': True,
                'vulnerabilities': vulnerabilities.get('vulnerabilities', []),
                'summary': vulnerabilities.get('summary', {}),
            }

        except Exception as e:
            logger.error(f"Error running Snyk: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def run_npm_audit() -> Dict[str, Any]:
        """
        Run npm audit for Node.js projects

        Returns:
            Audit results
        """
        logger.info("Running npm audit")

        cmd = ["npm", "audit", "--json"]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            audit_results = json.loads(stdout.decode())

            return {
                'success': True,
                'vulnerabilities': audit_results.get('vulnerabilities', {}),
                'metadata': audit_results.get('metadata', {}),
            }

        except Exception as e:
            logger.error(f"Error running npm audit: {e}")
            return {'success': False, 'error': str(e)}


class LintingIntegration:
    """Integration with linting and formatting tools"""

    @staticmethod
    async def run_eslint(
        paths: List[str],
        fix: bool = False,
    ) -> Dict[str, Any]:
        """
        Run ESLint

        Args:
            paths: Paths to lint
            fix: Automatically fix issues

        Returns:
            Linting results
        """
        logger.info(f"Running ESLint on {len(paths)} paths")

        cmd = ["eslint", "--format", "json"]

        if fix:
            cmd.append("--fix")

        cmd.extend(paths)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            lint_results = json.loads(stdout.decode())

            return {
                'success': result.returncode == 0,
                'results': lint_results,
            }

        except Exception as e:
            logger.error(f"Error running ESLint: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def run_pylint(
        paths: List[str],
    ) -> Dict[str, Any]:
        """
        Run Pylint

        Args:
            paths: Paths to lint

        Returns:
            Linting results
        """
        logger.info(f"Running Pylint on {len(paths)} paths")

        cmd = [
            "pylint",
            "--output-format=json",
            *paths,
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            lint_results = json.loads(stdout.decode())

            return {
                'success': result.returncode == 0,
                'messages': lint_results,
            }

        except Exception as e:
            logger.error(f"Error running Pylint: {e}")
            return {'success': False, 'error': str(e)}


class CIIntegration:
    """Integration with CI/CD systems"""

    @staticmethod
    async def run_github_action(
        workflow_file: str,
        inputs: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Trigger GitHub Action workflow

        Args:
            workflow_file: Workflow file name
            inputs: Workflow inputs

        Returns:
            Workflow run information
        """
        logger.info(f"Triggering GitHub Action: {workflow_file}")

        cmd = [
            "gh", "workflow", "run",
            workflow_file,
        ]

        if inputs:
            for key, value in inputs.items():
                cmd.extend(["-f", f"{key}={value}"])

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            return {
                'success': result.returncode == 0,
                'output': stdout.decode(),
            }

        except Exception as e:
            logger.error(f"Error triggering GitHub Action: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def get_workflow_status(
        run_id: str,
    ) -> Dict[str, Any]:
        """
        Get GitHub Action workflow status

        Args:
            run_id: Workflow run ID

        Returns:
            Workflow status
        """
        cmd = [
            "gh", "run", "view",
            run_id,
            "--json", "status,conclusion",
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            status = json.loads(stdout.decode())

            return {
                'success': True,
                'status': status.get('status'),
                'conclusion': status.get('conclusion'),
            }

        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {'success': False, 'error': str(e)}


class PerformanceToolIntegration:
    """Integration with performance testing tools"""

    @staticmethod
    async def run_locust(
        locustfile: str,
        host: str,
        users: int = 10,
        spawn_rate: int = 1,
        run_time: str = "1m",
    ) -> Dict[str, Any]:
        """
        Run Locust load test

        Args:
            locustfile: Path to locustfile
            host: Target host
            users: Number of users
            spawn_rate: Users spawned per second
            run_time: Test duration

        Returns:
            Load test results
        """
        logger.info(f"Running Locust load test: {users} users for {run_time}")

        cmd = [
            "locust",
            "-f", locustfile,
            "--headless",
            "--host", host,
            "-u", str(users),
            "-r", str(spawn_rate),
            "--run-time", run_time,
            "--json",
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            # Parse results
            return {
                'success': result.returncode == 0,
                'output': stdout.decode(),
            }

        except Exception as e:
            logger.error(f"Error running Locust: {e}")
            return {'success': False, 'error': str(e)}


# Convenience functions

async def run_security_scan(
    paths: List[str],
    tools: List[str] = ['bandit', 'semgrep'],
) -> Dict[str, Any]:
    """
    Run multiple security tools

    Args:
        paths: Paths to scan
        tools: Tools to run

    Returns:
        Aggregated results
    """
    results = {}

    if 'bandit' in tools:
        results['bandit'] = await SecurityToolIntegration.run_bandit(paths)

    if 'semgrep' in tools:
        results['semgrep'] = await SecurityToolIntegration.run_semgrep(paths)

    if 'snyk' in tools:
        results['snyk'] = await SecurityToolIntegration.run_snyk()

    return results


async def run_all_tests(
    test_paths: List[str],
    framework: str = 'pytest',
) -> Dict[str, Any]:
    """
    Run tests with specified framework

    Args:
        test_paths: Test paths
        framework: Testing framework

    Returns:
        Test results
    """
    if framework == 'pytest':
        return await TestFrameworkIntegration.run_pytest(test_paths)
    elif framework == 'jest':
        return await TestFrameworkIntegration.run_jest(test_paths)
    else:
        raise ValueError(f"Unsupported framework: {framework}")
