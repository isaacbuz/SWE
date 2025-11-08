"""
WebSocket server unit and integration tests.

Run with: pytest apps/api/websocket/tests.py -v
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime

# Mock tests - no external dependencies required
from websocket.models import (
    EventType,
    WebSocketEvent,
    ProjectUpdateEvent,
    AgentStatusEvent,
    AgentStatus,
    WorkflowProgressEvent,
    WorkflowStatus,
)
from websocket.rooms import RoomManager, RoomSubscriptionManager
from websocket.auth import WebSocketAuthHandler


class TestEventModels:
    """Test WebSocket event models."""

    def test_project_update_event(self):
        """Test project update event creation."""
        project_id = uuid4()
        user_id = uuid4()

        event = ProjectUpdateEvent(
            project_id=project_id,
            project_name="Test Project",
            repository_url="https://github.com/test/repo",
            status="active",
            updated_by=user_id,
            changes={"status": "updated"}
        )

        assert event.project_id == project_id
        assert event.status == "active"
        assert event.changes["status"] == "updated"

    def test_agent_status_event(self):
        """Test agent status event creation."""
        agent_id = uuid4()

        event = AgentStatusEvent(
            agent_id=agent_id,
            agent_name="GPT-4 Agent",
            status=AgentStatus.ONLINE,
            availability=85
        )

        assert event.agent_id == agent_id
        assert event.status == AgentStatus.ONLINE
        assert event.availability == 85

    def test_workflow_progress_event(self):
        """Test workflow progress event creation."""
        workflow_id = uuid4()

        event = WorkflowProgressEvent(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            progress=50,
            current_step="Step 2",
            total_steps=5,
            estimated_time_remaining=120
        )

        assert event.workflow_id == workflow_id
        assert event.progress == 50
        assert event.total_steps == 5

    def test_websocket_event(self):
        """Test WebSocket event envelope."""
        event_data = {"message": "test"}

        event = WebSocketEvent(
            type=EventType.PROJECT_UPDATED,
            data=event_data
        )

        assert event.type == EventType.PROJECT_UPDATED
        assert event.data == event_data
        assert isinstance(event.timestamp, datetime)

    def test_event_serialization(self):
        """Test event can be serialized to dict."""
        project_id = uuid4()

        event = WebSocketEvent(
            type=EventType.PROJECT_UPDATED,
            data={"project_id": str(project_id)},
            source="test"
        )

        event_dict = event.dict()

        assert event_dict["type"] == "project.updated"
        assert event_dict["source"] == "test"
        assert "timestamp" in event_dict


class TestRoomManager:
    """Test room management."""

    def test_room_names(self):
        """Test room name generation."""
        project_id = uuid4()
        user_id = uuid4()
        agent_id = uuid4()

        assert RoomManager.get_project_room(project_id) == f"project:{project_id}"
        assert RoomManager.get_user_room(user_id) == f"user:{user_id}"
        assert RoomManager.get_agent_room(agent_id) == f"agent:{agent_id}"
        assert RoomManager.get_global_room() == "global"

    def test_add_member_to_room(self):
        """Test adding members to rooms."""
        manager = RoomManager()
        room = "test_room"
        member = "member_1"

        # Add new member
        was_new = manager.add_member_to_room(room, member)
        assert was_new is True
        assert manager.get_room_count(room) == 1

        # Add same member again
        was_new = manager.add_member_to_room(room, member)
        assert was_new is False
        assert manager.get_room_count(room) == 1

    def test_remove_member_from_room(self):
        """Test removing members from rooms."""
        manager = RoomManager()
        room = "test_room"
        member = "member_1"

        manager.add_member_to_room(room, member)
        assert manager.get_room_count(room) == 1

        was_present = manager.remove_member_from_room(room, member)
        assert was_present is True
        assert manager.get_room_count(room) == 0

        # Room should be cleaned up
        assert room not in manager.room_members

    def test_get_room_members(self):
        """Test getting room members."""
        manager = RoomManager()
        room = "test_room"

        manager.add_member_to_room(room, "member_1")
        manager.add_member_to_room(room, "member_2")
        manager.add_member_to_room(room, "member_3")

        members = manager.get_room_members(room)
        assert len(members) == 3
        assert "member_1" in members
        assert "member_2" in members

    def test_get_member_rooms(self):
        """Test getting all rooms for a member."""
        manager = RoomManager()

        manager.add_member_to_room("room_1", "member_1")
        manager.add_member_to_room("room_2", "member_1")
        manager.add_member_to_room("room_3", "member_1")

        rooms = manager.get_member_rooms("member_1")
        assert len(rooms) == 3
        assert "room_1" in rooms
        assert "room_2" in rooms

    def test_remove_member_from_all_rooms(self):
        """Test removing member from all rooms."""
        manager = RoomManager()

        manager.add_member_to_room("room_1", "member_1")
        manager.add_member_to_room("room_2", "member_1")
        manager.add_member_to_room("room_3", "member_1")

        removed_from = manager.remove_member_from_all_rooms("member_1")
        assert len(removed_from) == 3

        # Member should not be in any room
        for room in ["room_1", "room_2", "room_3"]:
            assert "member_1" not in manager.get_room_members(room)

    def test_get_all_rooms(self):
        """Test getting all rooms."""
        manager = RoomManager()

        manager.add_member_to_room("room_1", "member_1")
        manager.add_member_to_room("room_1", "member_2")
        manager.add_member_to_room("room_2", "member_3")

        all_rooms = manager.get_all_rooms()
        assert len(all_rooms) == 2
        assert all_rooms["room_1"] == 2
        assert all_rooms["room_2"] == 1


class TestRoomSubscriptionManager:
    """Test subscription management."""

    def test_register_connection(self):
        """Test registering a connection."""
        manager = RoomSubscriptionManager()
        user_id = str(uuid4())

        manager.register_connection("conn_1", user_id)

        assert "conn_1" in manager.connection_to_user
        assert manager.connection_to_user["conn_1"] == user_id
        assert user_id in manager.user_subscriptions

    def test_unregister_connection(self):
        """Test unregistering a connection."""
        manager = RoomSubscriptionManager()
        user_id = str(uuid4())

        manager.register_connection("conn_1", user_id)
        returned_user = manager.unregister_connection("conn_1")

        assert returned_user == user_id
        assert "conn_1" not in manager.connection_to_user

    def test_subscribe_to_room(self):
        """Test subscribing to a room."""
        manager = RoomSubscriptionManager()
        user_id = str(uuid4())

        manager.register_connection("conn_1", user_id)
        success = manager.subscribe_to_room("conn_1", "project:123")

        assert success is True
        assert "project:123" in manager.get_user_rooms(user_id)

    def test_unsubscribe_from_room(self):
        """Test unsubscribing from a room."""
        manager = RoomSubscriptionManager()
        user_id = str(uuid4())

        manager.register_connection("conn_1", user_id)
        manager.subscribe_to_room("conn_1", "project:123")

        success = manager.unsubscribe_from_room("conn_1", "project:123")

        assert success is True
        assert "project:123" not in manager.get_user_rooms(user_id)

    def test_get_user_rooms(self):
        """Test getting all rooms for a user."""
        manager = RoomSubscriptionManager()
        user_id = str(uuid4())

        manager.register_connection("conn_1", user_id)
        manager.subscribe_to_room("conn_1", "project:123")
        manager.subscribe_to_room("conn_1", "user:456")

        rooms = manager.get_user_rooms(user_id)
        assert len(rooms) == 2
        assert "project:123" in rooms
        assert "user:456" in rooms

    def test_clear_user_subscriptions(self):
        """Test clearing all subscriptions for a user."""
        manager = RoomSubscriptionManager()
        user_id = str(uuid4())

        manager.register_connection("conn_1", user_id)
        manager.subscribe_to_room("conn_1", "project:123")
        manager.subscribe_to_room("conn_1", "user:456")

        cleared_rooms = manager.clear_user_subscriptions(user_id)

        assert len(cleared_rooms) == 2
        assert len(manager.get_user_rooms(user_id)) == 0


class TestWebSocketAuth:
    """Test WebSocket authentication."""

    def test_extract_token_from_auth_header(self):
        """Test extracting token from Authorization header."""
        handler = WebSocketAuthHandler()

        token = handler.extract_token_from_auth_header("Bearer valid_token_123")
        assert token == "valid_token_123"

        # Invalid format
        token = handler.extract_token_from_auth_header("InvalidFormat token")
        assert token is None

        # Missing header
        token = handler.extract_token_from_auth_header(None)
        assert token is None

    def test_extract_token_from_query_params(self):
        """Test extracting token from query parameters."""
        handler = WebSocketAuthHandler()

        params = {"token": "query_token_123", "other": "value"}
        token = handler.extract_token_from_query_params(params)
        assert token == "query_token_123"

        # Missing token
        token = handler.extract_token_from_query_params({"other": "value"})
        assert token is None

    def test_create_error_event(self):
        """Test creating error events."""
        handler = WebSocketAuthHandler()

        event = handler.create_error_event(
            error_code="AUTH_FAILED",
            error_message="Invalid token",
            connection_id="conn_123"
        )

        assert event.type == EventType.CONNECTION_ERROR
        assert event.data["error_code"] == "AUTH_FAILED"
        assert event.data["error_message"] == "Invalid token"
        assert event.data["connection_id"] == "conn_123"


class TestEventTypeEnums:
    """Test event type enumerations."""

    def test_project_events(self):
        """Test project event types."""
        assert EventType.PROJECT_UPDATED.value == "project.updated"
        assert EventType.PROJECT_DELETED.value == "project.deleted"

    def test_agent_events(self):
        """Test agent event types."""
        assert EventType.AGENT_STATUS_CHANGED.value == "agent.status_changed"
        assert EventType.AGENT_CONNECTED.value == "agent.connected"
        assert EventType.AGENT_DISCONNECTED.value == "agent.disconnected"

    def test_workflow_events(self):
        """Test workflow event types."""
        assert EventType.WORKFLOW_STARTED.value == "workflow.started"
        assert EventType.WORKFLOW_PROGRESS.value == "workflow.progress"
        assert EventType.WORKFLOW_COMPLETED.value == "workflow.completed"
        assert EventType.WORKFLOW_FAILED.value == "workflow.failed"

    def test_pr_events(self):
        """Test PR event types."""
        assert EventType.PR_CREATED.value == "pr.created"
        assert EventType.PR_UPDATED.value == "pr.updated"
        assert EventType.PR_CLOSED.value == "pr.closed"

    def test_issue_events(self):
        """Test issue event types."""
        assert EventType.ISSUE_CREATED.value == "issue.created"
        assert EventType.ISSUE_UPDATED.value == "issue.updated"
        assert EventType.ISSUE_CLOSED.value == "issue.closed"

    def test_ai_events(self):
        """Test AI event types."""
        assert EventType.AI_SUGGESTION.value == "ai.suggestion"
        assert EventType.AI_ANALYSIS_COMPLETE.value == "ai.analysis_complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
