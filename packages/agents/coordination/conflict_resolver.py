"""
Conflict Resolver Agent

Mediates disagreements between agents (e.g., Reviewer blocks Codegen).
Detects conflicts, analyzes both positions, gathers additional evidence,
proposes resolutions, and escalates to humans if needed.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base import BaseAgent, Task, Context, AgentResult, TaskType
from protocol import (
    AgentMessage, EscalationRequest, Evidence,
    MessageIntent, MessagePriority
)
from registry import AgentRegistry


@dataclass
class AgentPosition:
    """Position taken by an agent in a conflict"""
    agent_id: str
    position: str
    rationale: str
    evidence: List[Evidence] = field(default_factory=list)
    confidence: float = 0.5  # 0.0-1.0
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conflict:
    """Conflict between agents"""
    conflict_id: str
    type: str  # code_quality, security, performance, architecture, etc.
    agents_involved: List[str]
    positions: List[AgentPosition]
    context: Dict[str, Any]
    severity: str  # low, medium, high, critical
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    resolution_rationale: Optional[str] = None
    escalated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConflictResolver(BaseAgent):
    """
    Conflict Resolver for mediating agent disagreements

    Features:
    - Automatic conflict detection
    - Position analysis
    - Evidence gathering
    - Resolution proposal
    - Escalation to humans
    - Decision documentation
    """

    def __init__(
        self,
        agent_id: str = "conflict_resolver",
        registry: Optional[AgentRegistry] = None,
        escalation_threshold: float = 0.7,
        auto_resolve_enabled: bool = True,
        **kwargs
    ):
        """
        Initialize conflict resolver

        Args:
            agent_id: Agent identifier
            registry: Agent registry
            escalation_threshold: Confidence threshold for escalation
            auto_resolve_enabled: Enable automatic resolution
            **kwargs: Additional BaseAgent arguments
        """
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.REVIEW,
            **kwargs
        )

        self.registry = registry
        self.escalation_threshold = escalation_threshold
        self.auto_resolve_enabled = auto_resolve_enabled

        # Active conflicts
        self.active_conflicts: Dict[str, Conflict] = {}
        self.resolved_conflicts: Dict[str, Conflict] = {}

        self.logger = logging.getLogger(f"Agent.{agent_id}")

    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return """You are a Conflict Resolver agent responsible for mediating disagreements
between AI agents in the software development process.

Your responsibilities:
1. Analyze conflicting positions from different agents
2. Evaluate evidence and rationale from both sides
3. Gather additional evidence if needed
4. Propose fair and technically sound resolutions
5. Escalate to humans when necessary
6. Document decisions with clear rationale

When analyzing conflicts:
- Be objective and unbiased
- Prioritize code quality, security, and best practices
- Consider trade-offs between different concerns
- Evaluate confidence levels in each position
- Look for middle-ground solutions when possible
- Know when human judgment is required

Provide resolution in JSON format:
{
  "resolution_type": "accept|reject|compromise|escalate",
  "decision": "final decision",
  "rationale": "detailed explanation",
  "action_items": ["specific action 1", "specific action 2"],
  "confidence": 0.0-1.0,
  "requires_escalation": boolean,
  "escalation_reason": "reason if escalating"
}"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute conflict resolution

        Args:
            task: Task containing conflict data
            context: Execution context

        Returns:
            Resolution result
        """
        try:
            # Extract conflict from task
            conflict = await self._parse_conflict(task, context)

            if not conflict:
                return AgentResult(
                    success=False,
                    output={},
                    evidence=[],
                    error="Failed to parse conflict"
                )

            self.active_conflicts[conflict.conflict_id] = conflict

            # Detect conflict type
            await self._classify_conflict(conflict, context)

            # Analyze positions
            analysis = await self._analyze_positions(conflict, context)

            # Gather additional evidence if needed
            if analysis.get("needs_more_evidence"):
                await self._gather_evidence(conflict, context)

            # Attempt resolution
            if self.auto_resolve_enabled:
                resolution = await self._propose_resolution(conflict, context)
            else:
                resolution = None

            # Check if escalation is needed
            if self._should_escalate(conflict, resolution):
                escalation = await self._escalate_conflict(conflict, context)
                return AgentResult(
                    success=True,
                    output={
                        "conflict_id": conflict.conflict_id,
                        "resolution_type": "escalated",
                        "escalation": escalation
                    },
                    evidence=self._collect_conflict_evidence(conflict),
                    metadata={"escalated": True}
                )

            # Apply resolution
            if resolution:
                conflict.resolution = resolution["decision"]
                conflict.resolution_rationale = resolution["rationale"]
                conflict.resolved_at = datetime.utcnow()
                self.resolved_conflicts[conflict.conflict_id] = conflict
                del self.active_conflicts[conflict.conflict_id]

                return AgentResult(
                    success=True,
                    output={
                        "conflict_id": conflict.conflict_id,
                        "resolution_type": resolution["resolution_type"],
                        "decision": resolution["decision"],
                        "rationale": resolution["rationale"],
                        "action_items": resolution.get("action_items", []),
                        "confidence": resolution.get("confidence", 0.5)
                    },
                    evidence=self._collect_conflict_evidence(conflict),
                    metadata={
                        "severity": conflict.severity,
                        "agents_involved": conflict.agents_involved
                    }
                )

            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error="Failed to resolve conflict"
            )

        except Exception as e:
            self.logger.error(f"Conflict resolution failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    async def _parse_conflict(
        self,
        task: Task,
        context: Context
    ) -> Optional[Conflict]:
        """
        Parse conflict from task data

        Args:
            task: Task containing conflict
            context: Execution context

        Returns:
            Conflict object or None
        """
        try:
            conflict_data = task.input_data.get("conflict", {})

            positions = []
            for pos_data in conflict_data.get("positions", []):
                evidence = [
                    Evidence(
                        id=e.get("id", str(uuid.uuid4())),
                        source=e.get("source", ""),
                        description=e.get("description", ""),
                        weight=e.get("weight", 1.0)
                    )
                    for e in pos_data.get("evidence", [])
                ]

                position = AgentPosition(
                    agent_id=pos_data["agent_id"],
                    position=pos_data["position"],
                    rationale=pos_data["rationale"],
                    evidence=evidence,
                    confidence=pos_data.get("confidence", 0.5),
                    supporting_data=pos_data.get("supporting_data", {})
                )
                positions.append(position)

            conflict = Conflict(
                conflict_id=str(uuid.uuid4()),
                type=conflict_data.get("type", "unknown"),
                agents_involved=[p.agent_id for p in positions],
                positions=positions,
                context=conflict_data.get("context", {}),
                severity=conflict_data.get("severity", "medium"),
                metadata=conflict_data.get("metadata", {})
            )

            return conflict

        except Exception as e:
            self.logger.error(f"Failed to parse conflict: {e}")
            return None

    async def _classify_conflict(
        self,
        conflict: Conflict,
        context: Context
    ) -> None:
        """Classify conflict type if not specified"""
        if conflict.type != "unknown":
            return

        # Use LLM to classify
        prompt = f"""Classify the following conflict between agents:

