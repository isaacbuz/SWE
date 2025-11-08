"""
WebSocket event handlers and processing.
"""
import logging
from typing import Optional, Any, Dict
from uuid import UUID

import socketio

from auth.models import TokenData
from websocket.models import (
    EventType,
    WebSocketEvent,
    ConnectionEstablishedEvent,
)
from websocket.rooms import room_manager, subscription_manager
from middleware.logging import logger as app_logger

logger = logging.getLogger(__name__)


class WebSocketEventHandler:
    """Handles WebSocket events and messages."""

    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.room_manager = room_manager
        self.subscription_manager = subscription_manager

    async def handle_connect(
        self,
        sid: str,
        environ: Dict[str, Any],
        auth: Optional[TokenData] = None
    ) -> bool:
        """
        Handle client connection.

        Args:
            sid: Session ID
            environ: ASGI environ dictionary
            auth: Authenticated token data

        Returns:
            True to accept connection, False to reject
        """
        if not auth:
            logger.warning(f"Connection attempt without authentication: {sid}")
            return False

        try:
            user_id = auth.sub
            app_logger.info(
                "websocket_connect",
                connection_id=sid,
                user_id=user_id,
                email=auth.email
            )

            # Register connection
            self.subscription_manager.register_connection(sid, user_id)

            # Auto-subscribe to user's personal room
            user_room = self.room_manager.get_user_room(UUID(user_id))
            await self.sio.enter_room(sid, user_room)
            self.room_manager.add_member_to_room(user_room, sid)

            # Auto-subscribe to global room
            global_room = self.room_manager.get_global_room()
            await self.sio.enter_room(sid, global_room)
            self.room_manager.add_member_to_room(global_room, sid)

            # Send connection established event
            connection_event = WebSocketEvent(
                type=EventType.CONNECTION_ESTABLISHED,
                data=ConnectionEstablishedEvent(
                    connection_id=sid,
                    user_id=UUID(user_id)
                ).dict()
            )

            await self.sio.emit("connection_established", connection_event.dict(), to=sid)

            logger.info(f"Connection established: {sid} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error handling connection: {str(e)}", exc_info=True)
            return False

    async def handle_disconnect(self, sid: str) -> None:
        """
        Handle client disconnection.

        Args:
            sid: Session ID
        """
        try:
            # Get user ID before unregistering
            user_id = None
            for cid, uid in self.subscription_manager.connection_to_user.items():
                if cid == sid:
                    user_id = uid
                    break

            # Remove from all rooms
            removed_from = self.room_manager.remove_member_from_all_rooms(sid)

            # Unregister connection
            self.subscription_manager.unregister_connection(sid)

            app_logger.info(
                "websocket_disconnect",
                connection_id=sid,
                user_id=user_id,
                rooms_count=len(removed_from)
            )

            logger.info(f"Connection closed: {sid}")

        except Exception as e:
            logger.error(f"Error handling disconnection: {str(e)}", exc_info=True)

    async def handle_subscribe(
        self,
        sid: str,
        data: Dict[str, Any],
        auth: Optional[TokenData] = None
    ) -> Dict[str, Any]:
        """
        Handle room subscription request.

        Args:
            sid: Session ID
            data: Subscription data {room: str}
            auth: Authenticated token data

        Returns:
            Response dictionary with status
        """
        if not auth:
            return {"status": "error", "message": "Unauthorized"}

        try:
            room = data.get("room")
            if not room:
                return {"status": "error", "message": "Room not specified"}

            # Validate room access (implement based on your logic)
            if not await self._validate_room_access(room, auth):
                logger.warning(f"Access denied to room {room} for user {auth.sub}")
                return {"status": "error", "message": "Access denied"}

            # Join room
            await self.sio.enter_room(sid, room)
            self.room_manager.add_member_to_room(room, sid)
            self.subscription_manager.subscribe_to_room(sid, room)

            logger.info(f"User {auth.sub} subscribed to room {room}")
            return {"status": "success", "room": room}

        except Exception as e:
            logger.error(f"Error subscribing to room: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def handle_unsubscribe(
        self,
        sid: str,
        data: Dict[str, Any],
        auth: Optional[TokenData] = None
    ) -> Dict[str, Any]:
        """
        Handle room unsubscription request.

        Args:
            sid: Session ID
            data: Unsubscription data {room: str}
            auth: Authenticated token data

        Returns:
            Response dictionary with status
        """
        if not auth:
            return {"status": "error", "message": "Unauthorized"}

        try:
            room = data.get("room")
            if not room:
                return {"status": "error", "message": "Room not specified"}

            # Leave room
            await self.sio.leave_room(sid, room)
            self.room_manager.remove_member_from_room(room, sid)
            self.subscription_manager.unsubscribe_from_room(sid, room)

            logger.info(f"User {auth.sub} unsubscribed from room {room}")
            return {"status": "success", "room": room}

        except Exception as e:
            logger.error(f"Error unsubscribing from room: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _validate_room_access(
        self,
        room: str,
        auth: TokenData
    ) -> bool:
        """
        Validate if user has access to a room.

        Args:
            room: Room name
            auth: Authenticated token data

        Returns:
            True if access allowed, False otherwise
        """
        user_id = auth.sub

        # User can always access their own user room
        if room == self.room_manager.get_user_room(UUID(user_id)):
            return True

        # User can always access global room
        if room == self.room_manager.get_global_room():
            return True

        # Project room access check
        if room.startswith(self.room_manager.PROJECT_ROOM_PREFIX):
            # TODO: Check if user has access to project
            # This would typically query the database
            return True

        # Agent room access check
        if room.startswith(self.room_manager.AGENT_ROOM_PREFIX):
            # TODO: Check if user has access to agent
            return True

        return False

    async def handle_ping(
        self,
        sid: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle ping/heartbeat from client.

        Args:
            sid: Session ID
            data: Ping data

        Returns:
            Pong response
        """
        return {"status": "pong"}


# Global event handler (initialized after sio is created)
_event_handler: Optional[WebSocketEventHandler] = None


def get_event_handler(sio: socketio.AsyncServer) -> WebSocketEventHandler:
    """Get or create event handler."""
    global _event_handler
    if _event_handler is None:
        _event_handler = WebSocketEventHandler(sio)
    return _event_handler
