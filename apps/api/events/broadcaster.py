"""
Event broadcaster for emitting WebSocket events from any part of the application.

This module provides helper functions to emit real-time events to clients,
integrating with the WebSocket server and supporting Temporal workflow integration.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from websocket.server import get_sio
from websocket.models import (
    EventType,
    WebSocketEvent,
    ProjectUpdateEvent,
    AgentStatusEvent,
    WorkflowProgressEvent,
    PRCreatedEvent,
    IssueUpdateEvent,
    AISuggestionEvent,
)
from middleware.logging import logger as app_logger

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Broadcasts real-time events to WebSocket clients."""

    def __init__(self):
        """Initialize broadcaster."""
        self.sio = None
        self._initialized = False

    def init(self):
        """Initialize broadcaster with Socket.IO server."""
        try:
            self.sio = get_sio()
            self._initialized = True
            logger.info("EventBroadcaster initialized")
        except Exception as e:
            logger.error(f"Failed to initialize EventBroadcaster: {str(e)}")

    async def _ensure_initialized(self) -> bool:
        """Ensure broadcaster is initialized."""
        if not self._initialized:
            self.init()
        return self._initialized

    async def _emit_event(
        self,
        event: WebSocketEvent,
        target_type: str = "global",
        target_id: Optional[UUID] = None,
    ) -> bool:
        """
        Internal method to emit an event.

        Args:
            event: WebSocketEvent to emit
            target_type: Type of target (global, project, user, agent)
            target_id: Optional ID for targeted emission

        Returns:
            True if emission successful
        """
        if not await self._ensure_initialized():
            logger.error("EventBroadcaster not initialized")
            return False

        try:
            event_data = event.dict()

            # Determine room based on target
            if target_type == "global":
                room = "global"
            elif target_type == "project" and target_id:
                room = f"project:{target_id}"
            elif target_type == "user" and target_id:
                room = f"user:{target_id}"
            elif target_type == "agent" and target_id:
                room = f"agent:{target_id}"
            else:
                logger.warning(f"Unknown target type: {target_type}")
                return False

            # Emit event to room
            await self.sio.emit(
                event.type.value,
                event_data,
                room=room,
                namespace="/ws"
            )

            app_logger.info(
                "event_broadcast",
                event_type=event.type.value,
                target_type=target_type,
                target_id=str(target_id) if target_id else None,
                room=room
            )

            return True

        except Exception as e:
            logger.error(f"Error emitting event: {str(e)}", exc_info=True)
            return False

    # Project Events

    async def broadcast_project_updated(
        self,
        project_id: UUID,
        project_name: str,
        repository_url: str,
        status: str,
        updated_by: UUID,
        changes: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Broadcast project update event.

        Args:
            project_id: Project ID
            project_name: Project name
            repository_url: GitHub repository URL
            status: Project status
            updated_by: User ID who made the update
            changes: Dictionary of changes made

        Returns:
            True if broadcast successful
        """
        event_data = ProjectUpdateEvent(
            project_id=project_id,
            project_name=project_name,
            repository_url=repository_url,
            status=status,
            updated_by=updated_by,
            changes=changes or {}
        )

        event = WebSocketEvent(
            type=EventType.PROJECT_UPDATED,
            data=event_data.dict(),
            source="project_service"
        )

        # Broadcast to project room and owner's user room
        results = await asyncio.gather(
            self._emit_event(event, "project", project_id),
            self._emit_event(event, "user", updated_by),
            return_exceptions=True
        )

        return all(r for r in results if not isinstance(r, Exception))

    async def broadcast_project_deleted(
        self,
        project_id: UUID,
        deleted_by: UUID,
    ) -> bool:
        """
        Broadcast project deletion event.

        Args:
            project_id: Project ID
            deleted_by: User ID who deleted the project

        Returns:
            True if broadcast successful
        """
        event = WebSocketEvent(
            type=EventType.PROJECT_DELETED,
            data={"project_id": str(project_id), "deleted_by": str(deleted_by)},
            source="project_service"
        )

        results = await asyncio.gather(
            self._emit_event(event, "project", project_id),
            self._emit_event(event, "user", deleted_by),
            return_exceptions=True
        )

        return all(r for r in results if not isinstance(r, Exception))

    # Agent Events

    async def broadcast_agent_status_changed(
        self,
        agent_id: UUID,
        agent_name: str,
        status: str,
        availability: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Broadcast agent status change event.

        Args:
            agent_id: Agent ID
            agent_name: Agent name
            status: Agent status (online, offline, busy, etc.)
            availability: Availability percentage (0-100)
            metadata: Additional metadata

        Returns:
            True if broadcast successful
        """
        event_data = AgentStatusEvent(
            agent_id=agent_id,
            agent_name=agent_name,
            status=status,
            availability=availability,
            metadata=metadata or {}
        )

        event = WebSocketEvent(
            type=EventType.AGENT_STATUS_CHANGED,
            data=event_data.dict(exclude={"metadata"}) | {"metadata": event_data.metadata},
            source="agent_service"
        )

        # Broadcast to agent room and global room
        results = await asyncio.gather(
            self._emit_event(event, "agent", agent_id),
            self._emit_event(event, "global"),
            return_exceptions=True
        )

        return all(r for r in results if not isinstance(r, Exception))

    # Workflow Events

    async def broadcast_workflow_progress(
        self,
        workflow_id: UUID,
        status: str,
        progress: int,
        current_step: str,
        total_steps: int,
        project_id: Optional[UUID] = None,
        estimated_time_remaining: Optional[int] = None,
        logs: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> bool:
        """
        Broadcast workflow progress event.

        Args:
            workflow_id: Workflow execution ID
            status: Current status (pending, running, completed, failed, cancelled)
            progress: Progress percentage (0-100)
            current_step: Current step being executed
            total_steps: Total number of steps
            project_id: Optional project ID
            estimated_time_remaining: Estimated time remaining in seconds
            logs: List of log messages
            errors: List of error messages

        Returns:
            True if broadcast successful
        """
        event_data = WorkflowProgressEvent(
            workflow_id=workflow_id,
            status=status,
            progress=progress,
            current_step=current_step,
            total_steps=total_steps,
            estimated_time_remaining=estimated_time_remaining,
            logs=logs,
            errors=errors
        )

        event = WebSocketEvent(
            type=EventType.WORKFLOW_PROGRESS,
            data=event_data.dict(),
            source="workflow_service"
        )

        # Broadcast to project room if available, otherwise global
        if project_id:
            return await self._emit_event(event, "project", project_id)
        else:
            return await self._emit_event(event, "global")

    # PR Events

    async def broadcast_pr_created(
        self,
        pr_id: UUID,
        project_id: UUID,
        title: str,
        description: Optional[str],
        author: str,
        branch: str,
        github_url: str,
        status: str,
    ) -> bool:
        """
        Broadcast PR created event.

        Args:
            pr_id: Pull request ID
            project_id: Project ID
            title: PR title
            description: PR description
            author: PR author GitHub username
            branch: Branch name
            github_url: GitHub PR URL
            status: PR status

        Returns:
            True if broadcast successful
        """
        event_data = PRCreatedEvent(
            pr_id=pr_id,
            project_id=project_id,
            title=title,
            description=description,
            author=author,
            branch=branch,
            github_url=github_url,
            status=status,
            created_at=datetime.utcnow()
        )

        event = WebSocketEvent(
            type=EventType.PR_CREATED,
            data=event_data.dict(),
            source="github_service"
        )

        return await self._emit_event(event, "project", project_id)

    async def broadcast_pr_updated(
        self,
        pr_id: UUID,
        project_id: UUID,
        title: str,
        status: str,
    ) -> bool:
        """
        Broadcast PR updated event.

        Args:
            pr_id: Pull request ID
            project_id: Project ID
            title: PR title
            status: PR status

        Returns:
            True if broadcast successful
        """
        event = WebSocketEvent(
            type=EventType.PR_UPDATED,
            data={
                "pr_id": str(pr_id),
                "project_id": str(project_id),
                "title": title,
                "status": status,
            },
            source="github_service"
        )

        return await self._emit_event(event, "project", project_id)

    # Issue Events

    async def broadcast_issue_updated(
        self,
        issue_id: UUID,
        project_id: UUID,
        title: str,
        description: Optional[str],
        status: str,
        priority: Optional[str],
        assigned_to: Optional[UUID],
    ) -> bool:
        """
        Broadcast issue update event.

        Args:
            issue_id: Issue ID
            project_id: Project ID
            title: Issue title
            description: Issue description
            status: Issue status
            priority: Issue priority
            assigned_to: User ID the issue is assigned to

        Returns:
            True if broadcast successful
        """
        event_data = IssueUpdateEvent(
            issue_id=issue_id,
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            updated_at=datetime.utcnow()
        )

        event = WebSocketEvent(
            type=EventType.ISSUE_UPDATED,
            data=event_data.dict(),
            source="github_service"
        )

        # Broadcast to project room and assigned user if applicable
        results = [await self._emit_event(event, "project", project_id)]
        if assigned_to:
            results.append(await self._emit_event(event, "user", assigned_to))

        return all(results)

    # AI Events

    async def broadcast_ai_suggestion(
        self,
        suggestion_id: UUID,
        target_type: str,
        target_id: UUID,
        category: str,
        title: str,
        description: str,
        severity: str = "info",
        confidence: float = 1.0,
        suggested_action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[UUID] = None,
    ) -> bool:
        """
        Broadcast AI suggestion event.

        Args:
            suggestion_id: Suggestion ID
            target_type: Type of target (issue, pr, code)
            target_id: Target ID
            category: Suggestion category (optimization, refactor, bug_fix, etc.)
            title: Suggestion title
            description: Suggestion description
            severity: Severity level (info, warning, critical)
            confidence: Confidence score (0.0 - 1.0)
            suggested_action: Suggested action to take
            metadata: Additional metadata
            project_id: Optional project ID

        Returns:
            True if broadcast successful
        """
        event_data = AISuggestionEvent(
            suggestion_id=suggestion_id,
            target_type=target_type,
            target_id=target_id,
            category=category,
            title=title,
            description=description,
            severity=severity,
            confidence=confidence,
            suggested_action=suggested_action,
            metadata=metadata or {}
        )

        event = WebSocketEvent(
            type=EventType.AI_SUGGESTION,
            data=event_data.dict(),
            source="ai_dock_service"
        )

        # Broadcast to project room if available
        if project_id:
            return await self._emit_event(event, "project", project_id)
        else:
            return await self._emit_event(event, "global")


# Global broadcaster instance
_broadcaster: Optional[EventBroadcaster] = None


def init_broadcaster() -> EventBroadcaster:
    """
    Initialize event broadcaster.

    Returns:
        EventBroadcaster instance
    """
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = EventBroadcaster()
        _broadcaster.init()
    return _broadcaster


def get_broadcaster() -> EventBroadcaster:
    """
    Get event broadcaster instance.

    Returns:
        EventBroadcaster instance
    """
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = EventBroadcaster()
    return _broadcaster
