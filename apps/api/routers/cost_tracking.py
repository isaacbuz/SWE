"""
Cost Tracking API Endpoints
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from services.cost_tracking_service import get_cost_tracker, CostEntry, CostSummary

router = APIRouter(prefix="/api/v1/costs", tags=["cost-tracking"])


class CostEntryResponse(BaseModel):
    """Cost entry response"""
    timestamp: str
    service: str
    provider: Optional[str] = None
    model: Optional[str] = None
    operation: str
    cost_usd: float
    metadata: Optional[dict] = None


class CostSummaryResponse(BaseModel):
    """Cost summary response"""
    total_cost: float
    period: dict
    by_service: dict
    by_provider: dict
    by_model: dict
    count: int


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    days: int = Query(7, description="Number of days (if dates not provided)")
):
    """
    Get cost summary for a period
    
    Returns aggregated cost data by service, provider, and model.
    """
    cost_tracker = get_cost_tracker()

    if start_date and end_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

    summary = cost_tracker.get_cost_summary(start, end)
    return CostSummaryResponse(**summary.to_dict())


@router.get("/entries", response_model=list[CostEntryResponse])
async def get_cost_entries(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    service: Optional[str] = Query(None, description="Filter by service"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    limit: int = Query(100, description="Maximum number of entries")
):
    """
    Get cost entries
    
    Returns individual cost entries with optional filtering.
    """
    cost_tracker = get_cost_tracker()
    all_costs = cost_tracker.get_all_costs()

    # Filter by date range
    if start_date and end_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        all_costs = [
            entry for entry in all_costs
            if start <= entry.timestamp <= end
        ]

    # Filter by service
    if service:
        all_costs = [entry for entry in all_costs if entry.service == service]

    # Filter by provider
    if provider:
        all_costs = [entry for entry in all_costs if entry.provider == provider]

    # Sort by timestamp (newest first) and limit
    all_costs.sort(key=lambda x: x.timestamp, reverse=True)
    all_costs = all_costs[:limit]

    return [CostEntryResponse(**entry.to_dict()) for entry in all_costs]


@router.get("/pricing")
async def get_pricing():
    """
    Get current pricing configuration
    
    Returns the pricing table for all providers and models.
    """
    cost_tracker = get_cost_tracker()
    return cost_tracker.get_pricing()

