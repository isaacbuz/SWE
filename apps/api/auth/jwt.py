"""
JWT token utilities for authentication.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings
from auth.models import TokenData, TokenType, UserRole


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTHandler:
    """JWT token handler."""

    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=settings.jwt_refresh_token_expire_days)

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        scopes: Optional[list] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User unique identifier
            email: User email
            role: User role
            scopes: Optional list of permission scopes

        Returns:
            str: Encoded JWT token
        """
        now = datetime.utcnow()
        expires_at = now + self.access_token_expire

        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "scopes": scopes or [],
            "token_type": TokenType.ACCESS.value,
            "exp": expires_at,
            "iat": now,
            "jti": str(uuid4())
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        email: str
    ) -> str:
        """
        Create JWT refresh token.

        Args:
            user_id: User unique identifier
            email: User email
            role: User role

        Returns:
            str: Encoded JWT refresh token
        """
        now = datetime.utcnow()
        expires_at = now + self.refresh_token_expire

        payload = {
            "sub": user_id,
            "email": email,
            "token_type": TokenType.REFRESH.value,
            "exp": expires_at,
            "iat": now,
            "jti": str(uuid4())
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, expected_type: TokenType = TokenType.ACCESS) -> Optional[TokenData]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string
            expected_type: Expected token type

        Returns:
            TokenData: Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            token_type = payload.get("token_type")
            if token_type != expected_type.value:
                return None

            # Extract token data
            token_data = TokenData(
                sub=payload.get("sub"),
                email=payload.get("email"),
                role=UserRole(payload.get("role")),
                scopes=payload.get("scopes", []),
                token_type=TokenType(token_type),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
                jti=payload.get("jti")
            )

            return token_data

        except JWTError:
            return None
        except ValueError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            str: New access token or None if refresh token invalid
        """
        token_data = self.verify_token(refresh_token, TokenType.REFRESH)
        if not token_data:
            return None

        return self.create_access_token(
            user_id=token_data.sub,
            email=token_data.email,
            role=token_data.role,
            scopes=token_data.scopes
        )


class PasswordHandler:
    """Password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password.

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            bool: True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)


class APIKeyHandler:
    """API key generation and validation."""

    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure API key.

        Returns:
            str: API key with prefix
        """
        random_part = secrets.token_urlsafe(settings.api_key_length)
        return f"{settings.api_key_prefix}{random_part}"

    @staticmethod
    def extract_key_prefix(api_key: str) -> str:
        """
        Extract prefix from API key for identification.

        Args:
            api_key: Full API key

        Returns:
            str: Key prefix (first 8 characters)
        """
        return api_key[:8] if len(api_key) >= 8 else api_key

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """
        Hash API key for storage.

        Args:
            api_key: Plain API key

        Returns:
            str: Hashed API key
        """
        return pwd_context.hash(api_key)

    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        """
        Verify API key against hash.

        Args:
            plain_key: Plain API key
            hashed_key: Hashed API key

        Returns:
            bool: True if key matches
        """
        return pwd_context.verify(plain_key, hashed_key)


# Global instances
jwt_handler = JWTHandler()
password_handler = PasswordHandler()
api_key_handler = APIKeyHandler()