Agent Positions:
{self._format_positions(conflict.positions)}

Context: {conflict.context}

Classify as one of: code_quality, security, performance, architecture, testing, documentation, other"""

        try:
            task = Task(
                id=f"classify_{conflict.conflict_id}",
                type=TaskType.PLANNING,
                description="Classify conflict type",
                input_data={}
            )

            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                max_tokens=256
            )

            conflict.type = response["content"].strip().lower()

        except Exception as e:
            self.logger.error(f"Conflict classification failed: {e}")
            conflict.type = "other"

    async def _analyze_positions(
        self,
        conflict: Conflict,
        context: Context
    ) -> Dict[str, Any]:
        """
        Analyze conflicting positions

        Args:
            conflict: Conflict to analyze
            context: Execution context

        Returns:
            Analysis results
        """
        prompt = f"""Analyze the following conflict between agents:

Conflict Type: {conflict.type}
Severity: {conflict.severity}

Agent Positions:
{self._format_positions(conflict.positions)}

Context:
{conflict.context}

Analyze:
1. Validity of each position
2. Strength of evidence
3. Technical correctness
4. Potential risks in each approach
5. Whether more evidence is needed

Provide analysis in JSON format with:
- position_analyses: array of {{"agent_id": string, "validity": 0-1, "strengths": [], "weaknesses": []}}
- needs_more_evidence: boolean
- additional_evidence_needed: array of strings
- preliminary_recommendation: string"""

        try:
            task = Task(
                id=f"analyze_{conflict.conflict_id}",
                type=TaskType.REVIEW,
                description="Analyze conflict positions",
                input_data={}
            )

            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_json=True,
                max_tokens=2048
            )

            import json
            return json.loads(response["content"])

        except Exception as e:
            self.logger.error(f"Position analysis failed: {e}")
            return {"needs_more_evidence": False}

    async def _gather_evidence(
        self,
        conflict: Conflict,
        context: Context
    ) -> None:
        """Gather additional evidence for conflict resolution"""
        # TODO: Implement evidence gathering
        # Could involve:
        # - Running additional tests
        # - Security scans
        # - Performance benchmarks
        # - Code analysis
        # - Consulting documentation
        pass

    async def _propose_resolution(
        self,
        conflict: Conflict,
        context: Context
    ) -> Optional[Dict[str, Any]]:
        """
        Propose resolution for conflict

        Args:
            conflict: Conflict to resolve
            context: Execution context

        Returns:
            Resolution proposal
        """
        prompt = f"""Propose a resolution for the following conflict:

Conflict Type: {conflict.type}
Severity: {conflict.severity}

Agent Positions:
{self._format_positions(conflict.positions)}

Context:
{conflict.context}

Propose a resolution that:
1. Is technically sound
2. Balances concerns from all parties
3. Prioritizes quality and security
4. Provides clear action items
5. Documents rationale clearly

