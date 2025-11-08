"""
Caching for Skills execution results
"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

from packages.db.redis import RedisClient, CacheManager

logger = logging.getLogger(__name__)


class SkillCache:
    """Cache manager for Skills execution results"""
    
    def __init__(self, redis_client: Optional[RedisClient] = None, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.redis_client = redis_client or RedisClient()
        self.cache = CacheManager(self.redis_client)
        self.default_ttl = default_ttl
    
    def compute_key(
        self,
        skill_id: str,
        skill_version: str,
        inputs: Dict[str, Any]
    ) -> str:
        """
        Compute cache key from skill and inputs
        
        Args:
            skill_id: Skill ID
            skill_version: Skill version
            inputs: Input dictionary
            
        Returns:
            Cache key string
        """
        # Create deterministic key from skill ID, version, and inputs
        key_data = {
            "skill_id": skill_id,
            "skill_version": skill_version,
            "inputs": self._normalize_inputs(inputs)
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"skill:cache:{skill_id}:{key_hash[:16]}"
    
    def _normalize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize inputs for consistent hashing"""
        normalized = {}
        for key, value in sorted(inputs.items()):
            if isinstance(value, dict):
                normalized[key] = self._normalize_inputs(value)
            elif isinstance(value, list):
                normalized[key] = [self._normalize_inputs(item) if isinstance(item, dict) else item for item in value]
            else:
                normalized[key] = value
        return normalized
    
    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached result or None
        """
        try:
            result = self.cache.get(cache_key)
            if result:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            return None
        except Exception as e:
            logger.error(f"Cache get failed for key {cache_key}: {e}")
            return None
    
    async def set(
        self,
        cache_key: str,
        result: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Cache result
        
        Args:
            cache_key: Cache key
            result: Result dictionary
            ttl_seconds: TTL in seconds (uses default if None)
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl_seconds or self.default_ttl
            success = self.cache.set(cache_key, result, ttl_seconds=ttl)
            if success:
                logger.debug(f"Cached result for key: {cache_key} (TTL: {ttl}s)")
            return success
        except Exception as e:
            logger.error(f"Cache set failed for key {cache_key}: {e}")
            return False
    
    async def invalidate(self, skill_id: str) -> int:
        """
        Invalidate all cache entries for a skill
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Number of keys deleted
        """
        try:
            pattern = f"skill:cache:{skill_id}:*"
            deleted = self.cache.clear_pattern(pattern)
            logger.info(f"Invalidated {deleted} cache entries for skill {skill_id}")
            return deleted
        except Exception as e:
            logger.error(f"Cache invalidation failed for skill {skill_id}: {e}")
            return 0
    
    async def exists(self, cache_key: str) -> bool:
        """Check if cache key exists"""
        try:
            return self.cache.exists(cache_key)
        except Exception as e:
            logger.error(f"Cache exists check failed for key {cache_key}: {e}")
            return False

