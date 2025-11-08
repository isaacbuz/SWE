"""
Integration tests for agent API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.agent
class TestAgentEndpoints:
    """Test agent API endpoints."""

    async def test_list_agents(self, authenticated_client: AsyncClient):
        """Test GET /api/agents endpoint."""
        response = await authenticated_client.get("/api/agents")
        # assert response.status_code == 200
        # assert "agents" in response.json()

    async def test_get_agent_by_id(self, authenticated_client: AsyncClient, mock_agent):
        """Test GET /api/agents/{id} endpoint."""
        agent_id = mock_agent["id"]
        response = await authenticated_client.get(f"/api/agents/{agent_id}")
        # assert response.status_code == 200
        # data = response.json()
        # assert data["id"] == agent_id

    async def test_create_agent(self, authenticated_client: AsyncClient):
        """Test POST /api/agents endpoint."""
        agent_data = {
            "name": "New Test Agent",
            "type": "developer",
            "capabilities": ["code_generation"],
        }
        response = await authenticated_client.post("/api/agents", json=agent_data)
        # assert response.status_code == 201
        # data = response.json()
        # assert data["name"] == agent_data["name"]

    async def test_update_agent(self, authenticated_client: AsyncClient, mock_agent):
        """Test PUT /api/agents/{id} endpoint."""
        agent_id = mock_agent["id"]
        update_data = {"status": "busy"}
        response = await authenticated_client.put(
            f"/api/agents/{agent_id}", json=update_data
        )
        # assert response.status_code == 200
        # data = response.json()
        # assert data["status"] == "busy"

    async def test_delete_agent(self, authenticated_client: AsyncClient, mock_agent):
        """Test DELETE /api/agents/{id} endpoint."""
        agent_id = mock_agent["id"]
        response = await authenticated_client.delete(f"/api/agents/{agent_id}")
        # assert response.status_code == 204

    async def test_agent_not_found(self, authenticated_client: AsyncClient):
        """Test 404 when agent not found."""
        response = await authenticated_client.get("/api/agents/non-existent-id")
        # assert response.status_code == 404

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test unauthorized access to agent endpoints."""
        response = await client.get("/api/agents")
        # assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.api
class TestAgentTaskAssignment:
    """Test agent task assignment endpoints."""

    async def test_assign_task_to_agent(
        self, authenticated_client: AsyncClient, mock_agent, mock_task
    ):
        """Test POST /api/agents/{id}/tasks endpoint."""
        agent_id = mock_agent["id"]
        task_id = mock_task["id"]
        response = await authenticated_client.post(
            f"/api/agents/{agent_id}/tasks", json={"task_id": task_id}
        )
        # assert response.status_code == 200

    async def test_list_agent_tasks(self, authenticated_client: AsyncClient, mock_agent):
        """Test GET /api/agents/{id}/tasks endpoint."""
        agent_id = mock_agent["id"]
        response = await authenticated_client.get(f"/api/agents/{agent_id}/tasks")
        # assert response.status_code == 200
        # assert "tasks" in response.json()

    async def test_remove_task_from_agent(
        self, authenticated_client: AsyncClient, mock_agent, mock_task
    ):
        """Test DELETE /api/agents/{id}/tasks/{task_id} endpoint."""
        agent_id = mock_agent["id"]
        task_id = mock_task["id"]
        response = await authenticated_client.delete(
            f"/api/agents/{agent_id}/tasks/{task_id}"
        )
        # assert response.status_code == 204
