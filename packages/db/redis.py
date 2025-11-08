"""
Redis utilities for caching, rate limiting, and session management.

Provides high-level abstractions for common Redis patterns used across the
AI-First Software Engineering Platform.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Set
from functools import wraps
import hashlib
import pickle

import redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError

logger = logging.getLogger(__name__)


class RedisConfig:
    """Configuration for Redis connection."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        ssl: bool = False,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
    ):
        """Initialize Redis configuration from environment or explicit parameters."""
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", 6379))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.ssl = ssl or os.getenv("REDIS_SSL", "false").lower() == "true"
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout


class RedisClient:
    """
    Singleton Redis client with connection pooling and utilities for caching,
    rate limiting, and session management.
    """

    _instance: Optional["RedisClient"] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls, config: Optional[RedisConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize Redis client with connection pooling."""
        if self._initialized:
            return

        self.config = config or RedisConfig()
        self._setup_connection_pool()
        self._initialized = True
        logger.info(
            f"Redis client initialized: {self.config.host}:{self.config.port}/{self.config.db}"
        )

    def _setup_connection_pool(self):
        """Set up Redis connection pool."""
        if RedisClient._pool is None:
            RedisClient._pool = ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=False,
            )

        if RedisClient._client is None:
            RedisClient._client = redis.Redis(connection_pool=RedisClient._pool)

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client instance."""
        if RedisClient._client is None:
            self._setup_connection_pool()
        return RedisClient._client

    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            self.client.ping()
            return True
        except (ConnectionError, RedisError) as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    def close(self):
        """Close Redis connection and clean up pool."""
        if RedisClient._client:
            RedisClient._client.close()
            RedisClient._client = None
        if RedisClient._pool:
            RedisClient._pool.disconnect()
            RedisClient._pool = None


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================


class CacheManager:
    """High-level cache abstraction for common patterns."""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client.client

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        serialize: bool = True,
    ) -> bool:
        """
        Set a cache value.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            serialize: Whether to JSON serialize the value

        Returns:
            True if successful, False otherwise
        """
        try:
            if serialize and not isinstance(value, (str, bytes)):
                value = json.dumps(value)

            if ttl_seconds:
                self.redis.setex(key, ttl_seconds, value)
            else:
                self.redis.set(key, value)
            return True
        except RedisError as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False

    def get(
        self, key: str, deserialize: bool = True, default: Any = None
    ) -> Any:
        """
        Get a cache value.

        Args:
            key: Cache key
            deserialize: Whether to JSON deserialize the value
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            value = self.redis.get(key)
            if value is None:
                return default

            if deserialize:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value
        except RedisError as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return default

    def delete(self, *keys: str) -> int:
        """
        Delete one or more cache keys.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        try:
            return self.redis.delete(*keys)
        except RedisError as e:
            logger.error(f"Cache delete failed: {e}")
            return 0

    def exists(self, *keys: str) -> bool:
        """Check if keys exist in cache."""
        try:
            return bool(self.redis.exists(*keys))
        except RedisError as e:
            logger.error(f"Cache exists check failed: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Cache clear pattern failed: {e}")
            return 0

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        try:
            return self.redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Cache increment failed for key {key}: {e}")
            return 0

    def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a counter."""
        try:
            return self.redis.decrby(key, amount)
        except RedisError as e:
            logger.error(f"Cache decrement failed for key {key}: {e}")
            return 0

    def ttl(self, key: str) -> int:
        """Get remaining TTL in seconds. Returns -1 if no expiry, -2 if not found."""
        try:
            return self.redis.ttl(key)
        except RedisError as e:
            logger.error(f"Cache ttl check failed for key {key}: {e}")
            return -2


def cache_result(ttl_seconds: int = 3600, key_prefix: str = "cache"):
    """
    Decorator to cache function results.

    Args:
        ttl_seconds: Cache TTL in seconds (default 1 hour)
        key_prefix: Prefix for cache keys

    Usage:
        @cache_result(ttl_seconds=3600)
        def expensive_function(arg1, arg2):
            return result
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = CacheManager(RedisClient())

            # Generate cache key from function name and arguments
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds=ttl_seconds)
            return result

        return wrapper

    return decorator


