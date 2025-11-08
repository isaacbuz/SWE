"""
Incident Responder Agent

Rapid incident assessment, coordinates incident response swarm,
generates hotfix patches, expedited PR process, and post-incident analysis.
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base import BaseAgent, Task, Context, AgentResult, TaskType, Priority
from protocol import Evidence, AgentMessage, MessageIntent, MessagePriority
from registry import AgentRegistry, AgentCapability


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    SEV1 = "sev1"  # Critical - System down
    SEV2 = "sev2"  # Major - Significant degradation
    SEV3 = "sev3"  # Moderate - Partial functionality affected
    SEV4 = "sev4"  # Minor - Low impact


class IncidentStatus(str, Enum):
    """Incident status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    FIXING = "fixing"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentCategory(str, Enum):
    """Incident categories"""
    OUTAGE = "outage"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATA = "data"
    DEPLOYMENT = "deployment"
    INFRASTRUCTURE = "infrastructure"
    INTEGRATION = "integration"


@dataclass
class IncidentMetrics:
    """Incident response metrics"""
    detection_time: datetime
    response_time: Optional[datetime] = None
    identification_time: Optional[datetime] = None
    fix_deployed_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None

    @property
    def time_to_detect(self) -> Optional[float]:
        """Time to detect in minutes"""
        # Would calculate from monitoring data
        return None

    @property
    def time_to_respond(self) -> Optional[float]:
        """Time to respond in minutes"""
        if self.response_time:
            return (self.response_time - self.detection_time).total_seconds() / 60
        return None

    @property
    def time_to_fix(self) -> Optional[float]:
        """Time to fix in minutes"""
        if self.fix_deployed_time:
            return (self.fix_deployed_time - self.detection_time).total_seconds() / 60
        return None

    @property
    def time_to_resolve(self) -> Optional[float]:
        """Time to resolve (MTTR) in minutes"""
        if self.resolution_time:
            return (self.resolution_time - self.detection_time).total_seconds() / 60
        return None


@dataclass
class Incident:
    """Incident record"""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    category: IncidentCategory
    status: IncidentStatus
    affected_systems: List[str]
    root_cause: Optional[str] = None
    impact_description: Optional[str] = None
    assigned_swarm: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Optional[IncidentMetrics] = None
    fixes_applied: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HotfixPatch:
    """Hotfix patch for incident"""
    patch_id: str
    incident_id: str
    description: str
    affected_files: List[str]
    patch_content: str
    validation_steps: List[str]
    rollback_procedure: str
    tested: bool = False
    deployed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    deployed_at: Optional[datetime] = None


