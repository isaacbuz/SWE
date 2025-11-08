"""
Tests for Skills cache
"""
import pytest
from unittest.mock import Mock, AsyncMock
from packages.skills_engine.cache import SkillCache


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = Mock()
    return client


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager"""
    manager = Mock()
    manager.get = Mock(return_value=None)
    manager.set = Mock(return_value=True)
    manager.exists = Mock(return_value=False)
    manager.clear_pattern = Mock(return_value=5)
    return manager


@pytest.fixture
def skill_cache(mock_redis_client, mock_cache_manager):
    """Create SkillCache instance"""
    cache = SkillCache(mock_redis_client)
    cache.cache = mock_cache_manager
    return cache


class TestSkillCache:
    """Test Skills cache functionality"""

    def test_compute_key_deterministic(self, skill_cache):
        """Test cache key is deterministic"""
        skill_id = "skill-1"
        version = "1.0.0"
        inputs1 = {"name": "test", "value": 123}
        inputs2 = {"name": "test", "value": 123}
        
        key1 = skill_cache.compute_key(skill_id, version, inputs1)
        key2 = skill_cache.compute_key(skill_id, version, inputs2)
        
        assert key1 == key2

    def test_compute_key_different_inputs(self, skill_cache):
        """Test cache key differs for different inputs"""
        skill_id = "skill-1"
        version = "1.0.0"
        inputs1 = {"name": "test1"}
        inputs2 = {"name": "test2"}
        
        key1 = skill_cache.compute_key(skill_id, version, inputs1)
        key2 = skill_cache.compute_key(skill_id, version, inputs2)
        
        assert key1 != key2

    def test_compute_key_different_skills(self, skill_cache):
        """Test cache key differs for different skills"""
        version = "1.0.0"
        inputs = {"name": "test"}
        
        key1 = skill_cache.compute_key("skill-1", version, inputs)
        key2 = skill_cache.compute_key("skill-2", version, inputs)
        
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, skill_cache, mock_cache_manager):
        """Test cache hit scenario"""
        cached_result = {"result": "cached"}
        mock_cache_manager.get = Mock(return_value=cached_result)
        
        result = await skill_cache.get("cache-key-123")
        
        assert result == cached_result
        mock_cache_manager.get.assert_called_once_with("cache-key-123")

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, skill_cache, mock_cache_manager):
        """Test cache miss scenario"""
        mock_cache_manager.get = Mock(return_value=None)
        
        result = await skill_cache.get("cache-key-123")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cache(self, skill_cache, mock_cache_manager):
        """Test setting cache"""
        result_data = {"result": "data"}
        
        success = await skill_cache.set("cache-key-123", result_data, ttl_seconds=3600)
        
        assert success is True
        mock_cache_manager.set.assert_called_once_with(
            "cache-key-123",
            result_data,
            ttl_seconds=3600
        )

    @pytest.mark.asyncio
    async def test_invalidate_skill(self, skill_cache, mock_cache_manager):
        """Test invalidating all cache entries for a skill"""
        skill_id = "skill-1"
        
        deleted = await skill_cache.invalidate(skill_id)
        
        assert deleted == 5
        mock_cache_manager.clear_pattern.assert_called_once_with(f"skill:cache:{skill_id}:*")

    @pytest.mark.asyncio
    async def test_exists(self, skill_cache, mock_cache_manager):
        """Test checking if cache key exists"""
        mock_cache_manager.exists = Mock(return_value=True)
        
        exists = await skill_cache.exists("cache-key-123")
        
        assert exists is True
        mock_cache_manager.exists.assert_called_once_with("cache-key-123")

    def test_normalize_inputs(self, skill_cache):
        """Test input normalization for consistent hashing"""
        inputs1 = {"a": 1, "b": 2}
        inputs2 = {"b": 2, "a": 1}  # Different order
        
        normalized1 = skill_cache._normalize_inputs(inputs1)
        normalized2 = skill_cache._normalize_inputs(inputs2)
        
        # Should produce same normalized structure
        assert normalized1 == normalized2

