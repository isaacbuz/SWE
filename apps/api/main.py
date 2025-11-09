"""
FastAPI main application entry point.
"""
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
from middleware import setup_cors, setup_logging, setup_rate_limiting, logger
from database import (
    get_engine,
    get_session_factory,
    check_database_connectivity,
    close_database_connections,
)
from redis_client import (
    get_redis_client,
    check_redis_connectivity,
    close_redis_connections,
)
from routers import (
    projects_router,
    agents_router,
    issues_router,
    prs_router,
    analytics_router,
    skills_router,
    tools_router,
    metrics_router,
    cost_tracking_router,
    audit_router,
)
from websocket import init_websocket_server
from events import init_broadcaster


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting", environment=settings.environment)

    # Initialize WebSocket server
    ws_server = init_websocket_server()
    logger.info("websocket_server_initialized")

    # Initialize event broadcaster
    broadcaster = init_broadcaster()
    logger.info("event_broadcaster_initialized")

    # Initialize database connection pool
    try:
        engine = get_engine()
        session_factory = get_session_factory()
        logger.info("database_connection_pool_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise

    # Initialize Redis connection pool
    try:
        redis_client = get_redis_client()
        # Test connection
        await redis_client.ping()
        logger.info("redis_connection_pool_initialized")
    except Exception as e:
        logger.warning("redis_initialization_failed", error=str(e))
        # Redis is optional, continue without it

    # Run database migrations (if Alembic is configured)
    # Note: In production, migrations should be run separately before starting the app
    # import alembic.config
    # alembic_cfg = alembic.config.Config("alembic.ini")
    # from alembic import command
    # command.upgrade(alembic_cfg, "head")

    logger.info("application_started")

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Close database connections
    try:
        await close_database_connections()
        logger.info("database_connections_closed")
    except Exception as e:
        logger.error("database_shutdown_error", error=str(e))

    # Close Redis connections
    try:
        await close_redis_connections()
        logger.info("redis_connections_closed")
    except Exception as e:
        logger.warning("redis_shutdown_error", error=str(e))

    # Gracefully shutdown background tasks
    # Background tasks should be managed by the task queue system
    # If using Celery or similar, shutdown workers here

    # Flush logs and metrics
    # Logs are typically flushed automatically by the logging handler
    # Metrics should be flushed if using a metrics exporter

    logger.info("application_stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    **SWE Agent API** - AI-powered software engineering automation platform.

    ## Features

    * **Project Management** - Manage GitHub repositories and configurations
    * **Agent Orchestration** - Deploy and monitor AI agents for code tasks
    * **Issue Resolution** - Automated issue analysis and resolution
    * **PR Review** - Intelligent pull request review and feedback
    * **Analytics** - Comprehensive metrics and performance tracking

    ## Authentication

    This API uses JWT-based authentication. Obtain a token via:
    - OAuth 2.0 (GitHub)
    - API Key authentication (for programmatic access)

    Include the token in the `Authorization` header:
    ```
    Authorization: Bearer <your_token>
    ```

    Or use an API key in the header:
    ```
    X-API-Key: <your_api_key>
    ```
    """,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
    debug=settings.debug,
)


# Setup middleware (order matters!)
setup_logging(app)  # First: logging
setup_cors(app)  # Second: CORS
setup_rate_limiting(app)  # Third: rate limiting


# Custom exception handlers

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with structured error response.

    Args:
        request: Incoming request
        exc: HTTP exception

    Returns:
        JSONResponse: Structured error response
    """
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None)
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
                "request_id": getattr(request.state, "request_id", None)
            }
        },
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors.

    Args:
        request: Incoming request
        exc: Validation error

    Returns:
        JSONResponse: Structured validation error response
    """
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        body=exc.body,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None)
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation error",
                "type": "validation_error",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: Incoming request
        exc: Exception

    Returns:
        JSONResponse: Structured error response
    """
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None),
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error" if not settings.debug else str(exc),
                "type": "internal_error",
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


# Health check endpoint

@app.get(
    "/health",
    tags=["health"],
    summary="Health check endpoint",
    status_code=status.HTTP_200_OK
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for load balancers and monitoring.

    Returns application status and basic metrics.
    """
    # Check database connectivity
    db_healthy = await check_database_connectivity()
    
    # Check Redis connectivity
    redis_healthy = await check_redis_connectivity()
    
    # Determine overall health status
    overall_status = "healthy" if db_healthy else "degraded"

    return {
        "status": overall_status,
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {
            "database": "ok" if db_healthy else "error",
            "redis": "ok" if redis_healthy else "error",
        }
    }


@app.get(
    "/",
    tags=["root"],
    summary="API root",
    status_code=status.HTTP_200_OK
)
async def root() -> Dict[str, Any]:
    """
    API root endpoint.

    Returns API information and available endpoints.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": settings.docs_url,
        "redoc_url": settings.redoc_url,
        "openapi_url": settings.openapi_url,
    }


# Register routers with API prefix
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(agents_router, prefix=settings.api_prefix)
app.include_router(issues_router, prefix=settings.api_prefix)
app.include_router(prs_router, prefix=settings.api_prefix)
app.include_router(analytics_router, prefix=settings.api_prefix)
app.include_router(skills_router, prefix=settings.api_prefix)
app.include_router(tools_router, prefix=settings.api_prefix)
app.include_router(metrics_router)
app.include_router(cost_tracking_router)
app.include_router(audit_router)


# Mount WebSocket server
ws_server = init_websocket_server()
ws_asgi_app = ws_server.get_asgi_app()
app.mount("/ws", ws_asgi_app)


# Run application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
