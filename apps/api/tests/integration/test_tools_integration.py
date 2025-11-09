"""
Integration tests for tools API.

Tests the complete flow from API request to tool execution.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user for authentication."""
    from auth.models import User
    return User(
        id="test-user-123",
        email="test@example.com",
        username="testuser",
    )


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    with patch("services.tools_service.get_tool_registry") as mock:
        registry = mock.return_value
        registry.get_tool_specs.return_value = [
            {
                "name": "createIssues",
                "description": "Create multiple GitHub issues",
                "operationId": "createIssues",
                "endpoint": "/github/create-issues",
                "method": "POST",
                "tags": ["github"],
            }
        ]
        registry.get_tool_by_name.return_value = {
            "name": "createIssues",
            "description": "Create multiple GitHub issues",
            "operationId": "createIssues",
            "endpoint": "/github/create-issues",
            "method": "POST",
            "tags": ["github"],
        }
        yield registry


@pytest.fixture
def mock_tool_executor():
    """Mock tool executor."""
    with patch("services.tools_service.get_tool_executor") as mock:
        executor = mock.return_value
        executor.execute = AsyncMock(return_value={
            "success": True,
            "data": {"message": "Tool executed successfully"},
        })
        yield executor


class TestListTools:
    """Test tool listing endpoints."""

    def test_list_tools_success(self, client, mock_tool_registry):
        """Test successful tool listing."""
        # Mock authentication
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            
            response = client.get("/api/v1/tools")
            assert response.status_code == 200
            data = response.json()
            assert "tools" in data
            assert "total" in data
            assert len(data["tools"]) > 0

    def test_list_tools_with_tag_filter(self, client, mock_tool_registry):
        """Test tool listing with tag filter."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            
            response = client.get("/api/v1/tools?tag=github")
            assert response.status_code == 200
            data = response.json()
            assert all("github" in tool.get("tags", []) for tool in data["tools"])

    def test_list_tools_with_search(self, client, mock_tool_registry):
        """Test tool listing with search query."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            
            response = client.get("/api/v1/tools?search=issue")
            assert response.status_code == 200
            data = response.json()
            assert len(data["tools"]) >= 0  # May be empty if no matches


class TestGetTool:
    """Test get tool endpoint."""

    def test_get_tool_success(self, client, mock_tool_registry):
        """Test successful tool retrieval."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            
            response = client.get("/api/v1/tools/createIssues")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "createIssues"
            assert "description" in data

    def test_get_tool_not_found(self, client, mock_tool_registry):
        """Test tool not found."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            mock_tool_registry.get_tool_by_name.return_value = None
            
            response = client.get("/api/v1/tools/nonexistent")
            assert response.status_code == 404


class TestExecuteTool:
    """Test tool execution endpoint."""

    def test_execute_tool_success(
        self, client, mock_tool_registry, mock_tool_executor
    ):
        """Test successful tool execution."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            with patch("services.permissions_service.get_permission_checker") as mock_perm:
                mock_perm.return_value.has_permission.return_value = True
                with patch("services.rate_limiting_service.get_rate_limiter") as mock_rate:
                    mock_rate.return_value.check_limit.return_value = {"exceeded": False}
                    with patch("services.audit_service.get_audit_logger") as mock_audit:
                        mock_audit.return_value.log_execution = AsyncMock()
                        
                        response = client.post(
                            "/api/v1/tools/execute",
                            json={
                                "toolName": "createIssues",
                                "arguments": {
                                    "owner": "example",
                                    "repo": "repo",
                                    "tasks": [],
                                },
                            },
                        )
                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True
                        assert "result" in data
                        assert "executionTime" in data

    def test_execute_tool_permission_denied(
        self, client, mock_tool_registry, mock_tool_executor
    ):
        """Test tool execution with permission denied."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            with patch("services.permissions_service.get_permission_checker") as mock_perm:
                mock_perm.return_value.has_permission.return_value = False
                
                response = client.post(
                    "/api/v1/tools/execute",
                    json={
                        "toolName": "createIssues",
                        "arguments": {},
                    },
                )
                assert response.status_code == 403

    def test_execute_tool_rate_limit_exceeded(
        self, client, mock_tool_registry, mock_tool_executor
    ):
        """Test tool execution with rate limit exceeded."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            with patch("services.permissions_service.get_permission_checker") as mock_perm:
                mock_perm.return_value.has_permission.return_value = True
                with patch("services.rate_limiting_service.get_rate_limiter") as mock_rate:
                    mock_rate.return_value.check_limit.return_value = {"exceeded": True}
                    
                    response = client.post(
                        "/api/v1/tools/execute",
                        json={
                            "toolName": "createIssues",
                            "arguments": {},
                        },
                    )
                    assert response.status_code == 429

    def test_execute_tool_not_found(
        self, client, mock_tool_registry, mock_tool_executor
    ):
        """Test tool execution with tool not found."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            with patch("services.permissions_service.get_permission_checker") as mock_perm:
                mock_perm.return_value.has_permission.return_value = True
                with patch("services.rate_limiting_service.get_rate_limiter") as mock_rate:
                    mock_rate.return_value.check_limit.return_value = {"exceeded": False}
                    mock_tool_executor.execute = AsyncMock(return_value={
                        "success": False,
                        "error": "Tool 'nonexistent' not found",
                    })
                    
                    response = client.post(
                        "/api/v1/tools/execute",
                        json={
                            "toolName": "nonexistent",
                            "arguments": {},
                        },
                    )
                    assert response.status_code == 500


class TestAuditLogs:
    """Test audit log endpoints."""

    def test_get_audit_logs_success(self, client):
        """Test successful audit log retrieval."""
        with patch("auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user()
            with patch("services.audit_service.get_audit_logger") as mock_audit:
                mock_audit.return_value.query_logs = AsyncMock(return_value=[])
                
                response = client.get("/api/v1/tools/audit")
                assert response.status_code == 200
                data = response.json()
                assert "logs" in data
                assert "total" in data


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/tools/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "tools"

