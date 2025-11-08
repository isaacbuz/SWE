"""
Incident response workflow using agent swarm

This workflow handles production incidents by coordinating multiple agents
to diagnose, fix, and document issues in parallel.
"""

from datetime import timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from temporalio import workflow
import asyncio

from ..activities.agent_activities import (
    analyze_logs,
    diagnose_issue,
    generate_fix,
    create_postmortem,
)
from ..activities.github_activities import (
    create_pull_request,
    create_issue,
)
from ..activities.tool_activities import (
    fetch_metrics,
    fetch_logs,
    run_tests,
)


@dataclass
class Alert:
    """Production alert"""
    id: str
    severity: str  # critical, high, medium, low
    service: str
    message: str
    timestamp: str
    metrics: Dict[str, Any]
    logs: List[str]


@dataclass
class Diagnosis:
    """Diagnosis from an agent"""
    agent_id: str
    root_cause: str
    confidence: float
    evidence: List[str]
    suggested_fix: str
    estimated_impact: str


@dataclass
class ConsensusResult:
    """Consensus on root cause"""
    root_cause: str
    confidence: float
    supporting_diagnoses: List[Diagnosis]
    conflicting_diagnoses: List[Diagnosis]


@dataclass
class IncidentResult:
    """Result of incident response"""
    alert_id: str
    consensus: ConsensusResult
    fix_applied: bool
    hotfix_pr_url: Optional[str]
    postmortem_url: Optional[str]
    resolution_time_minutes: float
    rollback_performed: bool


