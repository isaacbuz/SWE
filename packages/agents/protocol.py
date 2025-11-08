"""
Agent Communication Protocol

Defines message formats, handoff protocols, evidence sharing,
and state persistence for inter-agent communication.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid
import json


class MessageIntent(str, Enum):
    """Message intent types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    HANDOFF = "handoff"
    ESCALATION = "escalation"


class MessagePriority(str, Enum):
    """Message priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HandoffReason(str, Enum):
    """Reasons for agent handoff"""
    TASK_COMPLETE = "task_complete"
    BLOCKED = "blocked"
    OUT_OF_SCOPE = "out_of_scope"
    NEEDS_SPECIALIST = "needs_specialist"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    ESCALATION = "escalation"


@dataclass
class Evidence:
    """Evidence for agent decisions"""
    id: str
    source: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    """
    Standard message format for inter-agent communication

    Follows the protocol defined in architecture overview:
    - Unique message ID for tracking
    - Sender and recipient(s)
    - Intent and priority
    - Typed payload
    - Evidence trail
    - Timestamps for auditability
    """
    message_id: str
    from_agent: str
    to_agents: List[str]
    intent: MessageIntent
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.MEDIUM
    evidence_ids: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    parent_message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_request(
        cls,
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM,
        evidence: Optional[List[Evidence]] = None,
        conversation_id: Optional[str] = None
    ) -> "AgentMessage":
        """Create a request message"""
        msg_id = str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())

        return cls(
            message_id=msg_id,
            from_agent=from_agent,
            to_agents=[to_agent],
            intent=MessageIntent.REQUEST,
            payload=payload,
            priority=priority,
            evidence=evidence or [],
            evidence_ids=[e.id for e in (evidence or [])],
            conversation_id=conv_id
        )

    @classmethod
    def create_response(
        cls,
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any],
        parent_message: "AgentMessage",
        evidence: Optional[List[Evidence]] = None
    ) -> "AgentMessage":
        """Create a response message"""
        return cls(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agents=[to_agent],
            intent=MessageIntent.RESPONSE,
            payload=payload,
            evidence=evidence or [],
            evidence_ids=[e.id for e in (evidence or [])],
            parent_message_id=parent_message.message_id,
            conversation_id=parent_message.conversation_id
        )

    @classmethod
    def create_notification(
        cls,
        from_agent: str,
        to_agents: List[str],
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.LOW
    ) -> "AgentMessage":
        """Create a notification message"""
        return cls(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agents=to_agents,
            intent=MessageIntent.NOTIFICATION,
            payload=payload,
            priority=priority
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agents": self.to_agents,
            "intent": self.intent.value,
            "payload": self.payload,
            "priority": self.priority.value,
            "evidence_ids": self.evidence_ids,
            "evidence": [
                {
                    "id": e.id,
                    "source": e.source,
                    "description": e.description,
                    "data": e.data,
                    "weight": e.weight,
                    "timestamp": e.timestamp.isoformat(),
                    "metadata": e.metadata
                }
                for e in self.evidence
            ],
            "parent_message_id": self.parent_message_id,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create from dictionary"""
        evidence = [
            Evidence(
                id=e["id"],
                source=e["source"],
                description=e["description"],
                data=e["data"],
                weight=e["weight"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                metadata=e["metadata"]
            )
            for e in data.get("evidence", [])
        ]

        return cls(
            message_id=data["message_id"],
            from_agent=data["from_agent"],
            to_agents=data["to_agents"],
            intent=MessageIntent(data["intent"]),
            payload=data["payload"],
            priority=MessagePriority(data["priority"]),
            evidence_ids=data["evidence_ids"],
            evidence=evidence,
            parent_message_id=data.get("parent_message_id"),
            conversation_id=data.get("conversation_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class HandoffRequest:
    """
    Request to hand off work to another agent

    Used when an agent:
    - Completes its part and needs to pass work forward
    - Is blocked and needs help
    - Encounters work outside its scope
    - Fails quality gates
    """
    handoff_id: str
    from_agent: str
    to_agent: str
    reason: HandoffReason
    context: Dict[str, Any]
    work_state: Dict[str, Any]
    evidence: List[Evidence] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        from_agent: str,
        to_agent: str,
        reason: HandoffReason,
        context: Dict[str, Any],
        work_state: Dict[str, Any],
        evidence: Optional[List[Evidence]] = None,
        blocking_issues: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None
    ) -> "HandoffRequest":
        """Create handoff request"""
        return cls(
            handoff_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            context=context,
            work_state=work_state,
            evidence=evidence or [],
            blocking_issues=blocking_issues or [],
            recommendations=recommendations or []
        )

    def to_message(self) -> AgentMessage:
        """Convert to agent message"""
        return AgentMessage(
            message_id=str(uuid.uuid4()),
            from_agent=self.from_agent,
            to_agents=[self.to_agent],
            intent=MessageIntent.HANDOFF,
            payload={
                "handoff_id": self.handoff_id,
                "reason": self.reason.value,
                "context": self.context,
                "work_state": self.work_state,
                "blocking_issues": self.blocking_issues,
                "recommendations": self.recommendations
            },
            priority=MessagePriority.HIGH,
            evidence=self.evidence,
            evidence_ids=[e.id for e in self.evidence],
            metadata=self.metadata
        )


@dataclass
class EscalationRequest:
    """
    Request to escalate to human or higher authority

    Used when:
    - Agents cannot resolve conflict
    - Decision requires human judgment
    - Risk threshold exceeded
    - Policy violation detected
    """
    escalation_id: str
    from_agent: str
    severity: str  # critical, high, medium, low
    issue: str
    context: Dict[str, Any]
    attempted_resolutions: List[str]
    evidence: List[Evidence] = field(default_factory=list)
    recommended_action: Optional[str] = None
    requires_immediate_attention: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        from_agent: str,
        severity: str,
        issue: str,
        context: Dict[str, Any],
        attempted_resolutions: List[str],
        evidence: Optional[List[Evidence]] = None,
        recommended_action: Optional[str] = None,
        requires_immediate_attention: bool = False
    ) -> "EscalationRequest":
        """Create escalation request"""
        return cls(
            escalation_id=str(uuid.uuid4()),
            from_agent=from_agent,
            severity=severity,
            issue=issue,
            context=context,
            attempted_resolutions=attempted_resolutions,
            evidence=evidence or [],
            recommended_action=recommended_action,
            requires_immediate_attention=requires_immediate_attention
        )

    def to_message(self, to_agent: str = "human") -> AgentMessage:
        """Convert to agent message"""
        return AgentMessage(
            message_id=str(uuid.uuid4()),
            from_agent=self.from_agent,
            to_agents=[to_agent],
            intent=MessageIntent.ESCALATION,
            payload={
                "escalation_id": self.escalation_id,
                "severity": self.severity,
                "issue": self.issue,
                "context": self.context,
                "attempted_resolutions": self.attempted_resolutions,
                "recommended_action": self.recommended_action,
                "requires_immediate_attention": self.requires_immediate_attention
            },
            priority=MessagePriority.CRITICAL if self.requires_immediate_attention else MessagePriority.HIGH,
            evidence=self.evidence,
            evidence_ids=[e.id for e in self.evidence],
            metadata=self.metadata
        )


@dataclass
class AgentState:
    """
    Persistent state for an agent

    Enables:
    - Crash recovery
    - Handoff continuity
    - Audit trails
    - Performance tracking
    """
    agent_id: str
    status: str  # idle, running, blocked, completed, failed
    current_task_id: Optional[str] = None
    work_state: Dict[str, Any] = field(default_factory=dict)
    pending_messages: List[str] = field(default_factory=list)
    conversation_history: List[str] = field(default_factory=list)
    evidence_trail: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_task_id": self.current_task_id,
            "work_state": self.work_state,
            "pending_messages": self.pending_messages,
            "conversation_history": self.conversation_history,
            "evidence_trail": self.evidence_trail,
            "performance_metrics": self.performance_metrics,
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Create from dictionary"""
        return cls(
            agent_id=data["agent_id"],
            status=data["status"],
            current_task_id=data.get("current_task_id"),
            work_state=data.get("work_state", {}),
            pending_messages=data.get("pending_messages", []),
            conversation_history=data.get("conversation_history", []),
            evidence_trail=data.get("evidence_trail", []),
            performance_metrics=data.get("performance_metrics", {}),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            metadata=data.get("metadata", {})
        )


class MessageBus:
    """
    Event-driven message bus for agent communication

    Features:
    - Async message delivery
    - Message routing
    - Conversation tracking
    - Evidence aggregation
    """

    def __init__(self):
        self.messages: Dict[str, AgentMessage] = {}
        self.conversations: Dict[str, List[str]] = {}
        self.agent_queues: Dict[str, List[str]] = {}
        self.subscribers: Dict[str, List[callable]] = {}

    async def send(self, message: AgentMessage) -> None:
        """Send message to recipients"""
        # Store message
        self.messages[message.message_id] = message

        # Track conversation
        if message.conversation_id:
            if message.conversation_id not in self.conversations:
                self.conversations[message.conversation_id] = []
            self.conversations[message.conversation_id].append(message.message_id)

        # Queue for recipients
        for agent_id in message.to_agents:
            if agent_id not in self.agent_queues:
                self.agent_queues[agent_id] = []
            self.agent_queues[agent_id].append(message.message_id)

            # Notify subscribers
            if agent_id in self.subscribers:
                for callback in self.subscribers[agent_id]:
                    await callback(message)

    async def receive(self, agent_id: str) -> Optional[AgentMessage]:
        """Receive next message for agent"""
        if agent_id not in self.agent_queues or not self.agent_queues[agent_id]:
            return None

        message_id = self.agent_queues[agent_id].pop(0)
        return self.messages.get(message_id)

    def subscribe(self, agent_id: str, callback: callable) -> None:
        """Subscribe to messages for agent"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)

    def get_conversation(self, conversation_id: str) -> List[AgentMessage]:
        """Get all messages in a conversation"""
        if conversation_id not in self.conversations:
            return []

        return [
            self.messages[msg_id]
            for msg_id in self.conversations[conversation_id]
            if msg_id in self.messages
        ]

    def get_evidence_trail(self, conversation_id: str) -> List[Evidence]:
        """Get all evidence from a conversation"""
        messages = self.get_conversation(conversation_id)
        evidence = []
        seen_ids = set()

        for msg in messages:
            for e in msg.evidence:
                if e.id not in seen_ids:
                    evidence.append(e)
                    seen_ids.add(e.id)

        return evidence
