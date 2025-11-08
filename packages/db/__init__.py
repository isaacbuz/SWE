"""
Database package for AI-First Software Engineering Platform.

Provides:
- PostgreSQL schema definitions and migrations
- Redis utilities for caching, rate limiting, and sessions
- Evidence-driven audit logging
- Agent execution tracking
"""

__version__ = "0.1.0"

# Export main classes and functions
from .redis import (
    RedisClient,
    RedisConfig,
    CacheManager,
    RateLimiter,
    SessionManager,
    DistributedLock,
    PubSubManager,
    cache_result,
    get_redis_client,
    get_cache_manager,
    get_rate_limiter,
    get_session_manager,
)

__all__ = [
    "RedisClient",
    "RedisConfig",
    "CacheManager",
    "RateLimiter",
    "SessionManager",
    "DistributedLock",
    "PubSubManager",
    "cache_result",
    "get_redis_client",
    "get_cache_manager",
    "get_rate_limiter",
    "get_session_manager",
]