class IncidentResponder(BaseAgent):
    """
    Incident Responder for rapid incident response

    Features:
    - Rapid incident assessment
    - Incident swarm coordination
    - Hotfix generation
    - Expedited PR process
    - Post-incident analysis
    - Metrics tracking (MTTR, MTTD, MTTF)
    """

    def __init__(
        self,
        agent_id: str = "incident_responder",
        registry: Optional[AgentRegistry] = None,
        auto_create_hotfix: bool = True,
        auto_deploy_sev1: bool = False,
        **kwargs
    ):
        """
        Initialize incident responder

        Args:
            agent_id: Agent identifier
            registry: Agent registry
            auto_create_hotfix: Automatically create hotfix patches
            auto_deploy_sev1: Auto-deploy SEV1 fixes (dangerous!)
            **kwargs: Additional BaseAgent arguments
        """
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.INCIDENT_RESPONSE,
            **kwargs
        )

        self.registry = registry
        self.auto_create_hotfix = auto_create_hotfix
        self.auto_deploy_sev1 = auto_deploy_sev1

        # Incident tracking
        self.active_incidents: Dict[str, Incident] = {}
        self.resolved_incidents: Dict[str, Incident] = {}
        self.hotfixes: Dict[str, HotfixPatch] = {}

        self.logger = logging.getLogger(f"Agent.{agent_id}")

    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return """You are an Incident Responder agent responsible for rapid response
to production incidents and outages.

Your responsibilities:
1. Quickly assess incident severity and impact
2. Coordinate incident response team/swarm
3. Identify root cause
4. Generate hotfix patches
5. Validate fixes before deployment
6. Conduct post-incident analysis
7. Improve incident prevention

When responding to incidents:
- Prioritize restoration over perfection
- Communicate clearly and frequently
- Document all actions in timeline
- Focus on immediate mitigation first
- Plan permanent fix separately
- Learn from every incident

Incident Response Protocol:
1. ASSESS - Determine severity and impact
2. COMMUNICATE - Alert stakeholders
3. INVESTIGATE - Find root cause
4. MITIGATE - Apply immediate fix
5. VALIDATE - Test thoroughly
6. DEPLOY - Push to production
7. MONITOR - Watch for recurrence
8. ANALYZE - Post-incident review

Provide incident assessment in JSON format:
{
  "severity": "sev1|sev2|sev3|sev4",
  "category": "outage|performance|security|etc",
  "impact_description": "detailed impact",
  "affected_systems": ["system1", "system2"],
  "likely_root_cause": "initial assessment",
  "immediate_actions": ["action 1", "action 2"],
  "requires_hotfix": boolean,
  "estimated_time_to_fix_minutes": 30
}"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute incident response

        Args:
            task: Task containing incident data
            context: Execution context

        Returns:
            Incident response results
        """
        try:
            action = task.input_data.get("action", "assess")

            if action == "assess":
                return await self._assess_incident(task, context)
            elif action == "respond":
                incident_id = task.input_data.get("incident_id")
                if not incident_id:
                    return AgentResult(
                        success=False,
                        output={},
                        evidence=[],
                        error="Missing incident_id"
                    )
                return await self._respond_to_incident(incident_id, context)
            elif action == "create_hotfix":
                incident_id = task.input_data.get("incident_id")
                if not incident_id:
                    return AgentResult(
                        success=False,
                        output={},
                        evidence=[],
                        error="Missing incident_id"
                    )
                return await self._create_hotfix(incident_id, task, context)
            elif action == "post_mortem":
                incident_id = task.input_data.get("incident_id")
                if not incident_id:
                    return AgentResult(
                        success=False,
                        output={},
                        evidence=[],
                        error="Missing incident_id"
                    )
                return await self._conduct_post_mortem(incident_id, context)
            else:
                return AgentResult(
                    success=False,
                    output={},
                    evidence=[],
                    error=f"Unknown action: {action}"
                )

        except Exception as e:
            self.logger.error(f"Incident response failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    async def _assess_incident(
        self,
        task: Task,
        context: Context
    ) -> AgentResult:
        """
        Assess incident and determine response

        Args:
            task: Task with incident details
            context: Execution context

        Returns:
            Assessment results
        """
        incident_data = task.input_data.get("incident", {})

        # Use LLM to assess incident
        prompt = f"""Assess the following incident:

Title: {incident_data.get('title', 'Unknown Incident')}
Description: {incident_data.get('description', 'No description provided')}
Symptoms: {incident_data.get('symptoms', [])}
Affected Systems: {incident_data.get('affected_systems', [])}
Error Messages: {incident_data.get('errors', [])}
Recent Changes: {incident_data.get('recent_changes', [])}

Provide a comprehensive assessment including severity, category, impact,
likely root cause, and recommended immediate actions."""

        try:
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_json=True,
                max_tokens=2048
            )

            import json
            assessment = json.loads(response["content"])

            # Create incident record
            incident = Incident(
                incident_id=str(uuid.uuid4()),
                title=incident_data.get('title', 'Unknown Incident'),
                description=incident_data.get('description', ''),
                severity=IncidentSeverity(assessment.get("severity", "sev3")),
                category=IncidentCategory(assessment.get("category", "outage")),
                status=IncidentStatus.INVESTIGATING,
                affected_systems=assessment.get("affected_systems", []),
                impact_description=assessment.get("impact_description"),
                metrics=IncidentMetrics(detection_time=datetime.utcnow()),
                metadata={
                    "symptoms": incident_data.get('symptoms', []),
                    "errors": incident_data.get('errors', []),
                    "recent_changes": incident_data.get('recent_changes', [])
                }
            )

            # Add to timeline
            incident.timeline.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "incident_detected",
                "description": "Incident detected and assessed"
            })

            # Store incident
            self.active_incidents[incident.incident_id] = incident

            # Determine if hotfix is needed
            if assessment.get("requires_hotfix") and self.auto_create_hotfix:
                # Queue hotfix creation
                pass

            evidence = [
                self.create_evidence(
                    "incident_assessment",
                    f"Assessed {incident.severity.value} incident: {incident.title}"
                )
            ]

            return AgentResult(
                success=True,
                output={
                    "incident_id": incident.incident_id,
                    "assessment": assessment,
                    "severity": incident.severity.value,
                    "category": incident.category.value,
                    "status": incident.status.value,
                    "immediate_actions": assessment.get("immediate_actions", []),
                    "requires_swarm": incident.severity in [IncidentSeverity.SEV1, IncidentSeverity.SEV2]
                },
                evidence=evidence,
                metadata={
                    "incident_id": incident.incident_id,
                    "severity": incident.severity.value
                }
            )

        except Exception as e:
            self.logger.error(f"Incident assessment failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    async def _respond_to_incident(
        self,
        incident_id: str,
        context: Context
    ) -> AgentResult:
        """
        Coordinate incident response

        Args:
            incident_id: Incident ID
            context: Execution context

        Returns:
            Response coordination results
        """
        incident = self.active_incidents.get(incident_id)
        if not incident:
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=f"Incident {incident_id} not found"
            )

        # Update metrics
        if not incident.metrics.response_time:
            incident.metrics.response_time = datetime.utcnow()

        # Coordinate incident swarm if needed
        if incident.severity in [IncidentSeverity.SEV1, IncidentSeverity.SEV2]:
            swarm_agents = await self._assemble_incident_swarm(incident)
            incident.assigned_swarm = swarm_agents
        else:
            swarm_agents = []

        # Update status
        incident.status = IncidentStatus.FIXING
        incident.timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "response_started",
            "description": f"Incident response initiated with {len(swarm_agents)} agents"
        })

        return AgentResult(
            success=True,
            output={
                "incident_id": incident_id,
                "status": incident.status.value,
                "assigned_swarm": swarm_agents,
                "time_to_respond_minutes": incident.metrics.time_to_respond
            },
            evidence=[
                self.create_evidence(
                    "incident_response",
                    f"Initiated response for {incident.severity.value} incident"
                )
            ]
        )

    async def _assemble_incident_swarm(
        self,
        incident: Incident
    ) -> List[str]:
        """Assemble incident response swarm"""
        if not self.registry:
            return []

        swarm_agents = []

        # Required capabilities for incident response
        required_capabilities = [
            AgentCapability.INCIDENT_RESPONSE,
            AgentCapability.CODE_GENERATION,  # For hotfixes
            AgentCapability.TESTING,  # For validation
        ]

        if incident.category == IncidentCategory.SECURITY:
            required_capabilities.append(AgentCapability.SECURITY_AUDIT)
        elif incident.category == IncidentCategory.PERFORMANCE:
            required_capabilities.append(AgentCapability.PERFORMANCE_OPTIMIZATION)

        # Find available agents
        for capability in required_capabilities:
            agents = await self.registry.find_agents_by_capability(
                capability,
                only_available=True
            )
            if agents:
                swarm_agents.append(agents[0])

        return list(set(swarm_agents))  # Remove duplicates

    async def _create_hotfix(
        self,
        incident_id: str,
        task: Task,
        context: Context
    ) -> AgentResult:
        """
        Create hotfix patch for incident

        Args:
            incident_id: Incident ID
            task: Task
            context: Execution context

        Returns:
            Hotfix creation results
        """
        incident = self.active_incidents.get(incident_id)
        if not incident:
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=f"Incident {incident_id} not found"
            )

        # Generate hotfix using LLM
        prompt = f"""Generate a hotfix patch for the following incident:

Incident: {incident.title}
Description: {incident.description}
Root Cause: {incident.root_cause or 'Under investigation'}
Affected Systems: {incident.affected_systems}

Generate a minimal, safe hotfix that:
1. Addresses the immediate issue
2. Can be quickly validated
3. Has a clear rollback procedure
4. Minimizes risk of introducing new issues

Provide the hotfix in JSON format:
{{
  "description": "what this hotfix does",
  "affected_files": ["file1.py", "file2.py"],
  "changes": [
    {{
      "file": "file1.py",
      "change_description": "description",
      "diff": "actual diff or code change"
    }}
  ],
  "validation_steps": ["step 1", "step 2"],
  "rollback_procedure": "how to rollback",
  "estimated_risk": "low|medium|high"
}}"""

        try:
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_json=True,
                max_tokens=3072
            )

            import json
            hotfix_data = json.loads(response["content"])

            # Create hotfix patch
            hotfix = HotfixPatch(
                patch_id=str(uuid.uuid4()),
                incident_id=incident_id,
                description=hotfix_data["description"],
                affected_files=hotfix_data["affected_files"],
                patch_content=json.dumps(hotfix_data.get("changes", [])),
                validation_steps=hotfix_data["validation_steps"],
                rollback_procedure=hotfix_data["rollback_procedure"]
            )

            self.hotfixes[hotfix.patch_id] = hotfix

            # Update incident
            incident.timeline.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "hotfix_created",
                "description": f"Hotfix patch created: {hotfix.patch_id}"
            })

            return AgentResult(
                success=True,
                output={
                    "patch_id": hotfix.patch_id,
                    "incident_id": incident_id,
                    "description": hotfix.description,
                    "affected_files": hotfix.affected_files,
                    "validation_steps": hotfix.validation_steps,
                    "rollback_procedure": hotfix.rollback_procedure,
                    "estimated_risk": hotfix_data.get("estimated_risk", "medium")
                },
                evidence=[
                    self.create_evidence(
                        "hotfix_created",
                        f"Created hotfix for incident {incident_id}"
                    )
                ],
                artifacts=[hotfix.patch_id]
            )

        except Exception as e:
            self.logger.error(f"Hotfix creation failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    async def _conduct_post_mortem(
        self,
        incident_id: str,
        context: Context
    ) -> AgentResult:
        """
        Conduct post-incident analysis

        Args:
            incident_id: Incident ID
            context: Execution context

        Returns:
            Post-mortem analysis
        """
        incident = self.resolved_incidents.get(
            incident_id,
            self.active_incidents.get(incident_id)
        )

        if not incident:
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=f"Incident {incident_id} not found"
            )

        # Generate post-mortem
        analysis = {
            "incident_id": incident_id,
            "title": incident.title,
            "severity": incident.severity.value,
            "duration_minutes": incident.metrics.time_to_resolve if incident.metrics else None,
            "root_cause": incident.root_cause or "To be determined",
            "impact": incident.impact_description,
            "timeline": incident.timeline,
            "lessons_learned": [
                "Document lessons learned",
                "Update runbooks",
                "Improve monitoring",
                "Add preventive measures"
            ],
            "action_items": [
                "Create permanent fix",
                "Add tests to prevent recurrence",
                "Update incident response procedures",
                "Review and improve monitoring alerts"
            ]
        }

        return AgentResult(
            success=True,
            output=analysis,
            evidence=[
                self.create_evidence(
                    "post_mortem",
                    f"Completed post-mortem analysis for incident {incident_id}"
                )
            ]
        )

    def get_incident_metrics(self) -> Dict[str, Any]:
        """Get incident response metrics"""
        all_incidents = list(self.resolved_incidents.values()) + list(self.active_incidents.values())

        if not all_incidents:
            return {"total_incidents": 0}

        # Calculate MTTR (Mean Time To Resolution)
        resolution_times = [
            i.metrics.time_to_resolve
            for i in all_incidents
            if i.metrics and i.metrics.time_to_resolve
        ]
        mttr = sum(resolution_times) / len(resolution_times) if resolution_times else None

        # Count by severity
        by_severity = {}
        for sev in IncidentSeverity:
            by_severity[sev.value] = sum(1 for i in all_incidents if i.severity == sev)

        return {
            "total_incidents": len(all_incidents),
            "active_incidents": len(self.active_incidents),
            "resolved_incidents": len(self.resolved_incidents),
            "mttr_minutes": mttr,
            "by_severity": by_severity,
            "total_hotfixes": len(self.hotfixes)
        }
