"""
Unit tests for Workflow Activities
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from packages.workflows.activities.agent_activities import (
    create_design,
    create_issues,
    generate_code,
    review_code
)
from packages.workflows.activities.github_activities import (
    create_branch,
    create_pull_request,
    merge_pull_request
)
from packages.workflows.activities.tool_activities import (
    run_tests,
    run_linters,
    run_security_scan
)


class TestAgentActivities:
    """Test agent activities"""

    @pytest.mark.asyncio
    async def test_create_design(self):
        """Test design creation activity"""
        # Mock agent execution
        with patch('packages.workflows.activities.agent_activities.execute_agent') as mock_execute:
            mock_execute.return_value = {
                "architecture": "Test architecture",
                "components": ["component1"],
                "dependencies": [],
                "file_structure": {},
                "test_strategy": "Unit tests"
            }
            
            result = await create_design(
                requirement="Add authentication",
                context={}
            )
            
            assert result is not None
            assert "architecture" in result

    @pytest.mark.asyncio
    async def test_create_issues(self):
        """Test issue creation activity"""
        with patch('packages.workflows.activities.agent_activities.execute_agent') as mock_execute:
            mock_execute.return_value = [
                {
                    "id": "issue-1",
                    "title": "Test Issue",
                    "description": "Test",
                    "component": "test",
                    "files_to_modify": [],
                    "dependencies": [],
                    "estimated_complexity": 3
                }
            ]
            
            result = await create_issues(
                design={"components": ["test"]},
                context={}
            )
            
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_code(self):
        """Test code generation activity"""
        with patch('packages.workflows.activities.agent_activities.execute_agent') as mock_execute:
            mock_execute.return_value = {
                "issue_id": "issue-1",
                "files": {"test.py": "code"},
                "tests": {},
                "description": "Generated"
            }
            
            result = await generate_code(
                issue={"id": "issue-1"},
                context={}
            )
            
            assert result is not None
            assert "files" in result

    @pytest.mark.asyncio
    async def test_review_code(self):
        """Test code review activity"""
        with patch('packages.workflows.activities.agent_activities.execute_agent') as mock_execute:
            mock_execute.return_value = {
                "approved": True,
                "comments": [],
                "suggestions": []
            }
            
            result = await review_code(
                code={"files": {"test.py": "code"}},
                context={}
            )
            
            assert result is not None
            assert "approved" in result


class TestGitHubActivities:
    """Test GitHub activities"""

    @pytest.mark.asyncio
    async def test_create_branch(self):
        """Test branch creation activity"""
        with patch('packages.workflows.activities.github_activities.github_client') as mock_client:
            mock_client.create_branch = AsyncMock(return_value="feature/test-branch")
            
            result = await create_branch(
                repository="test/repo",
                branch_name="feature/test",
                base_branch="main"
            )
            
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_create_pull_request(self):
        """Test PR creation activity"""
        with patch('packages.workflows.activities.github_activities.github_client') as mock_client:
            mock_client.create_pull_request = AsyncMock(return_value={
                "number": 123,
                "url": "https://github.com/test/repo/pull/123",
                "branch_name": "feature/test"
            })
            
            result = await create_pull_request(
                repository="test/repo",
                title="Test PR",
                body="Test body",
                branch_name="feature/test",
                base_branch="main"
            )
            
            assert result is not None
            assert "number" in result or "pr_number" in result

    @pytest.mark.asyncio
    async def test_merge_pull_request(self):
        """Test PR merge activity"""
        with patch('packages.workflows.activities.github_activities.github_client') as mock_client:
            mock_client.merge_pull_request = AsyncMock(return_value={
                "merged": True,
                "merge_commit_sha": "abc123"
            })
            
            result = await merge_pull_request(
                repository="test/repo",
                pr_number=123
            )
            
            assert result is not None
            assert "merged" in result or result.get("merged") == True


class TestToolActivities:
    """Test tool activities"""

    @pytest.mark.asyncio
    async def test_run_tests(self):
        """Test test execution activity"""
        with patch('packages.workflows.activities.tool_activities.run_test_command') as mock_run:
            mock_run.return_value = {
                "passed": True,
                "coverage": 0.85,
                "output": "All tests passed"
            }
            
            result = await run_tests(
                repository="test/repo",
                branch="feature/test"
            )
            
            assert result is not None
            assert "passed" in result or result.get("passed") == True

    @pytest.mark.asyncio
    async def test_run_linters(self):
        """Test linter execution activity"""
        with patch('packages.workflows.activities.tool_activities.run_linter_command') as mock_run:
            mock_run.return_value = {
                "passed": True,
                "issues": []
            }
            
            result = await run_linters(
                repository="test/repo",
                branch="feature/test"
            )
            
            assert result is not None
            assert "passed" in result or result.get("passed") == True

    @pytest.mark.asyncio
    async def test_run_security_scan(self):
        """Test security scan activity"""
        with patch('packages.workflows.activities.tool_activities.run_security_scan_command') as mock_run:
            mock_run.return_value = {
                "passed": True,
                "issues": []
            }
            
            result = await run_security_scan(
                repository="test/repo",
                branch="feature/test"
            )
            
            assert result is not None
            assert "passed" in result or result.get("passed") == True

