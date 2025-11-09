"""
Pytest configuration and fixtures for Workflow tests
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker


@pytest.fixture
def mock_agent_activities():
    """Mock agent activities"""
    return {
        "create_design": AsyncMock(return_value={
            "architecture": "Test architecture",
            "components": ["component1", "component2"],
            "dependencies": [],
            "file_structure": {},
            "test_strategy": "Unit tests"
        }),
        "create_issues": AsyncMock(return_value=[
            {
                "id": "issue-1",
                "title": "Test Issue",
                "description": "Test description",
                "component": "test",
                "files_to_modify": [],
                "dependencies": [],
                "estimated_complexity": 3
            }
        ]),
        "generate_code": AsyncMock(return_value={
            "issue_id": "issue-1",
            "files": {"test.py": "def test(): pass"},
            "tests": {"test_test.py": "def test_test(): pass"},
            "description": "Generated code"
        }),
        "review_code": AsyncMock(return_value={
            "approved": True,
            "comments": [],
            "suggestions": []
        })
    }


@pytest.fixture
def mock_github_activities():
    """Mock GitHub activities"""
    return {
        "create_branch": AsyncMock(return_value="feature/test-branch"),
        "create_pull_request": AsyncMock(return_value={
            "number": 123,
            "url": "https://github.com/test/repo/pull/123",
            "branch_name": "feature/test-branch"
        }),
        "merge_pull_request": AsyncMock(return_value={
            "merged": True,
            "merge_commit_sha": "abc123"
        })
    }


@pytest.fixture
def mock_tool_activities():
    """Mock tool activities"""
    return {
        "run_tests": AsyncMock(return_value={
            "passed": True,
            "coverage": 0.85,
            "output": "All tests passed"
        }),
        "run_linters": AsyncMock(return_value={
            "passed": True,
            "issues": []
        }),
        "run_security_scan": AsyncMock(return_value={
            "passed": True,
            "issues": []
        })
    }


@pytest.fixture
async def workflow_environment():
    """Create Temporal workflow test environment"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env
    # Cleanup handled by context manager


@pytest.fixture
def sample_workflow_input():
    """Sample workflow input"""
    return {
        "requirement": "Add user authentication",
        "repository": "test/repo",
        "base_branch": "main",
        "auto_merge": False
    }

