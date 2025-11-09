"""
Redis connection management for the API application.
Provides async Redis connection pooling with lifecycle management.
"""
import logging
from typing import Optional
import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis
from urllib.parse import urlparse

from config import settings

logger = logging.getLogger(__name__)

# Global Redis pool and client
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None


def _parse_redis_url(url: str) -> dict:
    """Parse Redis URL into connection parameters"""
    parsed = urlparse(url)
    
    return {
        "host": parsed.hostname or "localhost",
        "port": int(parsed.port or 6379),
        "db": int(parsed.path.lstrip("/") or 0) if parsed.path else 0,
        "password": parsed.password,
        "ssl": parsed.scheme == "rediss",
        "decode_responses": False  # Keep binary for flexibility
    }


async def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool"""
    global _redis_pool
    
    if _redis_pool is None:
        try:
            redis_params = _parse_redis_url(str(settings.redis_url))
            _redis_pool = ConnectionPool(
                host=redis_params["host"],
                port=redis_params["port"],
                db=redis_params["db"],
                password=redis_params["password"],
                ssl=redis_params["ssl"],
                max_connections=settings.redis_pool_size,
                decode_responses=redis_params["decode_responses"]
            )
            logger.info(f"Redis connection pool created: {redis_params['host']}:{redis_params['port']}/{redis_params['db']}")
        except Exception as e:
            logger.error(f"Failed to create Redis connection pool: {e}")
            raise
    
    return _redis_pool


async def get_redis_client() -> Redis:
    """Get or create Redis client"""
    global _redis_client
    
    if _redis_client is None:
        pool = await get_redis_pool()
        _redis_client = Redis(connection_pool=pool)
        logger.info("Redis client created")
    
    return _redis_client


async def close_redis_pool() -> None:
    """Close Redis connection pool and client"""
    global _redis_pool, _redis_client
    
    if _redis_client:
        try:
            await _redis_client.aclose()
            _redis_client = None
            logger.info("Redis client closed")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
    
    if _redis_pool:
        try:
            await _redis_pool.aclose()
            _redis_pool = None
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis pool: {e}")


async def redis_health_check() -> bool:
    """Check Redis connection health"""
    try:
        client = await get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

