"""
Audit Logging API Endpoints
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from services.audit_service import get_audit_logger, AuditLogEntry
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


class AuditLogEntryResponse(BaseModel):
    """Audit log entry response"""
    id: str
    timestamp: str
    event_type: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    result: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[dict] = None
    changes: Optional[dict] = None


class AuditLogQueryResponse(BaseModel):
    """Audit log query response"""
    entries: list[AuditLogEntryResponse]
    total: int
    limit: int
    offset: int


@router.get("/logs", response_model=AuditLogQueryResponse)
async def query_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    result: Optional[str] = Query(None, description="Filter by result (success/failure/pending)"),
    limit: int = Query(100, description="Maximum number of entries", le=1000),
    offset: int = Query(0, description="Offset for pagination"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Query audit logs
    
    Requires authentication. Returns audit log entries matching the filters.
    """
    audit_logger = get_audit_logger()
    
    # Parse dates
    start = None
    end = None
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    # Query logs
    entries = await audit_logger.query(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start,
        end_date=end,
        result=result,
        limit=limit,
        offset=offset
    )
    
    return AuditLogQueryResponse(
        entries=[AuditLogEntryResponse(**entry.to_dict()) for entry in entries],
        total=len(entries),
        limit=limit,
        offset=offset
    )


@router.get("/logs/{log_id}", response_model=AuditLogEntryResponse)
async def get_audit_log(
    log_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get audit log by ID
    
    Requires authentication.
    """
    audit_logger = get_audit_logger()
    entry = await audit_logger.get_by_id(log_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return AuditLogEntryResponse(**entry.to_dict())


@router.get("/summary")
async def get_audit_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    days: int = Query(7, description="Number of days (if dates not provided)"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get audit log summary
    
    Returns aggregated statistics for audit logs.
    """
    audit_logger = get_audit_logger()
    
    # Parse dates
    if start_date and end_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
    
    # Query all logs in period
    entries = await audit_logger.query(
        start_date=start,
        end_date=end,
        limit=10000  # Get all for summary
    )
    
    # Calculate statistics
    total_events = len(entries)
    by_event_type: dict[str, int] = {}
    by_result: dict[str, int] = {}
    by_user: dict[str, int] = {}
    by_resource_type: dict[str, int] = {}
    
    for entry in entries:
        by_event_type[entry.event_type] = by_event_type.get(entry.event_type, 0) + 1
        by_result[entry.result] = by_result.get(entry.result, 0) + 1
        
        if entry.user_id:
            by_user[entry.user_id] = by_user.get(entry.user_id, 0) + 1
        
        if entry.resource_type:
            by_resource_type[entry.resource_type] = by_resource_type.get(entry.resource_type, 0) + 1
    
    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "total_events": total_events,
        "by_event_type": by_event_type,
        "by_result": by_result,
        "by_user": by_user,
        "by_resource_type": by_resource_type,
    }

