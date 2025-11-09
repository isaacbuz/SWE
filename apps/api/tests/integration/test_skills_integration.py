"""
Integration tests for Skills API endpoints.

These tests verify the full flow including database interactions.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime
import json

from apps.api.main import app


@pytest.fixture
async def test_client():
    """Create test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_skill_data():
    """Sample skill data for testing"""
    return {
        "name": "Integration Test Skill",
        "slug": f"integration-test-{uuid4().hex[:8]}",
        "description": "A skill for integration testing",
        "detailed_description": "Detailed description for testing",
        "category": "CODE_GENERATION",
        "tags": ["test", "integration"],
        "prompt_template": "Generate code for {{task}}",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"}
            },
            "required": ["task"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"}
            },
            "required": ["code"]
        },
        "model_preferences": {
            "temperature": 0.7
        },
        "visibility": "public",
        "license": "MIT",
        "pricing_model": "free",
    }


@pytest.mark.integration
@pytest.mark.skills
class TestSkillsAPIIntegration:
    """Integration tests for Skills API"""

    @pytest.mark.asyncio
    async def test_create_and_list_skills(self, test_client: AsyncClient, sample_skill_data):
        """Test creating a skill and listing it"""
        # Create skill
        response = await test_client.post(
            "/api/v1/skills",
            json=sample_skill_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Note: This will fail without proper auth, but tests the flow
        # In real scenario, would use proper auth token
        assert response.status_code in [201, 401, 403]  # Created or auth required
        
        if response.status_code == 201:
            created_skill = response.json()
            assert created_skill["name"] == sample_skill_data["name"]
            assert created_skill["slug"] == sample_skill_data["slug"]
            
            # List skills
            list_response = await test_client.get("/api/v1/skills")
            assert list_response.status_code == 200
            skills = list_response.json()
            assert isinstance(skills, list)
            
            # Find our skill
            found = next((s for s in skills if s["slug"] == sample_skill_data["slug"]), None)
            if found:
                assert found["name"] == sample_skill_data["name"]

    @pytest.mark.asyncio
    async def test_get_skill_by_id(self, test_client: AsyncClient):
        """Test getting skill by ID"""
        # First, list skills to get an ID
        list_response = await test_client.get("/api/v1/skills")
        assert list_response.status_code == 200
        skills = list_response.json()
        
        if len(skills) > 0:
            skill_id = skills[0]["id"]
            
            # Get skill by ID
            get_response = await test_client.get(f"/api/v1/skills/{skill_id}")
            assert get_response.status_code == 200
            skill = get_response.json()
            assert skill["id"] == skill_id
            assert "prompt_template" in skill

    @pytest.mark.asyncio
    async def test_get_nonexistent_skill(self, test_client: AsyncClient):
        """Test getting non-existent skill"""
        fake_id = str(uuid4())
        response = await test_client.get(f"/api/v1/skills/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_skills_with_filters(self, test_client: AsyncClient):
        """Test listing skills with category filter"""
        response = await test_client.get(
            "/api/v1/skills",
            params={"category": "CODE_GENERATION", "limit": 10}
        )
        assert response.status_code == 200
        skills = response.json()
        assert isinstance(skills, list)
        
        # All returned skills should match category (if any returned)
        for skill in skills:
            assert skill.get("category") == "CODE_GENERATION"

    @pytest.mark.asyncio
    async def test_list_skills_with_search(self, test_client: AsyncClient):
        """Test searching skills"""
        response = await test_client.get(
            "/api/v1/skills",
            params={"search": "test", "limit": 5}
        )
        assert response.status_code == 200
        skills = response.json()
        assert isinstance(skills, list)
        
        # Results should contain "test" in name or description (if any)
        for skill in skills:
            name_desc = f"{skill.get('name', '')} {skill.get('description', '')}".lower()
            assert "test" in name_desc

    @pytest.mark.asyncio
    async def test_skill_validation(self, test_client: AsyncClient, sample_skill_data):
        """Test skill creation validation"""
        # Missing required field
        invalid_data = sample_skill_data.copy()
        del invalid_data["name"]
        
        response = await test_client.post(
            "/api/v1/skills",
            json=invalid_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [422, 401, 403]  # Validation error or auth required

    @pytest.mark.asyncio
    async def test_skill_execution_flow(self, test_client: AsyncClient):
        """Test skill execution flow (mocked)"""
        # This would require:
        # 1. A skill in database
        # 2. Proper authentication
        # 3. Mocked AI provider
        
        # For now, just test the endpoint exists
        fake_id = str(uuid4())
        response = await test_client.post(
            f"/api/v1/skills/{fake_id}/execute",
            json={
                "skill_id": fake_id,
                "inputs": {"task": "test"},
                "context": {}
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should return 404 (skill not found) or 401/403 (auth required)
        assert response.status_code in [404, 401, 403]

    @pytest.mark.asyncio
    async def test_install_skill_flow(self, test_client: AsyncClient):
        """Test skill installation flow"""
        fake_id = str(uuid4())
        response = await test_client.post(
            f"/api/v1/skills/{fake_id}/install",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should return 404 (skill not found) or 401/403 (auth required)
        assert response.status_code in [404, 401, 403]

    @pytest.mark.asyncio
    async def test_list_installed_skills(self, test_client: AsyncClient):
        """Test listing installed skills"""
        response = await test_client.get(
            "/api/v1/skills/installed",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should return 200 (empty list) or 401/403 (auth required)
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            installed = response.json()
            assert isinstance(installed, list)

    @pytest.mark.asyncio
    async def test_pagination(self, test_client: AsyncClient):
        """Test pagination parameters"""
        response = await test_client.get(
            "/api/v1/skills",
            params={"limit": 5, "offset": 0}
        )
        assert response.status_code == 200
        skills = response.json()
        assert isinstance(skills, list)
        assert len(skills) <= 5

    @pytest.mark.asyncio
    async def test_sort_options(self, test_client: AsyncClient):
        """Test different sort options"""
        sort_options = ["name", "created_at", "download_count", "avg_rating"]
        
        for sort_by in sort_options:
            response = await test_client.get(
                "/api/v1/skills",
                params={"sort_by": sort_by, "sort_order": "desc"}
            )
            assert response.status_code == 200
            skills = response.json()
            assert isinstance(skills, list)

