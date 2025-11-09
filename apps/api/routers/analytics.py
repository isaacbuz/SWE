"""
Analytics and metrics endpoints.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import get_current_active_user, require_user, CurrentUser
from middleware import limiter
from db.connection import get_db_pool
from db.analytics import AnalyticsService
from db.users import UsersService


router = APIRouter(prefix="/analytics", tags=["analytics"])


# Enums

class MetricType(str, Enum):
    """Metric type enumeration."""
    ISSUES_RESOLVED = "issues_resolved"
    PRS_REVIEWED = "prs_reviewed"
    AGENT_EXECUTIONS = "agent_executions"
    CODE_QUALITY_SCORE = "code_quality_score"
    RESPONSE_TIME = "response_time"


class TimeRange(str, Enum):
    """Time range for analytics."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


# Request/Response Models

class MetricValue(BaseModel):
    """Single metric value."""
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]] = None


class MetricSeries(BaseModel):
    """Time series metric data."""
    metric_type: MetricType
    time_range: TimeRange
    data: List[MetricValue]
    total: float
    average: float
    min: float
    max: float


class ProjectMetrics(BaseModel):
    """Project-level metrics."""
    project_id: UUID
    total_issues: int
    resolved_issues: int
    open_issues: int
    total_prs: int
    reviewed_prs: int
    total_agents: int
    active_agents: int
    avg_resolution_time_hours: Optional[float]
    avg_review_time_hours: Optional[float]
    code_quality_score: Optional[float]


class AgentMetrics(BaseModel):
    """Agent performance metrics."""
    agent_id: UUID
    executions: int
    successes: int
    failures: int
    avg_execution_time_minutes: float
    success_rate: float


class DashboardMetrics(BaseModel):
    """Dashboard overview metrics."""
    total_projects: int
    total_issues: int
    resolved_issues: int
    total_prs: int
    reviewed_prs: int
    active_agents: int
    recent_activity: List[Dict[str, Any]]


class PerformanceMetrics(BaseModel):
    """System performance metrics."""
    avg_response_time_ms: float
    requests_per_minute: float
    error_rate: float
    active_users: int
    database_connections: int
    cache_hit_rate: float


# Dependencies
async def get_analytics_service() -> AnalyticsService:
    """Get analytics database service"""
    pool = await get_db_pool()
    return AnalyticsService(pool)


async def get_users_service() -> UsersService:
    """Get users database service"""
    pool = await get_db_pool()
    return UsersService(pool)


# Endpoints