If the conflict requires human judgment, indicate that escalation is needed."""

        try:
            task = Task(
                id=f"resolve_{conflict.conflict_id}",
                type=TaskType.REVIEW,
                description="Propose conflict resolution",
                input_data={}
            )

            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_json=True,
                max_tokens=2048
            )

            import json
            resolution = json.loads(response["content"])

            # Add evidence
            conflict.metadata["resolution_evidence"] = [
                {
                    "source": "llm_analysis",
                    "confidence": resolution.get("confidence", 0.5),
                    "model": response.get("model_used")
                }
            ]

            return resolution

        except Exception as e:
            self.logger.error(f"Resolution proposal failed: {e}")
            return None

    def _should_escalate(
        self,
        conflict: Conflict,
        resolution: Optional[Dict[str, Any]]
    ) -> bool:
        """Determine if conflict should be escalated"""
        # Escalate if critical severity
        if conflict.severity == "critical":
            return True

        # Escalate if resolution explicitly requires it
        if resolution and resolution.get("requires_escalation"):
            return True

        # Escalate if confidence is too low
        if resolution and resolution.get("confidence", 0.0) < self.escalation_threshold:
            return True

        # Escalate if positions have high confidence and conflict
        high_confidence_positions = [
            p for p in conflict.positions
            if p.confidence > 0.8
        ]
        if len(high_confidence_positions) >= 2:
            return True

        return False

    async def _escalate_conflict(
        self,
        conflict: Conflict,
        context: Context
    ) -> Dict[str, Any]:
        """
        Escalate conflict to human

        Args:
            conflict: Conflict to escalate
            context: Execution context

        Returns:
            Escalation details
        """
        conflict.escalated = True

        # Create escalation request
        escalation = EscalationRequest.create(
            from_agent=self.agent_id,
            severity=conflict.severity,
            issue=f"Conflict between agents: {', '.join(conflict.agents_involved)}",
            context={
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict.type,
                "positions": [
                    {
                        "agent": p.agent_id,
                        "position": p.position,
                        "rationale": p.rationale,
                        "confidence": p.confidence
                    }
                    for p in conflict.positions
                ],
                "context": conflict.context
            },
            attempted_resolutions=[
                "Analyzed positions",
                "Gathered evidence",
                "Attempted automatic resolution"
            ],
            recommended_action=f"Human review required for {conflict.type} conflict",
            requires_immediate_attention=(conflict.severity == "critical")
        )

        self.logger.info(
            f"Escalating conflict {conflict.conflict_id} to human "
            f"(severity={conflict.severity}, type={conflict.type})"
        )

        return {
            "escalation_id": escalation.escalation_id,
            "severity": escalation.severity,
            "issue": escalation.issue,
            "recommended_action": escalation.recommended_action,
            "requires_immediate_attention": escalation.requires_immediate_attention
        }

    def _collect_conflict_evidence(
        self,
        conflict: Conflict
    ) -> List[Evidence]:
        """Collect all evidence from conflict"""
        all_evidence = []

        for position in conflict.positions:
            all_evidence.extend(position.evidence)

        # Add resolution evidence
        all_evidence.append(
            Evidence(
                id=f"{conflict.conflict_id}_resolution",
                source=self.agent_id,
                description=f"Resolved {conflict.type} conflict between {len(conflict.positions)} agents",
                weight=1.0
            )
        )

        return all_evidence

    def _format_positions(
        self,
        positions: List[AgentPosition]
    ) -> str:
        """Format positions for prompt"""
        formatted = []
        for i, pos in enumerate(positions, 1):
            formatted.append(f"""
Position {i} (Agent: {pos.agent_id}, Confidence: {pos.confidence:.2f}):
{pos.position}

Rationale:
{pos.rationale}

Evidence: {len(pos.evidence)} pieces of supporting evidence
""")
        return "\n".join(formatted)

    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get conflict resolution statistics"""
        total = len(self.resolved_conflicts) + len(self.active_conflicts)
        resolved = len(self.resolved_conflicts)
        escalated = sum(1 for c in self.resolved_conflicts.values() if c.escalated)

        return {
            "total_conflicts": total,
            "resolved_conflicts": resolved,
            "active_conflicts": len(self.active_conflicts),
            "escalated_conflicts": escalated,
            "resolution_rate": resolved / total if total > 0 else 0.0,
            "escalation_rate": escalated / total if total > 0 else 0.0,
            "conflicts_by_type": self._count_by_type(),
            "conflicts_by_severity": self._count_by_severity()
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count conflicts by type"""
        counts = {}
        for conflict in list(self.resolved_conflicts.values()) + list(self.active_conflicts.values()):
            counts[conflict.type] = counts.get(conflict.type, 0) + 1
        return counts

    def _count_by_severity(self) -> Dict[str, int]:
        """Count conflicts by severity"""
        counts = {}
        for conflict in list(self.resolved_conflicts.values()) + list(self.active_conflicts.values()):
            counts[conflict.severity] = counts.get(conflict.severity, 0) + 1
        return counts
