"""
Authentication module.
"""
from auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_optional_user,
    require_admin,
    require_user,
    require_agent,
    RoleChecker,
    ScopeChecker,
    AuthenticationError,
    PermissionError,
)
from auth.jwt import jwt_handler, password_handler, api_key_handler
from auth.models import (
    User,
    CurrentUser,
    UserRole,
    Token,
    TokenData,
    APIKey,
    APIKeyWithSecret,
)

__all__ = [
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_admin",
    "require_user",
    "require_agent",
    "RoleChecker",
    "ScopeChecker",
    "AuthenticationError",
    "PermissionError",
    # Handlers
    "jwt_handler",
    "password_handler",
    "api_key_handler",
    # Models
    "User",
    "CurrentUser",
    "UserRole",
    "Token",
    "TokenData",
    "APIKey",
    "APIKeyWithSecret",
]
