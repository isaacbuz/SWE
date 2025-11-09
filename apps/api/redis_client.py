"""
Redis connection and client management.
"""
try:
    import redis.asyncio as redis
except ImportError:
    # Fallback for older redis versions
    import aioredis as redis
from typing import Optional

from config import settings

# Global Redis client
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            # Try redis.asyncio (redis >= 5.0)
            _redis_client = redis.from_url(
                str(settings.redis_url),
                max_connections=settings.redis_pool_size,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
        except AttributeError:
            # Fallback to aioredis (older versions)
            _redis_client = redis.from_url(
                str(settings.redis_url),
                max_connections=settings.redis_pool_size,
                decode_responses=True,
            )
    return _redis_client


async def check_redis_connectivity() -> bool:
    """
    Check if Redis is accessible.
    
    Returns:
        bool: True if Redis is accessible
    """
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception:
        return False


async def close_redis_connections():
    """Close Redis connections."""
    global _redis_client
    if _redis_client:
        try:
            # Try aclose() for redis.asyncio
            await _redis_client.aclose()
        except AttributeError:
            # Fallback to close() for aioredis
            await _redis_client.close()
        _redis_client = None

