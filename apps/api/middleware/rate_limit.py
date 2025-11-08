"""
Rate limiting middleware.
"""
from typing import Optional

from fastapi import FastAPI, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Prioritizes:
    1. User ID from authenticated request
    2. API key if present
    3. Client IP address

    Args:
        request: Incoming request

    Returns:
        str: Identifier for rate limiting
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Try to get API key from header
    api_key = request.headers.get(settings.api_key_header_name)
    if api_key:
        return f"apikey:{api_key[:16]}"  # Use prefix to avoid logging full key

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Create limiter instance
limiter = Limiter(
    key_func=get_identifier,
    storage_uri=settings.rate_limit_storage_url,
    enabled=settings.rate_limit_enabled,
    default_limits=[
        f"{settings.rate_limit_per_minute}/minute",
        f"{settings.rate_limit_per_hour}/hour",
    ],
    headers_enabled=True,  # Add rate limit headers to responses
)


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    if not settings.rate_limit_enabled:
        return

    # Add limiter to app state
    app.state.limiter = limiter

    # Register exception handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Export limiter for use in routes
__all__ = ["setup_rate_limiting", "limiter"]
