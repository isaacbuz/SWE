"""
Cost Tracking Service

Tracks and calculates costs for LLM provider usage, tool execution, and infrastructure.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from services.metrics_service import get_metrics_service

# Default LLM provider pricing (per 1K tokens)
DEFAULT_PRICING = {
    'openai': {
        'gpt-4': {'prompt': 0.03, 'completion': 0.06},
        'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
        'gpt-3.5-turbo': {'prompt': 0.0015, 'completion': 0.002},
    },
    'anthropic': {
        'claude-3-opus': {'prompt': 0.015, 'completion': 0.075},
        'claude-3-sonnet': {'prompt': 0.003, 'completion': 0.015},
        'claude-3-haiku': {'prompt': 0.00025, 'completion': 0.00125},
    },
    'google': {
        'gemini-pro': {'prompt': 0.0005, 'completion': 0.0015},
        'gemini-ultra': {'prompt': 0.0025, 'completion': 0.01},
    },
    'mistral': {
        'mistral-large': {'prompt': 0.002, 'completion': 0.006},
        'mistral-medium': {'prompt': 0.0007, 'completion': 0.0021},
        'mistral-small': {'prompt': 0.0002, 'completion': 0.0006},
    },
    'cohere': {
        'command': {'prompt': 0.0015, 'completion': 0.002},
        'command-light': {'prompt': 0.0003, 'completion': 0.0006},
    },
    'ibm': {
        'granite-13b-chat': {'prompt': 0.0005, 'completion': 0.0005},
        'granite-8b-chat': {'prompt': 0.0003, 'completion': 0.0003},
    },
}


@dataclass
class CostEntry:
    """Cost entry"""
    timestamp: datetime
    service: str
    provider: Optional[str] = None
    model: Optional[str] = None
    operation: str = 'completion'
    cost_usd: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class CostSummary:
    """Cost summary"""
    total_cost: float
    period_start: datetime
    period_end: datetime
    by_service: Dict[str, float]
    by_provider: Dict[str, float]
    by_model: Dict[str, float]
    count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_cost': self.total_cost,
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat(),
            },
            'by_service': self.by_service,
            'by_provider': self.by_provider,
            'by_model': self.by_model,
            'count': self.count,
        }


class CostTrackingService:
    """Cost tracking service"""

    def __init__(self, custom_pricing: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None):
        self.costs: List[CostEntry] = []
        self.pricing = {**DEFAULT_PRICING, **(custom_pricing or {})}
        self.metrics = get_metrics_service()

    def calculate_llm_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate LLM provider cost"""
        provider_pricing = self.pricing.get(provider.lower())
        if not provider_pricing:
            return 0.0

        model_pricing = provider_pricing.get(model.lower())
        if not model_pricing:
            return 0.0

        prompt_cost = (prompt_tokens / 1000) * model_pricing['prompt']
        completion_cost = (completion_tokens / 1000) * model_pricing['completion']

        return prompt_cost + completion_cost

    def record_llm_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostEntry:
        """Record LLM provider cost"""
        cost = self.calculate_llm_cost(provider, model, prompt_tokens, completion_tokens)

        entry = CostEntry(
            timestamp=datetime.utcnow(),
            service='llm-provider',
            provider=provider,
            model=model,
            operation='completion',
            cost_usd=cost,
            metadata={
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                **(metadata or {}),
            }
        )

        self.costs.append(entry)

        # Record in Prometheus metrics
        self.metrics.record_llm_request(
            provider=provider,
            model=model,
            status='success',
            latency_seconds=0.0,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost
        )

        return entry

    def record_tool_cost(
        self,
        tool_name: str,
        cost_usd: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostEntry:
        """Record tool execution cost"""
        entry = CostEntry(
            timestamp=datetime.utcnow(),
            service='tool-execution',
            operation=tool_name,
            cost_usd=cost_usd,
            metadata=metadata,
        )

        self.costs.append(entry)
        return entry

    def record_infrastructure_cost(
        self,
        service: str,
        cost_usd: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostEntry:
        """Record infrastructure cost"""
        entry = CostEntry(
            timestamp=datetime.utcnow(),
            service=service,
            operation='infrastructure',
            cost_usd=cost_usd,
            metadata=metadata,
        )

        self.costs.append(entry)
        return entry

    def get_cost_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CostSummary:
        """Get cost summary for a period"""
        filtered = [
            entry for entry in self.costs
            if start_date <= entry.timestamp <= end_date
        ]

        total_cost = sum(entry.cost_usd for entry in filtered)

        by_service: Dict[str, float] = {}
        by_provider: Dict[str, float] = {}
        by_model: Dict[str, float] = {}

        for entry in filtered:
            by_service[entry.service] = by_service.get(entry.service, 0) + entry.cost_usd

            if entry.provider:
                by_provider[entry.provider] = by_provider.get(entry.provider, 0) + entry.cost_usd

            if entry.model:
                by_model[entry.model] = by_model.get(entry.model, 0) + entry.cost_usd

        return CostSummary(
            total_cost=total_cost,
            period_start=start_date,
            period_end=end_date,
            by_service=by_service,
            by_provider=by_provider,
            by_model=by_model,
            count=len(filtered),
        )

    def get_all_costs(self) -> List[CostEntry]:
        """Get all costs"""
        return self.costs.copy()

    def clear(self):
        """Clear costs (useful for testing)"""
        self.costs.clear()

    def get_pricing(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Get current pricing"""
        return self.pricing.copy()

    def update_pricing(self, provider: str, pricing: Dict[str, Dict[str, float]]):
        """Update pricing"""
        self.pricing[provider.lower()] = pricing


# Singleton instance
_cost_tracker: Optional[CostTrackingService] = None


def get_cost_tracker() -> CostTrackingService:
    """Get cost tracker singleton"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTrackingService()
    return _cost_tracker