@router.get(
    "/dashboard",
    response_model=DashboardMetrics,
    summary="Get dashboard metrics"
)
@limiter.limit("30/minute")
async def get_dashboard_metrics(
    current_user: CurrentUser = Depends(require_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    users_service: UsersService = Depends(get_users_service)
) -> DashboardMetrics:
    """
    Get overview metrics for dashboard.

    Returns aggregated metrics across all user's projects.
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query aggregated metrics
    metrics = await analytics_service.get_dashboard_metrics(user_id)
    
    return DashboardMetrics(
        total_projects=metrics.get("total_projects", 0),
        total_issues=metrics.get("total_issues", 0),
        resolved_issues=metrics.get("resolved_issues", 0),
        total_prs=metrics.get("total_prs", 0),
        reviewed_prs=metrics.get("reviewed_prs", 0),
        active_agents=metrics.get("active_agents", 0),
        recent_activity=metrics.get("recent_activity", [])
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectMetrics,
    summary="Get project metrics"
)
@limiter.limit("30/minute")
async def get_project_metrics(
    project_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    users_service: UsersService = Depends(get_users_service)
) -> ProjectMetrics:
    """
    Get detailed metrics for a specific project.

    - **project_id**: Project UUID
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query project metrics
    metrics = await analytics_service.get_project_metrics(project_id, user_id)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    return ProjectMetrics(**metrics)


@router.get(
    "/agents/{agent_id}",
    response_model=AgentMetrics,
    summary="Get agent metrics"
)
@limiter.limit("30/minute")
async def get_agent_metrics(
    agent_id: UUID,
    current_user: CurrentUser = Depends(require_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    users_service: UsersService = Depends(get_users_service)
) -> AgentMetrics:
    """
    Get performance metrics for a specific agent.

    - **agent_id**: Agent UUID
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query agent metrics
    metrics = await analytics_service.get_agent_metrics(agent_id, user_id)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    return AgentMetrics(**metrics)


@router.get(
    "/timeseries/{metric_type}",
    response_model=MetricSeries,
    summary="Get time series metrics"
)
@limiter.limit("30/minute")
async def get_metric_timeseries(
    metric_type: MetricType,
    time_range: TimeRange = Query(TimeRange.WEEK, description="Time range"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    current_user: CurrentUser = Depends(require_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    users_service: UsersService = Depends(get_users_service)
) -> MetricSeries:
    """
    Get time series data for a specific metric.

    - **metric_type**: Type of metric to retrieve
    - **time_range**: Time range for data
    - **project_id**: Optional project filter
    """
    # Get user integer ID
    user_id = await users_service.get_user_id_by_uuid(current_user.id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query time series data
    data = await analytics_service.get_metric_series(
        user_id=user_id,
        metric_type=metric_type.value,
        time_range=time_range.value,
        project_id=project_id
    )
    
    # Calculate aggregates
    values = [item["value"] for item in data]
    total = sum(values)
    average = total / len(values) if values else 0.0
    min_val = min(values) if values else 0.0
    max_val = max(values) if values else 0.0
    
    return MetricSeries(
        metric_type=metric_type,
        time_range=time_range,
        data=[MetricValue(**item) for item in data],
        total=total,
        average=average,
        min=min_val,
        max=max_val
    )


@router.get(
    "/performance",
    response_model=PerformanceMetrics,
    summary="Get system performance metrics"
)
@limiter.limit("30/minute")
async def get_performance_metrics(
    current_user: CurrentUser = Depends(require_user)
) -> PerformanceMetrics:
    """
    Get system-level performance metrics.

    Requires admin role for detailed metrics.
    """
    # TODO: Check if user is admin for detailed metrics
    # TODO: Query performance metrics from monitoring system
    # TODO: Return performance metrics

    return PerformanceMetrics(
        avg_response_time_ms=0.0,
        requests_per_minute=0.0,
        error_rate=0.0,
        active_users=0,
        database_connections=0,
        cache_hit_rate=0.0
    )


@router.get(
    "/export",
    summary="Export analytics data"
)
@limiter.limit("5/minute")
async def export_analytics(
    format: str = Query("csv", pattern="^(csv|json)$"),
    metric_types: Optional[List[MetricType]] = Query(None, description="Metrics to export"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: CurrentUser = Depends(require_user)
) -> Dict[str, Any]:
    """
    Export analytics data in CSV or JSON format.

    - **format**: Export format (csv or json)
    - **metric_types**: Types of metrics to export
    - **project_id**: Optional project filter
    - **start_date**: Optional start date
    - **end_date**: Optional end date
    """
    # TODO: Query requested metrics from database
    # TODO: Apply filters
    # TODO: Format data based on requested format
    # TODO: Return export data or download link

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Analytics export not yet implemented"
    )


@router.post(
    "/events",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Record custom analytics event"
)
@limiter.limit("60/minute")
async def record_analytics_event(
    event_type: str = Field(..., min_length=1, max_length=100),
    event_data: Dict[str, Any] = Field(default_factory=dict),
    project_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_user)
) -> Dict[str, str]:
    """
    Record a custom analytics event.

    - **event_type**: Type/name of the event
    - **event_data**: Event metadata
    - **project_id**: Optional associated project
    """
    # TODO: Validate event data
    # TODO: Store event in analytics database
    # TODO: Update relevant metrics
    # TODO: Return acknowledgment

    return {"status": "accepted", "message": "Event recorded"}
