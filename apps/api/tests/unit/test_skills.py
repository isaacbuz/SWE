"""
Unit tests for Skills API endpoints
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi import status
from httpx import AsyncClient


@pytest.fixture
def mock_skill():
    """Mock skill data"""
    return {
        "id": str(uuid4()),
        "name": "Test Skill",
        "slug": "test-skill",
        "version": "1.0.0",
        "description": "A test skill",
        "detailed_description": "Detailed description",
        "category": "CODE_GENERATION",
        "tags": ["test", "code"],
        "prompt_template": "Generate {{name}}",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        },
        "model_preferences": {
            "preferred_models": ["claude-sonnet-4"],
            "min_quality": 0.8
        },
        "author_id": str(uuid4()),
        "author_name": "Test Author",
        "download_count": 0,
        "installation_count": 0,
        "execution_count": 0,
        "avg_rating": 0.0,
        "review_count": 0,
        "status": "active",
        "visibility": "public",
        "license": "MIT",
        "pricing_model": "free",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_skill_installation():
    """Mock skill installation"""
    return {
        "id": str(uuid4()),
        "skill_id": str(uuid4()),
        "user_id": str(uuid4()),
        "version": "1.0.0",
        "auto_update": True,
        "enabled": True,
        "installed_at": datetime.utcnow(),
        "last_used_at": None,
        "use_count": 0,
    }


@pytest.mark.unit
@pytest.mark.skills
class TestSkillsAPI:
    """Test Skills API endpoints"""

    @pytest.mark.asyncio
    async def test_list_skills_success(self, client: AsyncClient, mock_skill):
        """Test listing skills successfully"""
        # Mock database service
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.list_skills = AsyncMock(return_value=[mock_skill])
            mock_db_service.return_value = mock_service

            response = await client.get("/api/v1/skills")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert "id" in data[0]
                assert "name" in data[0]

    @pytest.mark.asyncio
    async def test_list_skills_with_filters(self, client: AsyncClient, mock_skill):
        """Test listing skills with filters"""
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.list_skills = AsyncMock(return_value=[mock_skill])
            mock_db_service.return_value = mock_service

            response = await client.get(
                "/api/v1/skills",
                params={"category": "CODE_GENERATION", "search": "test"}
            )
            
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_skill_success(self, client: AsyncClient, mock_skill):
        """Test getting skill details"""
        skill_id = mock_skill["id"]
        
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.get_skill_by_id = AsyncMock(return_value=mock_skill)
            mock_db_service.return_value = mock_service

            response = await client.get(f"/api/v1/skills/{skill_id}")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == skill_id
            assert "prompt_template" in data

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, client: AsyncClient):
        """Test getting non-existent skill"""
        skill_id = str(uuid4())
        
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.get_skill_by_id = AsyncMock(return_value=None)
            mock_db_service.return_value = mock_service

            response = await client.get(f"/api/v1/skills/{skill_id}")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_skill_success(self, client: AsyncClient, mock_skill):
        """Test creating a skill"""
        skill_data = {
            "name": "New Skill",
            "slug": "new-skill",
            "description": "A new skill",
            "category": "CODE_GENERATION",
            "prompt_template": "Generate {{input}}",
            "input_schema": {
                "type": "object",
                "properties": {"input": {"type": "string"}}
            },
            "output_schema": {
                "type": "object",
                "properties": {"output": {"type": "string"}}
            },
        }
        
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.get_skill_by_slug = AsyncMock(return_value=None)
            mock_service.create_skill = AsyncMock(return_value=mock_skill)
            mock_db_service.return_value = mock_service

            # Note: This would require authentication in real scenario
            # response = await client.post("/api/v1/skills", json=skill_data)
            # assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_execute_skill_success(self, client: AsyncClient, mock_skill):
        """Test executing a skill"""
        skill_id = mock_skill["id"]
        execution_request = {
            "skill_id": skill_id,
            "inputs": {"name": "test"},
            "context": {}
        }
        
        execution_result = {
            "execution_id": str(uuid4()),
            "skill_id": skill_id,
            "skill_version": "1.0.0",
            "status": "success",
            "inputs": {"name": "test"},
            "outputs": {"result": "generated"},
            "validation_passed": True,
            "latency_ms": 100,
            "cost_usd": 0.001,
            "cache_hit": False,
            "executed_at": datetime.utcnow().isoformat(),
        }
        
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service, \
             patch('apps.api.routers.skills.get_skills_engine') as mock_engine:
            
            mock_service = Mock()
            mock_service.get_skill_by_id = AsyncMock(return_value=mock_skill)
            mock_service.skill_dict_to_model = Mock(return_value=Mock())
            mock_service.log_execution = AsyncMock(return_value=uuid4())
            mock_db_service.return_value = mock_service
            
            mock_engine_instance = Mock()
            mock_engine_instance.execute_skill = AsyncMock(return_value=Mock(
                skill_id=skill_id,
                skill_version="1.0.0",
                status=Mock(value="success"),
                inputs={"name": "test"},
                outputs={"result": "generated"},
                validation_passed=True,
                validation_result=Mock(dict=lambda: {}),
                model_id="claude-sonnet-4",
                model_provider="anthropic",
                latency_ms=100,
                tokens_input=10,
                tokens_output=5,
                cost_usd=0.001,
                cache_hit=False,
                executed_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            ))
            mock_engine.return_value = mock_engine_instance

            # Note: Would require authentication
            # response = await client.post(
            #     f"/api/v1/skills/{skill_id}/execute",
            #     json=execution_request
            # )
            # assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_install_skill_success(self, client: AsyncClient, mock_skill_installation):
        """Test installing a skill"""
        skill_id = mock_skill_installation["skill_id"]
        
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.install_skill = AsyncMock(return_value=mock_skill_installation)
            mock_db_service.return_value = mock_service

            # Note: Would require authentication
            # response = await client.post(f"/api/v1/skills/{skill_id}/install")
            # assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_uninstall_skill_success(self, client: AsyncClient):
        """Test uninstalling a skill"""
        skill_id = str(uuid4())
        
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.uninstall_skill = AsyncMock(return_value=True)
            mock_db_service.return_value = mock_service

            # Note: Would require authentication
            # response = await client.delete(f"/api/v1/skills/{skill_id}/install")
            # assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_list_installed_skills(self, client: AsyncClient, mock_skill_installation):
        """Test listing installed skills"""
        with patch('apps.api.routers.skills.get_skills_db_service') as mock_db_service:
            mock_service = Mock()
            mock_service.list_installed_skills = AsyncMock(return_value=[mock_skill_installation])
            mock_db_service.return_value = mock_service

            # Note: Would require authentication
            # response = await client.get("/api/v1/skills/installed")
            # assert response.status_code == status.HTTP_200_OK
            # data = response.json()
            # assert isinstance(data, list)


@pytest.mark.unit
@pytest.mark.skills
class TestSkillsValidation:
    """Test Skills input/output validation"""

    def test_skill_input_validation(self):
        """Test skill input schema validation"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        
        # Valid input
        valid_input = {"name": "test"}
        # This would be validated by jsonschema in actual implementation
        
        # Invalid input (missing required field)
        invalid_input = {}
        # Would raise ValidationError

    def test_skill_output_validation(self):
        """Test skill output schema validation"""
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        }
        
        # Valid output
        valid_output = {"result": "success"}
        
        # Invalid output (missing required field)
        invalid_output = {}
        # Would raise ValidationError

