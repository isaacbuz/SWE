"""
Socket.IO server implementation for real-time updates.
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID

import socketio
from socketio import AsyncServer, ASGIApp
from socketio.exceptions import DisconnectedError

from config import settings
from auth.models import TokenData
from websocket.auth import ws_auth_handler
from websocket.events import get_event_handler
from middleware.logging import logger as app_logger

logger = logging.getLogger(__name__)


def _auth_handler(auth: Optional[Dict[str, Any]]) -> Optional[TokenData]:
    """
    Authenticate WebSocket connection via auth data.

    Args:
        auth: Auth dictionary passed by client

    Returns:
        TokenData if authenticated, None otherwise
    """
    if not auth:
        return None

    token = auth.get("token")
    if not token:
        return None

    return ws_auth_handler.verify_connection_token(token)


class WebSocketServer:
    """Socket.IO WebSocket server wrapper."""

    def __init__(self):
        """Initialize WebSocket server."""
        # Create async server with Redis adapter for scaling
        self.sio = AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=settings.cors_origins,
            cors_credentials=True,
            ping_timeout=60,
            ping_interval=25,
            max_http_buffer_size=1e6,  # 1MB
            logger=False,  # Use custom logger
            engineio_logger=False,
        )

        # Configure message queue with Redis for horizontal scaling
        self._setup_redis_adapter()

        # Get event handler
        self.event_handler = get_event_handler(self.sio)

        # Register event handlers
        self._register_handlers()

        logger.info("WebSocket server initialized")

    def _setup_redis_adapter(self) -> None:
        """
        Set up Redis adapter for horizontal scaling.

        Allows multiple instances to communicate via shared rooms.
        """
        try:
            import redis.asyncio as aioredis
            from socketio import AsyncRedisManager

            # Parse Redis URL
            redis_url = settings.redis_url
            mgr = AsyncRedisManager(redis_url)

            self.sio.attach(mgr)
            logger.info("Redis adapter configured for Socket.IO")

        except ImportError:
            logger.warning("Redis not available, using in-memory manager")
        except Exception as e:
            logger.error(f"Failed to setup Redis adapter: {str(e)}")

    def _register_handlers(self) -> None:
        """Register event handlers with Socket.IO."""

        @self.sio.on("connect", namespace="/ws")
        async def on_connect(sid: str, environ: Dict, auth: Optional[Dict]) -> bool:
            """Handle new connection."""
            token_data = _auth_handler(auth)
            return await self.event_handler.handle_connect(sid, environ, token_data)

        @self.sio.on("disconnect", namespace="/ws")
        async def on_disconnect(sid: str) -> None:
            """Handle disconnection."""
            await self.event_handler.handle_disconnect(sid)

        @self.sio.on("subscribe", namespace="/ws")
        async def on_subscribe(sid: str, data: Dict) -> Dict:
            """Handle subscription request."""
            # Get auth from stored session data
            auth = await self._get_session_auth(sid)
            return await self.event_handler.handle_subscribe(sid, data, auth)

        @self.sio.on("unsubscribe", namespace="/ws")
        async def on_unsubscribe(sid: str, data: Dict) -> Dict:
            """Handle unsubscription request."""
            auth = await self._get_session_auth(sid)
            return await self.event_handler.handle_unsubscribe(sid, data, auth)

        @self.sio.on("ping", namespace="/ws")
        async def on_ping(sid: str, data: Dict) -> Dict:
            """Handle ping/heartbeat."""
            return await self.event_handler.handle_ping(sid, data)

        logger.debug("Event handlers registered")

    async def _get_session_auth(self, sid: str) -> Optional[TokenData]:
        """
        Get authentication data from session.

        Args:
            sid: Session ID

        Returns:
            TokenData if available, None otherwise
        """
        try:
            # In a real implementation, retrieve from session store
            # For now, we'll rely on initial auth passed during connect
            return None
        except Exception as e:
            logger.error(f"Error getting session auth: {str(e)}")
            return None

    async def emit_to_room(
        self,
        room: str,
        event: str,
        data: Dict[str, Any],
        skip_sid: Optional[str] = None,
        namespace: str = "/ws"
    ) -> None:
        """
        Emit event to all members in a room.

        Args:
            room: Room name
            event: Event name
            data: Event data
            skip_sid: Optional SID to skip (e.g., sender)
            namespace: Socket.IO namespace
        """
        try:
            if skip_sid:
                # Emit to all except sender
                for sid in self.sio.rooms(namespace).get(room, []):
                    if sid != skip_sid:
                        await self.sio.emit(event, data, to=sid, namespace=namespace)
            else:
                # Emit to entire room
                await self.sio.emit(event, data, room=room, namespace=namespace)

            logger.debug(f"Emitted {event} to room {room}")

        except Exception as e:
            logger.error(f"Error emitting to room {room}: {str(e)}")

    async def emit_to_user(
        self,
        user_id: UUID,
        event: str,
        data: Dict[str, Any],
        namespace: str = "/ws"
    ) -> None:
        """
        Emit event to all connections of a specific user.

        Args:
            user_id: User ID
            event: Event name
            data: Event data
            namespace: Socket.IO namespace
        """
        user_room = f"user:{user_id}"
        await self.emit_to_room(user_room, event, data, namespace=namespace)

    async def emit_to_sid(
        self,
        sid: str,
        event: str,
        data: Dict[str, Any],
        namespace: str = "/ws"
    ) -> None:
        """
        Emit event to specific connection.

        Args:
            sid: Session ID
            event: Event name
            data: Event data
            namespace: Socket.IO namespace
        """
        try:
            await self.sio.emit(event, data, to=sid, namespace=namespace)
            logger.debug(f"Emitted {event} to connection {sid}")
        except DisconnectedError:
            logger.debug(f"Connection {sid} already disconnected")
        except Exception as e:
            logger.error(f"Error emitting to connection {sid}: {str(e)}")

    async def get_room_info(self, room: str, namespace: str = "/ws") -> Dict[str, Any]:
        """
        Get information about a room.

        Args:
            room: Room name
            namespace: Socket.IO namespace

        Returns:
            Dictionary with room info
        """
        try:
            sids = self.sio.rooms(namespace).get(room, [])
            return {
                "room": room,
                "member_count": len(sids),
                "members": list(sids)
            }
        except Exception as e:
            logger.error(f"Error getting room info: {str(e)}")
            return {"room": room, "member_count": 0, "error": str(e)}

    def get_asgi_app(self) -> ASGIApp:
        """
        Get ASGI app for mounting on FastAPI.

        Returns:
            Socket.IO ASGI application
        """
        return ASGIApp(self.sio)


# Global WebSocket server instance
_ws_server: Optional[WebSocketServer] = None


def get_sio() -> AsyncServer:
    """
    Get Socket.IO server instance.

    Returns:
        AsyncServer instance
    """
    global _ws_server
    if _ws_server is None:
        _ws_server = WebSocketServer()
    return _ws_server.sio


def init_websocket_server() -> WebSocketServer:
    """
    Initialize and return WebSocket server.

    Returns:
        WebSocketServer instance
    """
    global _ws_server
    if _ws_server is None:
        _ws_server = WebSocketServer()
    return _ws_server
