"""
Room management for WebSocket connections.

Rooms organize subscriptions for different entities:
- project:<project_id> - Project-specific updates
- user:<user_id> - User-specific updates
- agent:<agent_id> - Agent-specific updates
- global - Global/broadcast updates
"""
import logging
from typing import Set, Optional, Dict, List
from uuid import UUID

logger = logging.getLogger(__name__)


class RoomManager:
    """Manages WebSocket rooms and subscriptions."""

    # Room name formats
    PROJECT_ROOM_PREFIX = "project:"
    USER_ROOM_PREFIX = "user:"
    AGENT_ROOM_PREFIX = "agent:"
    GLOBAL_ROOM = "global"

    def __init__(self):
        # In-memory tracking (in production, use Redis)
        self.room_members: Dict[str, Set[str]] = {}

    @staticmethod
    def get_project_room(project_id: UUID) -> str:
        """Get project room name."""
        return f"{RoomManager.PROJECT_ROOM_PREFIX}{project_id}"

    @staticmethod
    def get_user_room(user_id: UUID) -> str:
        """Get user room name."""
        return f"{RoomManager.USER_ROOM_PREFIX}{user_id}"

    @staticmethod
    def get_agent_room(agent_id: UUID) -> str:
        """Get agent room name."""
        return f"{RoomManager.AGENT_ROOM_PREFIX}{agent_id}"

    @staticmethod
    def get_global_room() -> str:
        """Get global room name."""
        return RoomManager.GLOBAL_ROOM

    def add_member_to_room(self, room: str, member_id: str) -> bool:
        """
        Add a member to a room.

        Args:
            room: Room name
            member_id: Member identifier (typically connection ID or SID)

        Returns:
            True if member was added, False if already existed
        """
        if room not in self.room_members:
            self.room_members[room] = set()

        was_new = member_id not in self.room_members[room]
        self.room_members[room].add(member_id)

        logger.debug(f"Added {member_id} to room {room}")
        return was_new

    def remove_member_from_room(self, room: str, member_id: str) -> bool:
        """
        Remove a member from a room.

        Args:
            room: Room name
            member_id: Member identifier

        Returns:
            True if member was removed, False if not found
        """
        if room not in self.room_members:
            return False

        was_present = member_id in self.room_members[room]
        self.room_members[room].discard(member_id)

        # Clean up empty rooms
        if not self.room_members[room]:
            del self.room_members[room]

        logger.debug(f"Removed {member_id} from room {room}")
        return was_present

    def get_room_members(self, room: str) -> Set[str]:
        """
        Get all members in a room.

        Args:
            room: Room name

        Returns:
            Set of member IDs
        """
        return self.room_members.get(room, set()).copy()

    def get_member_rooms(self, member_id: str) -> Set[str]:
        """
        Get all rooms a member belongs to.

        Args:
            member_id: Member identifier

        Returns:
            Set of room names
        """
        rooms = set()
        for room, members in self.room_members.items():
            if member_id in members:
                rooms.add(room)
        return rooms

    def remove_member_from_all_rooms(self, member_id: str) -> List[str]:
        """
        Remove a member from all rooms (e.g., on disconnect).

        Args:
            member_id: Member identifier

        Returns:
            List of rooms the member was removed from
        """
        removed_from = []
        rooms_to_check = list(self.room_members.keys())

        for room in rooms_to_check:
            if member_id in self.room_members[room]:
                self.room_members[room].discard(member_id)
                removed_from.append(room)

                # Clean up empty rooms
                if not self.room_members[room]:
                    del self.room_members[room]

        logger.debug(f"Removed {member_id} from {len(removed_from)} rooms")
        return removed_from

    def get_room_count(self, room: str) -> int:
        """
        Get number of members in a room.

        Args:
            room: Room name

        Returns:
            Number of members
        """
        return len(self.room_members.get(room, set()))

    def get_all_rooms(self) -> Dict[str, int]:
        """
        Get all active rooms and their member counts.

        Returns:
            Dictionary mapping room names to member counts
        """
        return {room: len(members) for room, members in self.room_members.items()}


class RoomSubscriptionManager:
    """Manages user subscriptions to rooms."""

    def __init__(self):
        # Maps user_id -> set of rooms they subscribe to
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # Maps connection_id -> user_id
        self.connection_to_user: Dict[str, str] = {}

    def register_connection(self, connection_id: str, user_id: str) -> None:
        """
        Register a connection for a user.

        Args:
            connection_id: WebSocket connection ID
            user_id: User ID
        """
        self.connection_to_user[connection_id] = user_id
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()

        logger.debug(f"Registered connection {connection_id} for user {user_id}")

    def unregister_connection(self, connection_id: str) -> Optional[str]:
        """
        Unregister a connection.

        Args:
            connection_id: WebSocket connection ID

        Returns:
            User ID if found, None otherwise
        """
        user_id = self.connection_to_user.pop(connection_id, None)
        logger.debug(f"Unregistered connection {connection_id}")
        return user_id

    def subscribe_to_room(self, connection_id: str, room: str) -> bool:
        """
        Subscribe a connection to a room.

        Args:
            connection_id: WebSocket connection ID
            room: Room name

        Returns:
            True if subscription was successful
        """
        user_id = self.connection_to_user.get(connection_id)
        if not user_id:
            logger.warning(f"Connection {connection_id} not registered")
            return False

        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()

        self.user_subscriptions[user_id].add(room)
        logger.debug(f"Subscribed user {user_id} to room {room}")
        return True

    def unsubscribe_from_room(self, connection_id: str, room: str) -> bool:
        """
        Unsubscribe a connection from a room.

        Args:
            connection_id: WebSocket connection ID
            room: Room name

        Returns:
            True if unsubscription was successful
        """
        user_id = self.connection_to_user.get(connection_id)
        if not user_id or user_id not in self.user_subscriptions:
            return False

        self.user_subscriptions[user_id].discard(room)
        logger.debug(f"Unsubscribed user {user_id} from room {room}")
        return True

    def get_user_rooms(self, user_id: str) -> Set[str]:
        """
        Get all rooms a user is subscribed to.

        Args:
            user_id: User ID

        Returns:
            Set of room names
        """
        return self.user_subscriptions.get(user_id, set()).copy()

    def clear_user_subscriptions(self, user_id: str) -> Set[str]:
        """
        Clear all subscriptions for a user.

        Args:
            user_id: User ID

        Returns:
            Set of rooms that were cleared
        """
        rooms = self.user_subscriptions.pop(user_id, set())
        logger.debug(f"Cleared {len(rooms)} subscriptions for user {user_id}")
        return rooms


# Global instances
room_manager = RoomManager()
subscription_manager = RoomSubscriptionManager()
