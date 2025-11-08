"""
Tests for Skills Database Service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime
import json

from packages.skills_engine.db_service import SkillsDatabaseService


@pytest.fixture
def mock_pool():
    """Mock AsyncPG connection pool"""
    pool = Mock()
    pool.acquire = Mock()
    return pool


@pytest.fixture
def mock_conn():
    """Mock database connection"""
    conn = AsyncMock()
    return conn


@pytest.fixture
def db_service(mock_pool):
    """Create database service instance"""
    return SkillsDatabaseService(mock_pool)


@pytest.mark.asyncio
async def test_get_skill_by_id(db_service, mock_pool, mock_conn):
    """Test getting skill by ID"""
    skill_id = uuid4()
    mock_row = {
        "id": skill_id,
        "name": "Test Skill",
        "slug": "test-skill",
        "version": "1.0.0",
        "description": "Test",
        "prompt_template": "Template",
        "input_schema": json.dumps({"type": "object"}),
        "output_schema": json.dumps({"type": "object"}),
        "category": "CODE_GENERATION",
        "tags": ["test"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    mock_conn.fetchrow = AsyncMock(return_value=mock_row)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    result = await db_service.get_skill_by_id(skill_id)
    
    assert result is not None
    assert result["id"] == skill_id
    assert result["name"] == "Test Skill"


@pytest.mark.asyncio
async def test_get_skill_by_id_not_found(db_service, mock_pool, mock_conn):
    """Test getting non-existent skill"""
    skill_id = uuid4()
    
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    result = await db_service.get_skill_by_id(skill_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_list_skills(db_service, mock_pool, mock_conn):
    """Test listing skills with filters"""
    mock_rows = [
        {
            "id": uuid4(),
            "name": "Skill 1",
            "category": "CODE_GENERATION",
            "tags": ["test"],
            "created_at": datetime.utcnow(),
        }
    ]
    
    mock_conn.fetch = AsyncMock(return_value=mock_rows)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    result = await db_service.list_skills(
        category="CODE_GENERATION",
        limit=10,
        offset=0
    )
    
    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_create_skill(db_service, mock_pool, mock_conn):
    """Test creating a skill"""
    skill_data = {
        "name": "New Skill",
        "slug": "new-skill",
        "description": "Description",
        "category": "CODE_GENERATION",
        "prompt_template": "Template",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
    }
    
    author_id = uuid4()
    mock_row = {
        "id": uuid4(),
        "name": "New Skill",
        **skill_data,
    }
    
    mock_conn.fetchrow = AsyncMock(return_value=mock_row)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    result = await db_service.create_skill(skill_data, author_id)
    
    assert result is not None
    assert result["name"] == "New Skill"


@pytest.mark.asyncio
async def test_log_execution(db_service, mock_pool, mock_conn):
    """Test logging skill execution"""
    execution_data = {
        "skill_id": uuid4(),
        "skill_version": "1.0.0",
        "user_id": uuid4(),
        "inputs": {"test": "input"},
        "outputs": {"test": "output"},
        "status": "success",
        "latency_ms": 100,
        "cost_usd": 0.001,
    }
    
    mock_conn.execute = AsyncMock(return_value="INSERT 1")
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    execution_id = await db_service.log_execution(execution_data)
    
    assert execution_id is not None


@pytest.mark.asyncio
async def test_install_skill(db_service, mock_pool, mock_conn):
    """Test installing a skill"""
    skill_id = uuid4()
    user_id = uuid4()
    
    # Mock get_skill_by_id for version lookup
    mock_skill = {
        "version": "1.0.0"
    }
    mock_conn.fetchrow = AsyncMock(side_effect=[None, mock_skill])  # First for existing check, then for version
    
    # Mock insert
    mock_installation = {
        "id": uuid4(),
        "skill_id": skill_id,
        "user_id": user_id,
        "version": "1.0.0",
        "auto_update": True,
        "enabled": True,
        "installed_at": datetime.utcnow(),
    }
    mock_conn.fetchrow = AsyncMock(return_value=mock_installation)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    result = await db_service.install_skill(skill_id, user_id)
    
    assert result is not None


@pytest.mark.asyncio
async def test_uninstall_skill(db_service, mock_pool, mock_conn):
    """Test uninstalling a skill"""
    skill_id = uuid4()
    user_id = uuid4()
    
    mock_conn.execute = AsyncMock(return_value="DELETE 1")
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    result = await db_service.uninstall_skill(skill_id, user_id)
    
    assert result is True


@pytest.mark.asyncio
async def test_list_installed_skills(db_service, mock_pool, mock_conn):
    """Test listing installed skills"""
    user_id = uuid4()
    mock_rows = [
        {
            "id": uuid4(),
            "skill_id": uuid4(),
            "user_id": user_id,
            "version": "1.0.0",
            "enabled": True,
        }
    ]
    
    mock_conn.fetch = AsyncMock(return_value=mock_rows)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    result = await db_service.list_installed_skills(user_id)
    
    assert isinstance(result, list)
    assert len(result) > 0


def test_skill_dict_to_model(db_service):
    """Test converting database dict to Skill model"""
    skill_dict = {
        "id": str(uuid4()),
        "name": "Test Skill",
        "slug": "test-skill",
        "version": "1.0.0",
        "description": "Test",
        "prompt_template": "Template {{name}}",
        "input_schema": json.dumps({"type": "object", "properties": {"name": {"type": "string"}}}),
        "output_schema": json.dumps({"type": "object"}),
        "model_preferences": json.dumps({"temperature": 0.7}),
        "validation_rules": None,
        "category": "CODE_GENERATION",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    skill = db_service.skill_dict_to_model(skill_dict)
    
    assert skill.id == skill_dict["id"]
    assert skill.name == "Test Skill"
    assert skill.category == "CODE_GENERATION"

