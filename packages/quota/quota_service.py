"""
Quota Service
Main service for managing rate limits and cost quotas
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from .models import (
    QuotaConfig, QuotaResult, QuotaUsage, QuotaScope, QuotaType,
    RateLimitConfig, CostQuota
)
from .rate_limit_manager import RateLimitManager
from .cost_tracker import CostTracker


class QuotaService:
    """
    Main quota service for managing rate limits and cost quotas
    
    Features:
    - Per-user and per-tool rate limits
    - Cost quotas (daily/monthly)
    - Real-time cost tracking
    - Quota exhaustion detection
    - Admin override capabilities
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rate_limit_manager = RateLimitManager()
        self.cost_tracker = CostTracker()
        self._quota_configs: Dict[str, QuotaConfig] = {}
    
    def register_quota(self, config: QuotaConfig) -> None:
        """Register a quota configuration"""
        key = f"{config.scope.value}:{config.identifier}"
        self._quota_configs[key] = config
        self.logger.info(f"Registered quota config for {key}")
    
    def get_quota_config(
        self,
        scope: QuotaScope,
        identifier: str
    ) -> Optional[QuotaConfig]:
        """Get quota configuration"""
        key = f"{scope.value}:{identifier}"
        return self._quota_configs.get(key)
    
    async def check_quota(
        self,
        scope: QuotaScope,
        identifier: str,
        estimated_cost: Optional[float] = None,
        admin_override: bool = False
    ) -> QuotaResult:
        """
        Check if request is allowed based on quotas
        
        Args:
            scope: Quota scope
            identifier: Identifier for the scope
            estimated_cost: Estimated cost for this request
            admin_override: If True, bypass quota checks
        
        Returns:
            QuotaResult indicating if request is allowed
        """
        if admin_override:
            return QuotaResult(
                allowed=True,
                reason="Admin override"
            )
        
        config = self.get_quota_config(scope, identifier)
        if not config or not config.enabled:
            # No quota configured, allow
            return QuotaResult(
                allowed=True,
                reason="No quota configured"
            )
        
        # Check rate limits
        if config.rate_limits:
            allowed, remaining, reset_at = await self.rate_limit_manager.check_rate_limit(
                scope, identifier, config.rate_limits
            )
            
            if not allowed:
                return QuotaResult(
                    allowed=False,
                    reason=f"Rate limit exceeded",
                    remaining_requests=remaining,
                    reset_at=reset_at,
                    quota_type=QuotaType.PER_REQUEST
                )
        
        # Check cost quota
        if config.cost_quota and estimated_cost:
            cost_today = await self.cost_tracker.get_cost_today(scope, identifier)
            cost_this_month = await self.cost_tracker.get_cost_this_month(scope, identifier)
            
            # Check daily limit
            if config.cost_quota.daily_limit:
                if cost_today + estimated_cost > config.cost_quota.daily_limit:
                    reset_at = self._get_daily_reset_time(config.cost_quota.reset_hour)
                    return QuotaResult(
                        allowed=False,
                        reason=f"Daily cost quota exceeded (${cost_today:.2f} / ${config.cost_quota.daily_limit:.2f})",
                        remaining_cost=config.cost_quota.daily_limit - cost_today,
                        reset_at=reset_at,
                        quota_type=QuotaType.DAILY
                    )
            
            # Check monthly limit
            if config.cost_quota.monthly_limit:
                if cost_this_month + estimated_cost > config.cost_quota.monthly_limit:
                    reset_at = self._get_monthly_reset_time(config.cost_quota.reset_day)
                    return QuotaResult(
                        allowed=False,
                        reason=f"Monthly cost quota exceeded (${cost_this_month:.2f} / ${config.cost_quota.monthly_limit:.2f})",
                        remaining_cost=config.cost_quota.monthly_limit - cost_this_month,
                        reset_at=reset_at,
                        quota_type=QuotaType.MONTHLY
                    )
            
            # Check per-request limit
            if config.cost_quota.per_request_limit:
                if estimated_cost > config.cost_quota.per_request_limit:
                    return QuotaResult(
                        allowed=False,
                        reason=f"Per-request cost limit exceeded (${estimated_cost:.2f} > ${config.cost_quota.per_request_limit:.2f})",
                        quota_type=QuotaType.PER_REQUEST
                    )
        
        # All checks passed
        remaining_requests = None
        if config.rate_limits:
            remaining_requests = await self.rate_limit_manager.get_remaining_requests(
                scope, identifier, config.rate_limits
            )
        
        return QuotaResult(
            allowed=True,
            reason="Quota check passed",
            remaining_requests=remaining_requests
        )
    
    async def record_usage(
        self,
        scope: QuotaScope,
        identifier: str,
        cost: float,
        provider: Optional[str] = None,
        tool_name: Optional[str] = None
    ) -> None:
        """Record usage (cost) for quota tracking"""
        await self.cost_tracker.record_cost(
            scope, identifier, cost, provider, tool_name
        )
    
    async def get_quota_usage(
        self,
        scope: QuotaScope,
        identifier: str
    ) -> QuotaUsage:
        """Get current quota usage"""
        config = self.get_quota_config(scope, identifier)
        
        cost_today = await self.cost_tracker.get_cost_today(scope, identifier)
        cost_this_month = await self.cost_tracker.get_cost_this_month(scope, identifier)
        
        # Get request counts (simplified - would need to track separately)
        requests_today = 0
        requests_this_month = 0
        
        if config and config.rate_limits:
            remaining = await self.rate_limit_manager.get_remaining_requests(
                scope, identifier, config.rate_limits
            )
            if remaining is not None:
                if config.rate_limits.requests_per_day:
                    requests_today = config.rate_limits.requests_per_day - remaining
                elif config.rate_limits.requests_per_hour:
                    # Approximate daily from hourly
                    requests_today = (config.rate_limits.requests_per_hour - remaining) * 24
        
        return QuotaUsage(
            identifier=identifier,
            scope=scope,
            requests_today=requests_today,
            requests_this_month=requests_this_month,
            cost_today=cost_today,
            cost_this_month=cost_this_month
        )
    
    def _get_daily_reset_time(self, reset_hour: Optional[int] = None) -> datetime:
        """Get next daily reset time"""
        reset_hour = reset_hour or 0
        now = datetime.utcnow()
        reset_at = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
        
        if reset_at <= now:
            reset_at += timedelta(days=1)
        
        return reset_at
    
    def _get_monthly_reset_time(self, reset_day: Optional[int] = None) -> datetime:
        """Get next monthly reset time"""
        reset_day = reset_day or 1
        now = datetime.utcnow()
        
        # Next month
        if now.month == 12:
            reset_at = datetime(now.year + 1, 1, reset_day)
        else:
            reset_at = datetime(now.year, now.month + 1, reset_day)
        
        return reset_at

