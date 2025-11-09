"""
Quota Alert Service
Alerts for quota exhaustion and threshold warnings
"""

import logging
from typing import Optional, List, Callable
from datetime import datetime
from .models import QuotaScope, QuotaUsage, CostQuota
from .quota_service import QuotaService


class QuotaAlertService:
    """
    Alert service for quota exhaustion and warnings
    
    Features:
    - Quota exhaustion alerts
    - Threshold warnings (80%, 90%, 95%)
    - Custom alert handlers
    - Integration with notification systems
    """
    
    def __init__(self, quota_service: QuotaService):
        self.quota_service = quota_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self._alert_handlers: List[Callable] = []
        self._alert_history: List[Dict] = []
    
    def register_alert_handler(self, handler: Callable) -> None:
        """Register an alert handler function"""
        self._alert_handlers.append(handler)
    
    async def check_quota_alerts(
        self,
        scope: QuotaScope,
        identifier: str
    ) -> List[Dict]:
        """
        Check for quota alerts and trigger handlers
        
        Returns:
            List of alert dictionaries
        """
        usage = await self.quota_service.get_quota_usage(scope, identifier)
        config = self.quota_service.get_quota_config(scope, identifier)
        
        if not config or not config.cost_quota:
            return []
        
        alerts = []
        
        # Check daily quota
        if config.cost_quota.daily_limit:
            daily_percent = (usage.cost_today / config.cost_quota.daily_limit) * 100
            
            if daily_percent >= 100:
                alert = {
                    "type": "quota_exhausted",
                    "scope": scope.value,
                    "identifier": identifier,
                    "quota_type": "daily",
                    "current": usage.cost_today,
                    "limit": config.cost_quota.daily_limit,
                    "percentage": daily_percent,
                    "timestamp": datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                await self._trigger_alert(alert)
            
            elif daily_percent >= 95:
                alert = {
                    "type": "quota_warning",
                    "scope": scope.value,
                    "identifier": identifier,
                    "quota_type": "daily",
                    "current": usage.cost_today,
                    "limit": config.cost_quota.daily_limit,
                    "percentage": daily_percent,
                    "threshold": 95,
                    "timestamp": datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                await self._trigger_alert(alert)
            
            elif daily_percent >= 90:
                alert = {
                    "type": "quota_warning",
                    "scope": scope.value,
                    "identifier": identifier,
                    "quota_type": "daily",
                    "current": usage.cost_today,
                    "limit": config.cost_quota.daily_limit,
                    "percentage": daily_percent,
                    "threshold": 90,
                    "timestamp": datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                await self._trigger_alert(alert)
            
            elif daily_percent >= 80:
                alert = {
                    "type": "quota_warning",
                    "scope": scope.value,
                    "identifier": identifier,
                    "quota_type": "daily",
                    "current": usage.cost_today,
                    "limit": config.cost_quota.daily_limit,
                    "percentage": daily_percent,
                    "threshold": 80,
                    "timestamp": datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                await self._trigger_alert(alert)
        
        # Check monthly quota
        if config.cost_quota.monthly_limit:
            monthly_percent = (usage.cost_this_month / config.cost_quota.monthly_limit) * 100
            
            if monthly_percent >= 100:
                alert = {
                    "type": "quota_exhausted",
                    "scope": scope.value,
                    "identifier": identifier,
                    "quota_type": "monthly",
                    "current": usage.cost_this_month,
                    "limit": config.cost_quota.monthly_limit,
                    "percentage": monthly_percent,
                    "timestamp": datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                await self._trigger_alert(alert)
            
            elif monthly_percent >= 95:
                alert = {
                    "type": "quota_warning",
                    "scope": scope.value,
                    "identifier": identifier,
                    "quota_type": "monthly",
                    "current": usage.cost_this_month,
                    "limit": config.cost_quota.monthly_limit,
                    "percentage": monthly_percent,
                    "threshold": 95,
                    "timestamp": datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                await self._trigger_alert(alert)
        
        return alerts
    
    async def _trigger_alert(self, alert: Dict) -> None:
        """Trigger alert handlers"""
        self._alert_history.append(alert)
        
        # Keep only last 1000 alerts
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-1000:]
        
        self.logger.warning(
            f"Quota alert: {alert['type']} for {alert['scope']}:{alert['identifier']} "
            f"({alert['percentage']:.1f}% of {alert['quota_type']} quota)"
        )
        
        # Call registered handlers
        for handler in self._alert_handlers:
            try:
                if callable(handler):
                    await handler(alert) if hasattr(handler, '__call__') else handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
    
    def get_alert_history(
        self,
        scope: Optional[QuotaScope] = None,
        identifier: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get alert history"""
        alerts = self._alert_history
        
        if scope:
            alerts = [a for a in alerts if a.get('scope') == scope.value]
        
        if identifier:
            alerts = [a for a in alerts if a.get('identifier') == identifier]
        
        return alerts[-limit:]

