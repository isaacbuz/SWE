"""
Authentication endpoints for JWT tokens, OAuth, and API keys.
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, EmailStr

from auth import get_current_active_user, require_user, CurrentUser
from auth.jwt import jwt_handler, password_handler, api_key_handler
from auth.models import Token, TokenType, UserRole
from middleware import limiter
from services.users import user_service
from services.api_keys import api_key_service
from config import settings


router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response Models

class LoginRequest(BaseModel):
    """Login request with credentials."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class APIKeyCreateRequest(BaseModel):
    """API key creation request."""
    name: Optional[str] = Field(None, max_length=255)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response."""
    id: int
    key_prefix: str
    name: Optional[str]
    is_active: bool
    expires_at: Optional[str]
    last_used_at: Optional[str]
    created_at: str


class APIKeyWithSecret(BaseModel):
    """API key response with full secret (create only)."""
    id: int
    api_key: str  # Full key - only shown once!
    key_prefix: str
    name: Optional[str]
    expires_at: Optional[str]
    created_at: str


# Endpoints

@router.post(
    "/token",
    response_model=Token,
    summary="Obtain JWT access token"
)
@limiter.limit("10/minute")
async def login(credentials: LoginRequest) -> Token:
    """
    Authenticate user and return JWT tokens.
    
    - **email**: User email address
    - **password**: User password
    
    Returns access token and refresh token.
    """
    # Get user from database
    user_data = await user_service.get_user_by_email(credentials.email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not user_data.get("password_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not password_handler.verify_password(credentials.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Map database role to UserRole enum
    role_mapping = {
        "admin": UserRole.ADMIN,
        "manager": UserRole.USER,
        "user": UserRole.USER,
        "service": UserRole.AGENT
    }
    role = role_mapping.get(user_data.get("role", "user"), UserRole.USER)
    
    # Create tokens
    access_token = jwt_handler.create_access_token(
        user_id=str(user_data["id"]),
        email=user_data["email"],
        role=role,
        scopes=[]  # TODO: Load scopes from user permissions
    )
    
    refresh_token = jwt_handler.create_refresh_token(
        user_id=str(user_data["id"]),
        email=user_data["email"]
    )
    
    # Update last login
    await user_service.update_user_last_login(user_data["id"])
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token"
)
@limiter.limit("10/minute")
async def refresh_token(request: TokenRefreshRequest) -> Token:
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and refresh token.
    """
    # Verify refresh token
    token_data = jwt_handler.verify_token(request.refresh_token, TokenType.REFRESH)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user from database
    user_data = await user_service.get_user_by_id(int(token_data.sub))
    if not user_data or not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive"
        )
    
    # Map database role to UserRole enum
    role_mapping = {
        "admin": UserRole.ADMIN,
        "manager": UserRole.USER,
        "user": UserRole.USER,
        "service": UserRole.AGENT
    }
    role = role_mapping.get(user_data.get("role", "user"), UserRole.USER)
    
    # Create new tokens
    access_token = jwt_handler.create_access_token(
        user_id=str(user_data["id"]),
        email=user_data["email"],
        role=role,
        scopes=[]
    )
    
    refresh_token = jwt_handler.create_refresh_token(
        user_id=str(user_data["id"]),
        email=user_data["email"]
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user"
)
@limiter.limit("5/minute")
async def register(request: RegisterRequest) -> Token:
    """
    Register a new user account.
    
    - **username**: Unique username
    - **email**: Email address
    - **password**: Password (min 8 characters)
    - **full_name**: Optional full name
    
    Returns access token and refresh token.
    """
    # Hash password
    password_hash = password_handler.hash_password(request.password)
    
    # Create user
    try:
        user_data = await user_service.create_user(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            role="user"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )
    
    # Create tokens
    access_token = jwt_handler.create_access_token(
        user_id=str(user_data["id"]),
        email=user_data["email"],
        role=UserRole.USER,
        scopes=[]
    )
    
    refresh_token = jwt_handler.create_refresh_token(
        user_id=str(user_data["id"]),
        email=user_data["email"]
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post(
    "/github/login",
    summary="Initiate GitHub OAuth flow"
)
@limiter.limit("10/minute")
async def github_login() -> RedirectResponse:
    """
    Initiate GitHub OAuth authentication flow.
    
    Redirects user to GitHub for authorization.
    """
    # TODO: Implement GitHub OAuth flow
    # For now, return error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GitHub OAuth not yet implemented"
    )


@router.get(
    "/github/callback",
    summary="GitHub OAuth callback"
)
@limiter.limit("10/minute")
async def github_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
) -> RedirectResponse:
    """
    Handle GitHub OAuth callback.
    
    - **code**: Authorization code from GitHub
    - **state**: State parameter for CSRF protection
    
    Returns redirect to frontend with tokens.
    """
    # TODO: Implement GitHub OAuth callback
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GitHub OAuth callback not yet implemented"
    )


@router.post(
    "/api-keys",
    response_model=APIKeyWithSecret,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key"
)
@limiter.limit("10/minute")
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: CurrentUser = Depends(require_user)
) -> APIKeyWithSecret:
    """
    Create a new API key for programmatic access.
    
    - **name**: Optional name for the API key
    - **expires_in_days**: Optional expiration in days (1-365)
    
    Returns the full API key (shown only once!).
    """
    # Generate API key
    api_key = api_key_handler.generate_api_key()
    key_prefix = api_key_handler.extract_key_prefix(api_key)
    key_hash = api_key_handler.hash_api_key(api_key)
    
    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
    
    # Create API key in database
    key_data = await api_key_service.create_api_key(
        user_id=int(current_user.id),
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=request.name,
        expires_at=expires_at
    )
    
    return APIKeyWithSecret(
        id=key_data["id"],
        api_key=api_key,  # Full key - only shown once!
        key_prefix=key_data["key_prefix"],
        name=key_data.get("name"),
        expires_at=key_data.get("expires_at"),
        created_at=key_data["created_at"]
    )


@router.get(
    "/api-keys",
    response_model=List[APIKeyResponse],
    summary="List API keys"
)
@limiter.limit("30/minute")
async def list_api_keys(
    current_user: CurrentUser = Depends(require_user)
) -> List[APIKeyResponse]:
    """
    List all API keys for the current user.
    
    Returns list of API keys (without full secrets).
    """
    keys = await api_key_service.list_api_keys(int(current_user.id))
    
    return [
        APIKeyResponse(
            id=key["id"],
            key_prefix=key["key_prefix"],
            name=key.get("name"),
            is_active=key.get("is_active", True),
            expires_at=key.get("expires_at"),
            last_used_at=key.get("last_used_at"),
            created_at=key["created_at"]
        )
        for key in keys
    ]


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key"
)
@limiter.limit("10/minute")
async def revoke_api_key(
    key_id: int,
    current_user: CurrentUser = Depends(require_user)
) -> None:
    """
    Revoke an API key.
    
    - **key_id**: API key ID to revoke
    
    The key will be immediately invalidated.
    """
    await api_key_service.revoke_api_key(key_id, int(current_user.id))

