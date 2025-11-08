"""
Authentication models and schemas.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    READONLY = "readonly"


class TokenType(str, Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"


# Request Models

class TokenRequest(BaseModel):
    """OAuth token request."""
    grant_type: str = Field(..., pattern="^(authorization_code|refresh_token)$")
    code: Optional[str] = None
    refresh_token: Optional[str] = None
    redirect_uri: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class APIKeyCreateRequest(BaseModel):
    """API key creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)


# Response Models

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    sub: str  # User ID
    email: Optional[str] = None
    role: UserRole
    scopes: List[str] = Field(default_factory=list)
    token_type: TokenType
    exp: datetime
    iat: datetime
    jti: Optional[str] = None  # JWT ID for revocation


class User(BaseModel):
    """User model."""
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class APIKey(BaseModel):
    """API key model."""
    id: UUID
    user_id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKey):
    """API key with full secret (only returned on creation)."""
    key: str


class OAuthState(BaseModel):
    """OAuth state for CSRF protection."""
    state: str
    redirect_uri: str
    created_at: datetime


class GitHubUser(BaseModel):
    """GitHub user information."""
    id: int
    login: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class CurrentUser(BaseModel):
    """Current authenticated user."""
    id: UUID
    email: EmailStr
    role: UserRole
    scopes: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