def _generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key from function name and arguments."""
    key_parts = [prefix, func_name]

    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg))
        else:
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest())

    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()}")

    return ":".join(key_parts)


# ============================================================================
# RATE LIMITING
# ============================================================================


class RateLimiter:
    """Rate limiting implementation using Redis sliding window counter."""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client.client

    def is_allowed(
        self, identifier: str, max_requests: int, window_seconds: int = 60
    ) -> bool:
        """
        Check if a request should be allowed based on rate limit.

        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if request allowed, False if rate limited
        """
        key = f"rate_limit:{identifier}"
        try:
            current = self.redis.incr(key)
            if current == 1:
                # First request, set expiry
                self.redis.expire(key, window_seconds)

            return current <= max_requests
        except RedisError as e:
            logger.error(f"Rate limit check failed for {identifier}: {e}")
            return True  # Allow on error

    def get_remaining(self, identifier: str, max_requests: int) -> int:
        """Get remaining requests for identifier."""
        key = f"rate_limit:{identifier}"
        try:
            current = self.redis.get(key)
            if current is None:
                return max_requests
            return max(0, max_requests - int(current))
        except RedisError as e:
            logger.error(f"Get remaining requests failed for {identifier}: {e}")
            return max_requests

    def reset(self, identifier: str) -> bool:
        """Reset rate limit for identifier."""
        key = f"rate_limit:{identifier}"
        try:
            return bool(self.redis.delete(key))
        except RedisError as e:
            logger.error(f"Rate limit reset failed for {identifier}: {e}")
            return False


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


class SessionManager:
    """Manage user sessions in Redis."""

    def __init__(self, redis_client: RedisClient, default_ttl_seconds: int = 86400):
        self.redis = redis_client.client
        self.default_ttl = default_ttl_seconds

    def create(self, session_id: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        """Create a new session."""
        try:
            ttl = ttl_seconds or self.default_ttl
            session_key = f"session:{session_id}"
            return bool(self.redis.setex(session_key, ttl, json.dumps(data)))
        except RedisError as e:
            logger.error(f"Session create failed: {e}")
            return False

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        try:
            session_key = f"session:{session_id}"
            data = self.redis.get(session_key)
            if data is None:
                return None
            return json.loads(data)
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Session get failed: {e}")
            return None

    def update(self, session_id: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        """Update session data."""
        try:
            ttl = ttl_seconds or self.default_ttl
            session_key = f"session:{session_id}"
            return bool(self.redis.setex(session_key, ttl, json.dumps(data)))
        except RedisError as e:
            logger.error(f"Session update failed: {e}")
            return False

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            session_key = f"session:{session_id}"
            return bool(self.redis.delete(session_key))
        except RedisError as e:
            logger.error(f"Session delete failed: {e}")
            return False

    def refresh(self, session_id: str, ttl_seconds: Optional[int] = None) -> bool:
        """Refresh session expiry."""
        try:
            ttl = ttl_seconds or self.default_ttl
            session_key = f"session:{session_id}"
            return bool(self.redis.expire(session_key, ttl))
        except RedisError as e:
            logger.error(f"Session refresh failed: {e}")
            return False


# ============================================================================
# DISTRIBUTED LOCK (for task coordination)
# ============================================================================


class DistributedLock:
    """Simple distributed lock using Redis."""

    def __init__(self, redis_client: RedisClient, timeout_seconds: int = 30):
        self.redis = redis_client.client
        self.timeout_seconds = timeout_seconds

    def acquire(self, lock_name: str, value: str = "locked") -> bool:
        """
        Acquire a lock.

        Args:
            lock_name: Name of the lock
            value: Value to set (useful for verification)

        Returns:
            True if lock acquired, False if already locked
        """
        try:
            lock_key = f"lock:{lock_name}"
            acquired = self.redis.set(
                lock_key, value, nx=True, ex=self.timeout_seconds
            )
            return bool(acquired)
        except RedisError as e:
            logger.error(f"Lock acquire failed for {lock_name}: {e}")
            return False

    def release(self, lock_name: str) -> bool:
        """Release a lock."""
        try:
            lock_key = f"lock:{lock_name}"
            return bool(self.redis.delete(lock_key))
        except RedisError as e:
            logger.error(f"Lock release failed for {lock_name}: {e}")
            return False

    def is_locked(self, lock_name: str) -> bool:
        """Check if lock is currently held."""
        try:
            lock_key = f"lock:{lock_name}"
            return bool(self.redis.exists(lock_key))
        except RedisError as e:
            logger.error(f"Lock check failed for {lock_name}: {e}")
            return False


# ============================================================================
# PUBSUB for event broadcasting
# ============================================================================


class PubSubManager:
    """Publish-Subscribe for real-time events."""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client.client
        self.pubsub = None

    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """
        Publish a message to a channel.

        Args:
            channel: Channel name
            message: Message data

        Returns:
            Number of subscribers that received the message
        """
        try:
            return self.redis.publish(channel, json.dumps(message))
        except RedisError as e:
            logger.error(f"Publish failed to {channel}: {e}")
            return 0

    def subscribe(self, *channels: str):
        """Subscribe to channels."""
        try:
            self.pubsub = self.redis.pubsub()
            self.pubsub.subscribe(*channels)
            return self.pubsub
        except RedisError as e:
            logger.error(f"Subscribe failed: {e}")
            return None


# ============================================================================
# Module-level convenience functions
# ============================================================================


def get_redis_client(config: Optional[RedisConfig] = None) -> RedisClient:
    """Get or create singleton Redis client."""
    return RedisClient(config)


def get_cache_manager(redis_client: Optional[RedisClient] = None) -> CacheManager:
    """Get cache manager instance."""
    client = redis_client or RedisClient()
    return CacheManager(client)


def get_rate_limiter(redis_client: Optional[RedisClient] = None) -> RateLimiter:
    """Get rate limiter instance."""
    client = redis_client or RedisClient()
    return RateLimiter(client)


def get_session_manager(
    redis_client: Optional[RedisClient] = None, ttl_seconds: int = 86400
) -> SessionManager:
    """Get session manager instance."""
    client = redis_client or RedisClient()
    return SessionManager(client, ttl_seconds)
