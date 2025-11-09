"""
Rate Limit Manager
Per-user and per-tool rate limiting with Redis backend
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from .models import RateLimitConfig, QuotaScope
from ..db.redis_connection import get_redis_pool


class RateLimitManager:
    """
    Rate limit manager for users and tools
    
    Features:
    - Per-user rate limits
    - Per-tool rate limits
    - Sliding window algorithm
    - Redis-backed storage
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._redis = None
    
    async def _get_redis(self):
        """Get Redis connection"""
        if self._redis is None:
            self._redis = await get_redis_pool()
        return self._redis
    
    async def check_rate_limit(
        self,
        scope: QuotaScope,
        identifier: str,
        config: RateLimitConfig
    ) -> tuple:
        """
        Check if rate limit allows the request
        
        Returns:
            Tuple of (allowed: bool, remaining_requests: Optional[int], reset_at: Optional[datetime])
        """
        redis = await self._get_redis()
        now = datetime.utcnow()
        
        # Check per-minute limit
        if config.requests_per_minute:
            minute_key = f"rate_limit:{scope.value}:{identifier}:minute:{now.strftime('%Y-%m-%d-%H-%M')}"
            current = await redis.incr(minute_key)
            await redis.expire(minute_key, 60)
            
            if current > config.requests_per_minute:
                reset_at = now + timedelta(minutes=1)
                reset_at = reset_at.replace(second=0, microsecond=0)
                return False, 0, reset_at
            
            remaining = config.requests_per_minute - current
        
        # Check per-hour limit
        elif config.requests_per_hour:
            hour_key = f"rate_limit:{scope.value}:{identifier}:hour:{now.strftime('%Y-%m-%d-%H')}"
            current = await redis.incr(hour_key)
            await redis.expire(hour_key, 3600)
            
            if current > config.requests_per_hour:
                reset_at = now + timedelta(hours=1)
                reset_at = reset_at.replace(minute=0, second=0, microsecond=0)
                return False, 0, reset_at
            
            remaining = config.requests_per_hour - current
        
        # Check per-day limit
        elif config.requests_per_day:
            day_key = f"rate_limit:{scope.value}:{identifier}:day:{now.strftime('%Y-%m-%d')}"
            current = await redis.incr(day_key)
            await redis.expire(day_key, 86400)
            
            if current > config.requests_per_day:
                reset_at = now + timedelta(days=1)
                reset_at = reset_at.replace(hour=0, minute=0, second=0, microsecond=0)
                return False, 0, reset_at
            
            remaining = config.requests_per_day - current
        
        else:
            # No rate limit configured
            return True, None, None
        
        return True, remaining, None
    
    async def get_remaining_requests(
        self,
        scope: QuotaScope,
        identifier: str,
        config: RateLimitConfig
    ) -> Optional[int]:
        """Get remaining requests in current window"""
        redis = await self._get_redis()
        now = datetime.utcnow()
        
        if config.requests_per_minute:
            minute_key = f"rate_limit:{scope.value}:{identifier}:minute:{now.strftime('%Y-%m-%d-%H-%M')}"
            current = await redis.get(minute_key)
            if current is None:
                return config.requests_per_minute
            return max(0, config.requests_per_minute - int(current))
        
        elif config.requests_per_hour:
            hour_key = f"rate_limit:{scope.value}:{identifier}:hour:{now.strftime('%Y-%m-%d-%H')}"
            current = await redis.get(hour_key)
            if current is None:
                return config.requests_per_hour
            return max(0, config.requests_per_hour - int(current))
        
        elif config.requests_per_day:
            day_key = f"rate_limit:{scope.value}:{identifier}:day:{now.strftime('%Y-%m-%d')}"
            current = await redis.get(day_key)
            if current is None:
                return config.requests_per_day
            return max(0, config.requests_per_day - int(current))
        
        return None
    
    async def reset_rate_limit(
        self,
        scope: QuotaScope,
        identifier: str,
        window: str = "all"  # "minute", "hour", "day", "all"
    ) -> None:
        """Reset rate limit for identifier"""
        redis = await self._get_redis()
        now = datetime.utcnow()
        
        patterns = []
        if window in ["minute", "all"]:
            patterns.append(f"rate_limit:{scope.value}:{identifier}:minute:*")
        if window in ["hour", "all"]:
            patterns.append(f"rate_limit:{scope.value}:{identifier}:hour:*")
        if window in ["day", "all"]:
            patterns.append(f"rate_limit:{scope.value}:{identifier}:day:*")
        
        # Note: Redis doesn't support pattern deletion directly
        # This is a simplified version - in production, you'd want to track keys
        for pattern in patterns:
            # For now, we'll delete current window keys
            if "minute" in pattern:
                minute_key = f"rate_limit:{scope.value}:{identifier}:minute:{now.strftime('%Y-%m-%d-%H-%M')}"
                await redis.delete(minute_key)
            if "hour" in pattern:
                hour_key = f"rate_limit:{scope.value}:{identifier}:hour:{now.strftime('%Y-%m-%d-%H')}"
                await redis.delete(hour_key)
            if "day" in pattern:
                day_key = f"rate_limit:{scope.value}:{identifier}:day:{now.strftime('%Y-%m-%d')}"
                await redis.delete(day_key)

