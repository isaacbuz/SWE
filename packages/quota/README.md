# Rate Limiting and Quota Management System

Comprehensive rate limiting and cost quota management for tool execution and LLM providers.

## Features

- ✅ Per-user and per-tool rate limits
- ✅ Cost quotas (daily/monthly/per-request)
- ✅ Real-time cost tracking
- ✅ Quota exhaustion alerts
- ✅ Threshold warnings (80%, 90%, 95%)
- ✅ Admin override capabilities
- ✅ Redis-backed storage
- ✅ Integration ready for ToolExecutor

## Quick Start

```python
from quota import QuotaService, QuotaConfig, QuotaScope, RateLimitConfig, CostQuota

# Initialize service
quota_service = QuotaService()

# Configure user quota
user_quota = QuotaConfig(
    scope=QuotaScope.USER,
    identifier="user-123",
    rate_limits=RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000
    ),
    cost_quota=CostQuota(
        daily_limit=100.0,  # $100 per day
        monthly_limit=2000.0,  # $2000 per month
        reset_hour=0  # Reset at midnight UTC
    )
)

quota_service.register_quota(user_quota)

# Check quota before execution
result = await quota_service.check_quota(
    scope=QuotaScope.USER,
    identifier="user-123",
    estimated_cost=0.05
)

if result.allowed:
    # Execute tool
    # ...
    # Record actual cost
    await quota_service.record_usage(
        scope=QuotaScope.USER,
        identifier="user-123",
        cost=0.05,
        provider="openai",
        tool_name="createIssues"
    )
else:
    raise Exception(f"Quota exceeded: {result.reason}")
```

## Components

### QuotaService
Main service for quota management and checking.

### CostTracker
Real-time cost tracking with Redis backend.

### RateLimitManager
Per-user and per-tool rate limiting.

### QuotaAlertService
Alert system for quota exhaustion and warnings.

## Usage Examples

### Configure Tool Quota

```python
tool_quota = QuotaConfig(
    scope=QuotaScope.TOOL,
    identifier="createIssues",
    rate_limits=RateLimitConfig(
        requests_per_minute=10,  # Respect GitHub API limits
        requests_per_hour=100
    ),
    cost_quota=CostQuota(
        per_request_limit=1.0  # Max $1 per request
    )
)

quota_service.register_quota(tool_quota)
```

### Check Quota Usage

```python
usage = await quota_service.get_quota_usage(
    scope=QuotaScope.USER,
    identifier="user-123"
)

print(f"Cost today: ${usage.cost_today:.2f}")
print(f"Cost this month: ${usage.cost_this_month:.2f}")
print(f"Requests today: {usage.requests_today}")
```

### Setup Alerts

```python
from quota import QuotaAlertService

alert_service = QuotaAlertService(quota_service)

# Register custom alert handler
async def send_email_alert(alert):
    # Send email notification
    pass

alert_service.register_alert_handler(send_email_alert)

# Check for alerts
alerts = await alert_service.check_quota_alerts(
    scope=QuotaScope.USER,
    identifier="user-123"
)
```

## Integration with ToolExecutor

```python
from openapi_tools import ToolExecutor
from quota import QuotaService, QuotaScope

quota_service = QuotaService()

async def check_quota(tool_name: str, user_id: str, estimated_cost: float):
    result = await quota_service.check_quota(
        scope=QuotaScope.USER,
        identifier=user_id,
        estimated_cost=estimated_cost
    )
    if not result.allowed:
        raise Exception(result.reason)
    return result

executor = ToolExecutor(
    enableAuditLog=True,
    quotaChecker=check_quota
)
```

## License

MIT

