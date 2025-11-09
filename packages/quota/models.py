"""
Quota System Data Models
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class QuotaType(str, Enum):
    """Quota types"""
    DAILY = "daily"
    MONTHLY = "monthly"
    PER_REQUEST = "per_request"


class QuotaScope(str, Enum):
    """Quota scope"""
    USER = "user"
    TEAM = "team"
    PROJECT = "project"
    TOOL = "tool"
    PROVIDER = "provider"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    tokens_per_hour: Optional[int] = None
    tokens_per_day: Optional[int] = None


@dataclass
class CostQuota:
    """Cost quota configuration"""
    daily_limit: Optional[float] = None  # USD per day
    monthly_limit: Optional[float] = None  # USD per month
    per_request_limit: Optional[float] = None  # USD per request
    reset_day: Optional[int] = None  # Day of month for monthly reset (1-31)
    reset_hour: Optional[int] = None  # Hour of day for daily reset (0-23)


@dataclass
class QuotaConfig:
    """Complete quota configuration"""
    scope: QuotaScope
    identifier: str  # user_id, team_id, project_id, tool_name, provider_name
    rate_limits: RateLimitConfig = field(default_factory=RateLimitConfig)
    cost_quota: Optional[CostQuota] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuotaResult:
    """Result of quota check"""
    allowed: bool
    reason: str = ""
    remaining_requests: Optional[int] = None
    remaining_cost: Optional[float] = None
    reset_at: Optional[datetime] = None
    quota_type: Optional[QuotaType] = None
    
    def __bool__(self):
        return self.allowed


@dataclass
class QuotaUsage:
    """Current quota usage"""
    identifier: str
    scope: QuotaScope
    requests_today: int = 0
    requests_this_month: int = 0
    cost_today: float = 0.0
    cost_this_month: float = 0.0
    last_reset: Optional[datetime] = None
    next_reset: Optional[datetime] = None

