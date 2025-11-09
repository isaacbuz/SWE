"""
Cost Tracking Service
Real-time cost tracking for LLM providers and tool execution
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from .models import CostQuota, QuotaScope, QuotaUsage
from ..db.redis_connection import get_redis_pool


class CostTracker:
    """
    Real-time cost tracking service
    
    Features:
    - Per-user/team/project cost tracking
    - Daily and monthly cost quotas
    - Cost aggregation and reporting
    - Integration with Redis for fast lookups
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._redis = None
    
    async def _get_redis(self):
        """Get Redis connection"""
        if self._redis is None:
            self._redis = await get_redis_pool()
        return self._redis
    
    async def record_cost(
        self,
        scope: QuotaScope,
        identifier: str,
        cost: float,
        provider: Optional[str] = None,
        tool_name: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record a cost transaction
        
        Args:
            scope: Quota scope (user, team, project, tool, provider)
            identifier: Identifier for the scope
            cost: Cost in USD
            provider: Optional provider name
            tool_name: Optional tool name
            timestamp: Optional timestamp (defaults to now)
        """
        if cost <= 0:
            return
        
        timestamp = timestamp or datetime.utcnow()
        redis = await self._get_redis()
        
        # Daily cost tracking
        day_key = f"cost:{scope.value}:{identifier}:day:{timestamp.strftime('%Y-%m-%d')}"
        await redis.incrbyfloat(day_key, cost)
        await redis.expire(day_key, 86400 * 2)  # Keep for 2 days
        
        # Monthly cost tracking
        month_key = f"cost:{scope.value}:{identifier}:month:{timestamp.strftime('%Y-%m')}"
        await redis.incrbyfloat(month_key, cost)
        await redis.expire(month_key, 86400 * 35)  # Keep for 35 days
        
        # Provider-specific tracking
        if provider:
            provider_key = f"cost:{scope.value}:{identifier}:provider:{provider}:{timestamp.strftime('%Y-%m-%d')}"
            await redis.incrbyfloat(provider_key, cost)
            await redis.expire(provider_key, 86400 * 2)
        
        # Tool-specific tracking
        if tool_name:
            tool_key = f"cost:{scope.value}:{identifier}:tool:{tool_name}:{timestamp.strftime('%Y-%m-%d')}"
            await redis.incrbyfloat(tool_key, cost)
            await redis.expire(tool_key, 86400 * 2)
        
        self.logger.debug(f"Recorded cost ${cost:.6f} for {scope.value}:{identifier}")
    
    async def get_cost_today(
        self,
        scope: QuotaScope,
        identifier: str
    ) -> float:
        """Get total cost for today"""
        redis = await self._get_redis()
        today = datetime.utcnow().strftime('%Y-%m-%d')
        key = f"cost:{scope.value}:{identifier}:day:{today}"
        value = await redis.get(key)
        return float(value) if value else 0.0
    
    async def get_cost_this_month(
        self,
        scope: QuotaScope,
        identifier: str
    ) -> float:
        """Get total cost for this month"""
        redis = await self._get_redis()
        month = datetime.utcnow().strftime('%Y-%m')
        key = f"cost:{scope.value}:{identifier}:month:{month}"
        value = await redis.get(key)
        return float(value) if value else 0.0
    
    async def get_cost_by_provider(
        self,
        scope: QuotaScope,
        identifier: str,
        provider: str,
        date: Optional[datetime] = None
    ) -> float:
        """Get cost for a specific provider"""
        redis = await self._get_redis()
        date = date or datetime.utcnow()
        key = f"cost:{scope.value}:{identifier}:provider:{provider}:{date.strftime('%Y-%m-%d')}"
        value = await redis.get(key)
        return float(value) if value else 0.0
    
    async def get_cost_by_tool(
        self,
        scope: QuotaScope,
        identifier: str,
        tool_name: str,
        date: Optional[datetime] = None
    ) -> float:
        """Get cost for a specific tool"""
        redis = await self._get_redis()
        date = date or datetime.utcnow()
        key = f"cost:{scope.value}:{identifier}:tool:{tool_name}:{date.strftime('%Y-%m-%d')}"
        value = await redis.get(key)
        return float(value) if value else 0.0
    
    async def get_cost_history(
        self,
        scope: QuotaScope,
        identifier: str,
        days: int = 30
    ) -> List[Dict[str, any]]:
        """Get cost history for the last N days"""
        redis = await self._get_redis()
        history = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            day_key = f"cost:{scope.value}:{identifier}:day:{date.strftime('%Y-%m-%d')}"
            value = await redis.get(day_key)
            cost = float(value) if value else 0.0
            
            history.append({
                "date": date.strftime('%Y-%m-%d'),
                "cost": cost
            })
        
        return list(reversed(history))
    
    async def reset_daily_cost(
        self,
        scope: QuotaScope,
        identifier: str,
        date: Optional[datetime] = None
    ) -> None:
        """Reset daily cost for a specific date"""
        redis = await self._get_redis()
        date = date or datetime.utcnow()
        day_key = f"cost:{scope.value}:{identifier}:day:{date.strftime('%Y-%m-%d')}"
        await redis.delete(day_key)
    
    async def reset_monthly_cost(
        self,
        scope: QuotaScope,
        identifier: str,
        month: Optional[str] = None
    ) -> None:
        """Reset monthly cost for a specific month"""
        redis = await self._get_redis()
        month = month or datetime.utcnow().strftime('%Y-%m')
        month_key = f"cost:{scope.value}:{identifier}:month:{month}"
        await redis.delete(month_key)