@workflow.defn
class IncidentSwarmWorkflow:
    """
    Incident response workflow that:
    1. Detects and analyzes alerts
    2. Spawns multiple diagnostic agents in parallel
    3. Reaches consensus on root cause
    4. Generates and applies automated fix
    5. Creates hotfix PR
    6. Generates post-mortem document
    """

    def __init__(self):
        self.alert: Optional[Alert] = None
        self.diagnoses: List[Diagnosis] = []
        self.consensus: Optional[ConsensusResult] = None
        self.fix_applied = False
        self.rollback_performed = False

    @workflow.run
    async def run(
        self,
        alert: Alert,
        num_diagnostic_agents: int = 3,
        auto_fix: bool = True,
    ) -> IncidentResult:
        """
        Execute incident response workflow

        Args:
            alert: Production alert to respond to
            num_diagnostic_agents: Number of agents to run in parallel for diagnosis
            auto_fix: Whether to automatically apply fixes

        Returns:
            IncidentResult with resolution details
        """
        start_time = workflow.now()
        workflow.logger.info(f"Incident response started for alert: {alert.id}")

        self.alert = alert

        # Step 1: Gather context (metrics and logs in parallel)
        workflow.logger.info("Step 1: Gathering context (metrics and logs)")
        metrics, logs = await asyncio.gather(
            workflow.execute_activity(
                fetch_metrics,
                args=[alert.service, alert.timestamp],
                start_to_close_timeout=timedelta(minutes=2),
            ),
            workflow.execute_activity(
                fetch_logs,
                args=[alert.service, alert.timestamp],
                start_to_close_timeout=timedelta(minutes=2),
            ),
        )

        # Update alert with gathered data
        self.alert.metrics = metrics
        self.alert.logs = logs

        # Step 2: Parallel diagnosis by multiple agents
        workflow.logger.info(f"Step 2: Running {num_diagnostic_agents} diagnostic agents in parallel")
        self.diagnoses = await asyncio.gather(*[
            workflow.execute_activity(
                diagnose_issue,
                args=[self.alert, i],
                start_to_close_timeout=timedelta(minutes=10),
                heartbeat_timeout=timedelta(minutes=2),
            )
            for i in range(num_diagnostic_agents)
        ])

        workflow.logger.info(f"Received {len(self.diagnoses)} diagnoses")

        # Step 3: Reach consensus on root cause
        workflow.logger.info("Step 3: Building consensus on root cause")
        self.consensus = await self._build_consensus(self.diagnoses)

        workflow.logger.info(
            f"Consensus reached: {self.consensus.root_cause} "
            f"(confidence: {self.consensus.confidence:.2f})"
        )

        # Step 4: Generate fix if confidence is high enough
        hotfix_pr_url = None
        if auto_fix and self.consensus.confidence >= 0.7:
            workflow.logger.info("Step 4: Generating automated fix")
            fix = await workflow.execute_activity(
                generate_fix,
                args=[self.consensus],
                start_to_close_timeout=timedelta(minutes=10),
            )

            # Step 5: Test the fix
            workflow.logger.info("Step 5: Testing the fix")
            test_result = await workflow.execute_activity(
                run_tests,
                args=[[fix]],
                start_to_close_timeout=timedelta(minutes=5),
            )

            if test_result['passed']:
                # Step 6: Create hotfix PR
                workflow.logger.info("Step 6: Creating hotfix PR")
                pr_result = await workflow.execute_activity(
                    create_pull_request,
                    args=[{
                        'branch': f"hotfix/{alert.id}",
                        'title': f"[HOTFIX] {alert.message}",
                        'description': self.consensus.root_cause,
                        'patches': [fix],
                        'labels': ['hotfix', 'incident', alert.severity],
                    }],
                    start_to_close_timeout=timedelta(minutes=2),
                )
                hotfix_pr_url = pr_result.pr_url
                self.fix_applied = True
                workflow.logger.info(f"Hotfix PR created: {hotfix_pr_url}")
            else:
                workflow.logger.warning("Fix tests failed, creating issue for manual intervention")
                await workflow.execute_activity(
                    create_issue,
                    args=[{
                        'title': f"[INCIDENT] {alert.message}",
                        'body': f"Automated fix failed tests.\n\nRoot cause: {self.consensus.root_cause}",
                        'labels': ['incident', 'needs-manual-fix', alert.severity],
                    }],
                    start_to_close_timeout=timedelta(minutes=1),
                )
        else:
            workflow.logger.info(
                f"Skipping auto-fix (confidence {self.consensus.confidence:.2f} < 0.7)"
            )

        # Step 7: Generate post-mortem document
        workflow.logger.info("Step 7: Generating post-mortem document")
        postmortem_url = await workflow.execute_activity(
            create_postmortem,
            args=[{
                'alert': self.alert,
                'diagnoses': self.diagnoses,
                'consensus': self.consensus,
                'fix_applied': self.fix_applied,
                'hotfix_pr_url': hotfix_pr_url,
            }],
            start_to_close_timeout=timedelta(minutes=5),
        )

        resolution_time = (workflow.now() - start_time).total_seconds() / 60

        result = IncidentResult(
            alert_id=alert.id,
            consensus=self.consensus,
            fix_applied=self.fix_applied,
            hotfix_pr_url=hotfix_pr_url,
            postmortem_url=postmortem_url,
            resolution_time_minutes=resolution_time,
            rollback_performed=self.rollback_performed,
        )

        workflow.logger.info(
            f"Incident response completed in {resolution_time:.1f} minutes"
        )

        return result

    async def _build_consensus(self, diagnoses: List[Diagnosis]) -> ConsensusResult:
        """
        Build consensus from multiple diagnoses using voting and confidence weighting
        """
        # Group diagnoses by similar root causes
        cause_groups: Dict[str, List[Diagnosis]] = {}

        for diagnosis in diagnoses:
            # Simple grouping by exact match (in production, use semantic similarity)
            cause = diagnosis.root_cause
            if cause not in cause_groups:
                cause_groups[cause] = []
            cause_groups[cause].append(diagnosis)

        # Find the root cause with highest weighted confidence
        best_cause = None
        best_score = 0.0
        best_group = []

        for cause, group in cause_groups.items():
            # Score is average confidence * number of supporting agents
            avg_confidence = sum(d.confidence for d in group) / len(group)
            score = avg_confidence * len(group)

            if score > best_score:
                best_score = score
                best_cause = cause
                best_group = group

        # Separate supporting and conflicting diagnoses
        supporting = best_group
        conflicting = [d for d in diagnoses if d not in best_group]

        # Overall confidence based on agreement
        agreement_ratio = len(supporting) / len(diagnoses)
        avg_confidence = sum(d.confidence for d in supporting) / len(supporting)
        overall_confidence = avg_confidence * agreement_ratio

        return ConsensusResult(
            root_cause=best_cause,
            confidence=overall_confidence,
            supporting_diagnoses=supporting,
            conflicting_diagnoses=conflicting,
        )

    @workflow.signal
    async def rollback(self):
        """Signal to rollback the applied fix"""
        workflow.logger.info("Rollback requested")
        self.rollback_performed = True
        # In production, trigger rollback activity

    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query current incident response status"""
        return {
            'alert_id': self.alert.id if self.alert else None,
            'diagnoses_count': len(self.diagnoses),
            'consensus_reached': self.consensus is not None,
            'consensus_confidence': self.consensus.confidence if self.consensus else 0.0,
            'fix_applied': self.fix_applied,
            'rollback_performed': self.rollback_performed,
        }


@workflow.defn
class ContinuousMonitoringWorkflow:
    """
    Long-running workflow that monitors for incidents and spawns
    IncidentSwarmWorkflow for each detected issue
    """

    def __init__(self):
        self.incidents_handled = 0
        self.active_incidents: List[str] = []

    @workflow.run
    async def run(self, service: str):
        """
        Continuously monitor a service and respond to incidents

        Args:
            service: Service name to monitor
        """
        workflow.logger.info(f"Starting continuous monitoring for {service}")

        while True:
            # Check for alerts every 30 seconds
            await asyncio.sleep(30)

            alerts = await workflow.execute_activity(
                fetch_metrics,
                args=[service, "now"],
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Spawn child workflow for each critical alert
            for alert_data in alerts.get('critical_alerts', []):
                alert = Alert(**alert_data)

                if alert.id not in self.active_incidents:
                    workflow.logger.info(f"Detected new incident: {alert.id}")
                    self.active_incidents.append(alert.id)

                    # Spawn child workflow for incident response
                    await workflow.execute_child_workflow(
                        IncidentSwarmWorkflow.run,
                        args=[alert],
                        id=f"incident-{alert.id}",
                    )

                    self.incidents_handled += 1

    @workflow.query
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            'incidents_handled': self.incidents_handled,
            'active_incidents': self.active_incidents,
        }
