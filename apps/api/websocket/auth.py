"""
WebSocket authentication handlers.
"""
from typing import Optional
import logging

from auth.jwt import jwt_handler
from auth.models import TokenData, TokenType
from websocket.models import ConnectionErrorEvent, EventType, WebSocketEvent
from middleware.logging import logger as app_logger

logger = logging.getLogger(__name__)


class WebSocketAuthError(Exception):
    """WebSocket authentication error."""
    pass


class WebSocketAuthHandler:
    """Handles WebSocket authentication and token validation."""

    def __init__(self):
        self.jwt_handler = jwt_handler
        self.auth_header_name = "Authorization"

    def extract_token_from_auth_header(self, auth_header: Optional[str]) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Args:
            auth_header: Authorization header value

        Returns:
            Token string or None if not found or invalid format
        """
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def verify_connection_token(self, token: str) -> Optional[TokenData]:
        """
        Verify JWT token for WebSocket connection.

        Args:
            token: JWT token string

        Returns:
            TokenData if valid, None otherwise
        """
        try:
            token_data = self.jwt_handler.verify_token(token, TokenType.ACCESS)
            return token_data
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return None

    def extract_token_from_query_params(self, query_params: dict) -> Optional[str]:
        """
        Extract token from query parameters (fallback method).

        Args:
            query_params: Dictionary of query parameters

        Returns:
            Token string or None
        """
        return query_params.get("token")

    def authenticate_connection(
        self,
        auth_header: Optional[str] = None,
        query_params: Optional[dict] = None
    ) -> Optional[TokenData]:
        """
        Authenticate WebSocket connection from headers or query params.

        Args:
            auth_header: Authorization header value
            query_params: Query parameters dictionary

        Returns:
            TokenData if authentication successful, None otherwise
        """
        # Try Authorization header first
        token = None
        if auth_header:
            token = self.extract_token_from_auth_header(auth_header)

        # Fall back to query parameters
        if not token and query_params:
            token = self.extract_token_from_query_params(query_params)

        if not token:
            logger.warning("No token provided for WebSocket connection")
            return None

        return self.verify_connection_token(token)

    def create_error_event(
        self,
        error_code: str,
        error_message: str,
        connection_id: Optional[str] = None
    ) -> WebSocketEvent:
        """
        Create a connection error event.

        Args:
            error_code: Error code
            error_message: Error message
            connection_id: Optional connection ID

        Returns:
            WebSocketEvent with error details
        """
        error_data = ConnectionErrorEvent(
            connection_id=connection_id,
            error_code=error_code,
            error_message=error_message
        )

        return WebSocketEvent(
            type=EventType.CONNECTION_ERROR,
            data=error_data.dict()
        )


# Global instance
ws_auth_handler = WebSocketAuthHandler()
