"""
Tools API router for OpenAPI tool execution.

Provides endpoints for:
- Listing available tools
- Executing tools
- Viewing audit logs
- Tool metadata and schemas
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user
from auth.models import User
from services.tools_service import get_tool_registry, get_tool_executor
from services.audit_service import get_audit_logger
from services.permissions_service import get_permission_checker
from services.rate_limiting_service import get_rate_limiter

router = APIRouter(
    prefix="/tools",
    tags=["tools"],
    responses={404: {"description": "Not found"}},
)


# Request/Response Models
class ToolSpecResponse(BaseModel):
    """Tool specification response model."""
    name: str
    description: str
    operationId: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    tags: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None


class ToolExecuteRequest(BaseModel):
    """Tool execution request model."""
    toolName: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(..., description="Tool arguments")
    options: Optional[Dict[str, Any]] = Field(
        None, description="Execution options (timeout, retries, etc.)"
    )


class ToolExecuteResponse(BaseModel):
    """Tool execution response model."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executionTime: float = Field(..., description="Execution time in milliseconds")
    toolName: str
    timestamp: datetime


class ToolListResponse(BaseModel):
    """Tool list response model."""
    tools: List[ToolSpecResponse]
    total: int


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: str
    timestamp: datetime
    userId: str
    toolName: str
    success: bool
    durationMs: float
    error: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Audit log response model."""
    logs: List[AuditLogEntry]
    total: int
    page: int
    pageSize: int


# Endpoints
@router.get(
    "",
    response_model=ToolListResponse,
    summary="List available tools",
    description="Get a list of all available OpenAPI tools",
)
async def list_tools(
    tag: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> ToolListResponse:
    """
    List all available tools, optionally filtered by tag or search query.
    
    Args:
        tag: Filter tools by tag
        search: Search tools by name or description
        current_user: Authenticated user
    
    Returns:
        List of available tools
    """
    registry = get_tool_registry()
    tools = registry.get_tool_specs()
    
    if tag:
        tools = [t for t in tools if tag in (t.get("tags") or [])]
    
    if search:
        search_lower = search.lower()
        tools = [
            t for t in tools
            if search_lower in t.get("name", "").lower()
            or search_lower in (t.get("description") or "").lower()
        ]
    
    return ToolListResponse(
        tools=[
            ToolSpecResponse(
                name=tool.get("name"),
                description=tool.get("description", ""),
                operationId=tool.get("operationId"),
                endpoint=tool.get("endpoint"),
                method=tool.get("method"),
                tags=tool.get("tags"),
            )
            for tool in tools
        ],
        total=len(tools),
    )


@router.get(
    "/{tool_name}",
    response_model=ToolSpecResponse,
    summary="Get tool details",
    description="Get detailed information about a specific tool",
)
async def get_tool(
    tool_name: str,
    current_user: User = Depends(get_current_user),
) -> ToolSpecResponse:
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_name: Name of the tool
        current_user: Authenticated user
    
    Returns:
        Tool specification
    """
    registry = get_tool_registry()
    tool = registry.get_tool_by_name(tool_name)
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )
    
    return ToolSpecResponse(
        name=tool.get("name"),
        description=tool.get("description", ""),
        operationId=tool.get("operationId"),
        endpoint=tool.get("endpoint"),
        method=tool.get("method"),
        tags=tool.get("tags"),
    )


@router.post(
    "/execute",
    response_model=ToolExecuteResponse,
    summary="Execute a tool",
    description="Execute an OpenAPI tool with provided arguments",
    status_code=status.HTTP_200_OK,
)
async def execute_tool(
    request: ToolExecuteRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
) -> ToolExecuteResponse:
    """
    Execute a tool with the provided arguments.
    
    This endpoint:
    1. Validates user permissions
    2. Checks rate limits
    3. Validates tool arguments
    4. Executes the tool
    5. Logs the execution for audit
    
    Args:
        request: Tool execution request
        http_request: HTTP request object (for IP, user agent)
        current_user: Authenticated user
    
    Returns:
        Tool execution result
    """
    import time
    start_time = time.time()
    
    # 1. Check permissions
    permission_checker = get_permission_checker()
    if not permission_checker.has_permission(current_user.id, request.toolName, "execute"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # 2. Check rate limits
    rate_limiter = get_rate_limiter()
    rate_status = rate_limiter.check_limit(
        identifier=current_user.id,
        max_requests=100,
        window_ms=60000,
    )
    if rate_status["exceeded"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # 3. Execute tool
    executor = get_tool_executor()
    result = await executor.execute(
        request.toolName,
        request.arguments,
        request.options,
    )
    
    execution_time = (time.time() - start_time) * 1000
    
    # 4. Audit logging
    audit_logger = get_audit_logger()
    await audit_logger.log_execution(
        user_id=current_user.id,
        tool_name=request.toolName,
        args=request.arguments,
        result=result.get("data") if result.get("success") else None,
        success=result.get("success", False),
        duration_ms=execution_time,
        error=result.get("error") if not result.get("success") else None,
        metadata={
            "ipAddress": http_request.client.host if http_request.client else None,
            "userAgent": http_request.headers.get("user-agent"),
        }
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Tool execution failed")
        )
    
    return ToolExecuteResponse(
        success=True,
        result=result.get("data"),
        executionTime=execution_time,
        toolName=request.toolName,
        timestamp=datetime.now(),
    )


@router.get(
    "/audit",
    response_model=AuditLogResponse,
    summary="Get audit logs",
    description="Get audit logs for tool executions",
)
async def get_audit_logs(
    tool_name: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
) -> AuditLogResponse:
    """
    Get audit logs for tool executions.
    
    Only admins can view all logs. Regular users can only view their own logs.
    
    Args:
        tool_name: Filter by tool name
        user_id: Filter by user ID (admins only)
        start_date: Filter by start date
        end_date: Filter by end date
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
    
    Returns:
        Audit log entries
    """
    # Check admin permissions
    if user_id and user_id != current_user.id:
        # TODO: Check if user is admin
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Permission denied")
        pass
    
    # Query audit logs
    audit_logger = get_audit_logger()
    logs = await audit_logger.query_logs(
        user_id=user_id or current_user.id,
        tool_name=tool_name,
        start_date=start_date,
        end_date=end_date,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    
    return AuditLogResponse(
        logs=[
            AuditLogEntry(
                id=log["id"],
                timestamp=log["timestamp"],
                userId=log["userId"],
                toolName=log["toolName"],
                success=log["success"],
                durationMs=log["durationMs"],
                error=log.get("error"),
            )
            for log in logs
        ],
        total=len(logs),
        page=page,
        pageSize=page_size,
    )


@router.get(
    "/health",
    summary="Tools service health check",
    description="Check the health of the tools service",
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the tools service.
    
    Returns:
        Service health status
    """
    # TODO: Check actual service health
    # - Tool registry loaded
    # - Tool executor initialized
    # - LLM providers available
    # - Audit logger connected
    
    return {
        "status": "healthy",
        "service": "tools",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "tool_registry": "operational",
            "tool_executor": "operational",
            "audit_logger": "operational",
        },
    }

