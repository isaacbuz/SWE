"""
Authentication dependencies for FastAPI routes.
"""
from typing import Optional, List
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from auth.jwt import jwt_handler, api_key_handler
from auth.models import CurrentUser, UserRole, TokenType


# Security schemes
http_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name=settings.api_key_header_name, auto_error=False)


class AuthenticationError(HTTPException):
    """Authentication error exception."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionError(HTTPException):
    """Permission denied exception."""

    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Optional[CurrentUser]:
    """
    Get current user from JWT token.

    Args:
        credentials: HTTP bearer credentials

    Returns:
        CurrentUser: Current user or None if no valid token

    Raises:
        AuthenticationError: If token is invalid
    """
    if not credentials:
        return None

    token = credentials.credentials
    token_data = jwt_handler.verify_token(token, TokenType.ACCESS)

    if not token_data:
        raise AuthenticationError("Invalid or expired token")

    # TODO: Check if token is revoked in Redis
    # TODO: Load user from database to verify it still exists and is active

    return CurrentUser(
        id=UUID(token_data.sub),
        email=token_data.email,
        role=token_data.role,
        scopes=token_data.scopes
    )


async def get_current_user_from_api_key(
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[CurrentUser]:
    """
    Get current user from API key.

    Args:
        api_key: API key from header

    Returns:
        CurrentUser: Current user or None if no valid API key

    Raises:
        AuthenticationError: If API key is invalid
    """
    if not api_key:
        return None

    # TODO: Load API key from database by prefix
    # TODO: Verify hashed key matches
    # TODO: Check if key is expired or inactive
    # TODO: Update last_used_at timestamp
    # TODO: Load associated user

    # For now, return None (API key auth not fully implemented)
    return None


async def get_current_user(
    token_user: Optional[CurrentUser] = Depends(get_current_user_from_token),
    api_key_user: Optional[CurrentUser] = Depends(get_current_user_from_api_key)
) -> CurrentUser:
    """
    Get current authenticated user from either JWT token or API key.

    Args:
        token_user: User from JWT token
        api_key_user: User from API key

    Returns:
        CurrentUser: Current authenticated user

    Raises:
        AuthenticationError: If no valid authentication provided
    """
    user = token_user or api_key_user

    if not user:
        raise AuthenticationError()

    return user


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Get current active user.

    Args:
        current_user: Current user

    Returns:
        CurrentUser: Current active user

    Raises:
        AuthenticationError: If user is inactive
    """
    # TODO: Verify user is active in database
    return current_user


class RoleChecker:
    """Dependency for checking user roles."""

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
        """
        Check if user has required role.

        Args:
            current_user: Current user

        Returns:
            CurrentUser: Current user if authorized

        Raises:
            PermissionError: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            raise PermissionError(
                f"User role '{current_user.role}' not authorized. Required: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


class ScopeChecker:
    """Dependency for checking user scopes."""

    def __init__(self, required_scopes: List[str]):
        self.required_scopes = required_scopes

    def __call__(self, current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
        """
        Check if user has required scopes.

        Args:
            current_user: Current user

        Returns:
            CurrentUser: Current user if authorized

        Raises:
            PermissionError: If user doesn't have required scopes
        """
        user_scopes = set(current_user.scopes)
        required_scopes = set(self.required_scopes)

        if not required_scopes.issubset(user_scopes):
            missing_scopes = required_scopes - user_scopes
            raise PermissionError(f"Missing required scopes: {list(missing_scopes)}")

        return current_user


# Common role dependencies
require_admin = RoleChecker([UserRole.ADMIN])
require_user = RoleChecker([UserRole.ADMIN, UserRole.USER])
require_agent = RoleChecker([UserRole.ADMIN, UserRole.AGENT])


# Optional authentication (user may be None)
async def get_optional_user(
    token_user: Optional[CurrentUser] = Depends(get_current_user_from_token),
    api_key_user: Optional[CurrentUser] = Depends(get_current_user_from_api_key)
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, None otherwise.

    Args:
        token_user: User from JWT token
        api_key_user: User from API key

    Returns:
        Optional[CurrentUser]: Current user or None
    """
    return token_user or api_key_user


# Import settings for api_key_header
from config import settings
