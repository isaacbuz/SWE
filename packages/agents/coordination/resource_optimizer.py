"""
Resource Optimizer Agent

Tracks agent workload and availability, distributes work based on specialization,
prevents bottlenecks, provides dynamic scaling recommendations, and optimizes costs.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base import BaseAgent, Task, Context, AgentResult, TaskType
from protocol import Evidence
from registry import AgentRegistry, AgentCapability


class OptimizationGoal(str, Enum):
    """Optimization goals"""
    MINIMIZE_COST = "minimize_cost"
    MINIMIZE_TIME = "minimize_time"
    BALANCE = "balance"
    MAXIMIZE_QUALITY = "maximize_quality"


@dataclass
class WorkloadMetrics:
    """Workload metrics for an agent"""
    agent_id: str
    current_load: int
    max_capacity: int
    utilization: float  # 0.0-1.0
    avg_task_time_ms: float
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    total_cost: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BottleneckAnalysis:
    """Analysis of system bottlenecks"""
    bottleneck_type: str  # agent_capacity, task_queue, capability_shortage
    severity: str  # low, medium, high, critical
    affected_agents: List[str]
    affected_capabilities: List[str]
    impact: str
    recommendations: List[str]
    estimated_delay_minutes: float = 0.0


@dataclass
class ScalingRecommendation:
    """Recommendation for scaling agents"""
    action: str  # scale_up, scale_down, redistribute
    target_agents: List[str]
    target_capabilities: List[AgentCapability]
    rationale: str
    expected_improvement: str
    estimated_cost_impact: float
    priority: str  # low, medium, high, critical


class ResourceOptimizer(BaseAgent):
    """
    Resource Optimizer for agent workload management

    Features:
    - Real-time workload tracking
    - Bottleneck detection
    - Load balancing recommendations
    - Dynamic scaling suggestions
    - Cost optimization
    - Performance optimization
    """

    def __init__(
        self,
        agent_id: str = "resource_optimizer",
        registry: Optional[AgentRegistry] = None,
        optimization_goal: OptimizationGoal = OptimizationGoal.BALANCE,
        monitoring_interval_seconds: int = 60,
        max_utilization_threshold: float = 0.8,
        min_utilization_threshold: float = 0.2,
        **kwargs
    ):
        """
        Initialize resource optimizer

        Args:
            agent_id: Agent identifier
            registry: Agent registry
            optimization_goal: Primary optimization goal
            monitoring_interval_seconds: Monitoring interval
            max_utilization_threshold: Maximum utilization before scaling
            min_utilization_threshold: Minimum utilization before scaling down
            **kwargs: Additional BaseAgent arguments
        """
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.PLANNING,
            **kwargs
        )

        self.registry = registry
        self.optimization_goal = optimization_goal
        self.monitoring_interval = monitoring_interval_seconds
        self.max_utilization_threshold = max_utilization_threshold
        self.min_utilization_threshold = min_utilization_threshold

        # Metrics storage
        self.workload_history: Dict[str, List[WorkloadMetrics]] = {}
        self.bottlenecks: List[BottleneckAnalysis] = []
        self.scaling_recommendations: List[ScalingRecommendation] = []

        self.logger = logging.getLogger(f"Agent.{agent_id}")

    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return """You are a Resource Optimizer agent responsible for managing agent
workloads, detecting bottlenecks, and optimizing resource allocation.

Your responsibilities:
1. Monitor agent utilization and performance
2. Detect bottlenecks and capacity issues
3. Recommend load balancing strategies
4. Suggest dynamic scaling actions
5. Optimize for cost and performance
6. Prevent system degradation

When analyzing resource utilization:
- Consider both current load and trends
- Identify capability gaps
- Balance cost vs. performance
- Anticipate future bottlenecks
- Recommend proactive scaling

Provide recommendations in JSON format:
{
  "bottlenecks": [
    {
      "type": "bottleneck type",
      "severity": "low|medium|high|critical",
      "affected_agents": ["agent1", "agent2"],
      "impact": "description",
      "recommendations": ["action 1", "action 2"]
    }
  ],
  "scaling_recommendations": [
    {
      "action": "scale_up|scale_down|redistribute",
      "targets": ["agent1", "capability1"],
      "rationale": "explanation",
      "priority": "low|medium|high|critical"
    }
  ],
  "optimization_opportunities": ["opportunity 1", "opportunity 2"]
}"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute resource optimization

        Args:
            task: Task (typically periodic monitoring)
            context: Execution context

        Returns:
            Optimization recommendations
        """
        try:
            # Collect current metrics
            metrics = await self._collect_workload_metrics()

            # Analyze bottlenecks
            bottlenecks = await self._detect_bottlenecks(metrics, context)

            # Generate scaling recommendations
            recommendations = await self._generate_scaling_recommendations(
                metrics,
                bottlenecks,
                context
            )

            # Optimize task distribution
            distribution = await self._optimize_task_distribution(
                metrics,
                context
            )

            # Calculate cost optimization opportunities
            cost_savings = await self._identify_cost_optimizations(
                metrics,
                context
            )

            evidence = [
                self.create_evidence(
                    "resource_analysis",
                    f"Analyzed {len(metrics)} agents, found {len(bottlenecks)} bottlenecks"
                )
            ]

            return AgentResult(
                success=True,
                output={
                    "metrics": [self._metrics_to_dict(m) for m in metrics],
                    "bottlenecks": [self._bottleneck_to_dict(b) for b in bottlenecks],
                    "scaling_recommendations": [
                        self._recommendation_to_dict(r) for r in recommendations
                    ],
                    "distribution_recommendations": distribution,
                    "cost_optimization_opportunities": cost_savings,
                    "overall_health": self._calculate_system_health(metrics)
                },
                evidence=evidence,
                metadata={
                    "optimization_goal": self.optimization_goal.value,
                    "monitored_agents": len(metrics),
                    "critical_bottlenecks": sum(
                        1 for b in bottlenecks if b.severity == "critical"
                    )
                }
            )

        except Exception as e:
            self.logger.error(f"Resource optimization failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    async def _collect_workload_metrics(self) -> List[WorkloadMetrics]:
        """
        Collect current workload metrics from all agents

        Returns:
            List of workload metrics
        """
        if not self.registry:
            return []

        metrics = []

        for agent_id, registration in self.registry.registrations.items():
            utilization = (
                registration.current_load / registration.max_concurrent_tasks
                if registration.max_concurrent_tasks > 0 else 0.0
            )

            metric = WorkloadMetrics(
                agent_id=agent_id,
                current_load=registration.current_load,
                max_capacity=registration.max_concurrent_tasks,
                utilization=utilization,
                avg_task_time_ms=registration.avg_execution_time_ms,
                pending_tasks=0,  # Would come from task queue
                completed_tasks=registration.total_tasks_completed,
                failed_tasks=registration.total_tasks_failed,
                success_rate=registration.success_rate,
                total_cost=0.0  # Would accumulate from agent stats
            )

            metrics.append(metric)

            # Store in history
            if agent_id not in self.workload_history:
                self.workload_history[agent_id] = []
            self.workload_history[agent_id].append(metric)

            # Keep only last 1000 metrics
            if len(self.workload_history[agent_id]) > 1000:
                self.workload_history[agent_id] = self.workload_history[agent_id][-1000:]

        return metrics

    async def _detect_bottlenecks(
        self,
        metrics: List[WorkloadMetrics],
        context: Context
    ) -> List[BottleneckAnalysis]:
        """
        Detect system bottlenecks

        Args:
            metrics: Current workload metrics
            context: Execution context

        Returns:
            List of detected bottlenecks
        """
        bottlenecks = []

        # Check for overutilized agents
        overutilized = [
            m for m in metrics
            if m.utilization > self.max_utilization_threshold
        ]
        if overutilized:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_type="agent_capacity",
                severity=self._calculate_severity(overutilized, metrics),
                affected_agents=[m.agent_id for m in overutilized],
                affected_capabilities=[],
                impact=f"{len(overutilized)} agents operating above {self.max_utilization_threshold*100}% capacity",
                recommendations=[
                    "Scale up affected agents",
                    "Redistribute workload to underutilized agents",
                    "Consider adding more agent instances"
                ],
                estimated_delay_minutes=sum(m.avg_task_time_ms / 60000 for m in overutilized)
            ))

        # Check for failing agents
        failing = [
            m for m in metrics
            if m.success_rate < 0.8 and m.completed_tasks > 10
        ]
        if failing:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_type="agent_reliability",
                severity="high" if any(m.success_rate < 0.5 for m in failing) else "medium",
                affected_agents=[m.agent_id for m in failing],
                affected_capabilities=[],
                impact=f"{len(failing)} agents with success rate below 80%",
                recommendations=[
                    "Investigate agent failures",
                    "Reassign tasks from unreliable agents",
                    "Consider agent maintenance or replacement"
                ]
            ))

        # Check for capability shortages
        if self.registry:
            capability_bottlenecks = await self._detect_capability_bottlenecks()
            bottlenecks.extend(capability_bottlenecks)

        self.bottlenecks = bottlenecks
        return bottlenecks

    async def _detect_capability_bottlenecks(self) -> List[BottleneckAnalysis]:
        """Detect bottlenecks in specific capabilities"""
        bottlenecks = []

        if not self.registry:
            return bottlenecks

        for capability in AgentCapability:
            agents = await self.registry.find_agents_by_capability(
                capability,
                only_available=False
            )

            available = await self.registry.find_agents_by_capability(
                capability,
                only_available=True
            )

            # Check if capability is under-resourced
            if len(agents) > 0 and len(available) == 0:
                bottlenecks.append(BottleneckAnalysis(
                    bottleneck_type="capability_shortage",
                    severity="high",
                    affected_agents=agents,
                    affected_capabilities=[capability.value],
                    impact=f"No available agents for {capability.value}",
                    recommendations=[
                        f"Add more agents with {capability.value} capability",
                        "Wait for existing agents to become available",
                        "Consider task prioritization"
                    ]
                ))

        return bottlenecks

    async def _generate_scaling_recommendations(
        self,
        metrics: List[WorkloadMetrics],
        bottlenecks: List[BottleneckAnalysis],
        context: Context
    ) -> List[ScalingRecommendation]:
        """
        Generate scaling recommendations

        Args:
            metrics: Current workload metrics
            bottlenecks: Detected bottlenecks
            context: Execution context

        Returns:
            List of scaling recommendations
        """
        recommendations = []

        # Scale up overutilized agents
        overutilized = [
            m for m in metrics
            if m.utilization > self.max_utilization_threshold
        ]
        if overutilized:
            recommendations.append(ScalingRecommendation(
                action="scale_up",
                target_agents=[m.agent_id for m in overutilized],
                target_capabilities=[],
                rationale=f"{len(overutilized)} agents operating above capacity",
                expected_improvement=f"Reduce wait times by ~{len(overutilized) * 30}%",
                estimated_cost_impact=len(overutilized) * 100.0,  # Estimated cost
                priority="high" if len(overutilized) > 3 else "medium"
            ))

        # Scale down underutilized agents
        underutilized = [
            m for m in metrics
            if m.utilization < self.min_utilization_threshold and m.completed_tasks > 0
        ]
        if len(underutilized) > 2:  # Only recommend if multiple agents
            recommendations.append(ScalingRecommendation(
                action="scale_down",
                target_agents=[m.agent_id for m in underutilized],
                target_capabilities=[],
                rationale=f"{len(underutilized)} agents underutilized (< {self.min_utilization_threshold*100}%)",
                expected_improvement=f"Reduce costs by ~{len(underutilized) * 15}%",
                estimated_cost_impact=-len(underutilized) * 50.0,  # Cost savings
                priority="low"
            ))

        # Address capability shortages
        capability_bottlenecks = [
            b for b in bottlenecks
            if b.bottleneck_type == "capability_shortage"
        ]
        for bottleneck in capability_bottlenecks:
            recommendations.append(ScalingRecommendation(
                action="scale_up",
                target_agents=[],
                target_capabilities=[AgentCapability(c) for c in bottleneck.affected_capabilities],
                rationale=bottleneck.impact,
                expected_improvement="Eliminate capability bottleneck",
                estimated_cost_impact=100.0,
                priority=bottleneck.severity
            ))

        self.scaling_recommendations = recommendations
        return recommendations

    async def _optimize_task_distribution(
        self,
        metrics: List[WorkloadMetrics],
        context: Context
    ) -> Dict[str, Any]:
        """
        Optimize task distribution across agents

        Args:
            metrics: Current workload metrics
            context: Execution context

        Returns:
            Distribution recommendations
        """
        if not metrics:
            return {}

        # Calculate optimal distribution
        total_capacity = sum(m.max_capacity for m in metrics)
        total_load = sum(m.current_load for m in metrics)

        if total_capacity == 0:
            return {}

        avg_utilization = total_load / total_capacity

        # Find imbalances
        overloaded = [m for m in metrics if m.utilization > avg_utilization * 1.5]
        underloaded = [m for m in metrics if m.utilization < avg_utilization * 0.5]

        recommendations = []

        if overloaded and underloaded:
            for over in overloaded:
                # Calculate how many tasks to redistribute
                excess_load = int(over.current_load - (over.max_capacity * avg_utilization))
                if excess_load > 0:
                    recommendations.append({
                        "from_agent": over.agent_id,
                        "tasks_to_redistribute": excess_load,
                        "target_agents": [u.agent_id for u in underloaded[:3]],
                        "expected_improvement": f"Balance load, reduce {over.agent_id} utilization by {excess_load/over.max_capacity*100:.1f}%"
                    })

        return {
            "current_utilization": avg_utilization,
            "optimal_utilization": 0.7,  # Target 70% utilization
            "redistribution_needed": len(recommendations) > 0,
            "recommendations": recommendations,
            "load_imbalance_score": self._calculate_imbalance_score(metrics)
        }

    async def _identify_cost_optimizations(
        self,
        metrics: List[WorkloadMetrics],
        context: Context
    ) -> List[Dict[str, Any]]:
        """
        Identify cost optimization opportunities

        Args:
            metrics: Current workload metrics
            context: Execution context

        Returns:
            List of cost optimization opportunities
        """
        opportunities = []

        # Identify idle agents
        idle_agents = [
            m for m in metrics
            if m.current_load == 0 and m.completed_tasks > 0
        ]
        if idle_agents:
            potential_savings = len(idle_agents) * 50.0  # Estimated
            opportunities.append({
                "type": "idle_agents",
                "description": f"{len(idle_agents)} agents are idle",
                "affected_agents": [m.agent_id for m in idle_agents],
                "potential_savings_usd": potential_savings,
                "recommendation": "Consider scaling down or reassigning idle agents"
            })

        # Identify redundant capabilities
        if self.registry:
            for capability in AgentCapability:
                agents = await self.registry.find_agents_by_capability(
                    capability,
                    only_available=False
                )
                if len(agents) > 5:  # Arbitrary threshold
                    opportunities.append({
                        "type": "capability_redundancy",
                        "description": f"{len(agents)} agents have {capability.value} capability",
                        "capability": capability.value,
                        "agent_count": len(agents),
                        "recommendation": "Consider consolidating or redistributing capabilities"
                    })

        return opportunities

    def _calculate_severity(
        self,
        affected: List[WorkloadMetrics],
        all_metrics: List[WorkloadMetrics]
    ) -> str:
        """Calculate bottleneck severity"""
        if not all_metrics:
            return "low"

        ratio = len(affected) / len(all_metrics)

        if ratio > 0.5:
            return "critical"
        elif ratio > 0.3:
            return "high"
        elif ratio > 0.1:
            return "medium"
        else:
            return "low"

    def _calculate_system_health(
        self,
        metrics: List[WorkloadMetrics]
    ) -> Dict[str, Any]:
        """Calculate overall system health score"""
        if not metrics:
            return {"score": 0.0, "status": "unknown"}

        # Calculate various health factors
        avg_utilization = statistics.mean(m.utilization for m in metrics)
        avg_success_rate = statistics.mean(m.success_rate for m in metrics)
        utilization_variance = statistics.variance(m.utilization for m in metrics) if len(metrics) > 1 else 0

        # Health score (0-100)
        # Penalize both over and under utilization
        utilization_score = max(0, 100 - abs(avg_utilization - 0.7) * 100)
        success_score = avg_success_rate * 100
        balance_score = max(0, 100 - utilization_variance * 200)

        overall_score = (utilization_score + success_score + balance_score) / 3

        if overall_score >= 80:
            status = "healthy"
        elif overall_score >= 60:
            status = "fair"
        elif overall_score >= 40:
            status = "degraded"
        else:
            status = "critical"

        return {
            "score": overall_score,
            "status": status,
            "utilization_score": utilization_score,
            "success_score": success_score,
            "balance_score": balance_score,
            "avg_utilization": avg_utilization,
            "avg_success_rate": avg_success_rate
        }

    def _calculate_imbalance_score(
        self,
        metrics: List[WorkloadMetrics]
    ) -> float:
        """Calculate load imbalance score (0-1, lower is better)"""
        if not metrics:
            return 0.0

        utilizations = [m.utilization for m in metrics]
        if len(utilizations) == 1:
            return 0.0

        return statistics.stdev(utilizations)

    def _metrics_to_dict(self, metrics: WorkloadMetrics) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "agent_id": metrics.agent_id,
            "current_load": metrics.current_load,
            "max_capacity": metrics.max_capacity,
            "utilization": metrics.utilization,
            "avg_task_time_ms": metrics.avg_task_time_ms,
            "success_rate": metrics.success_rate
        }

    def _bottleneck_to_dict(self, bottleneck: BottleneckAnalysis) -> Dict[str, Any]:
        """Convert bottleneck to dictionary"""
        return {
            "type": bottleneck.bottleneck_type,
            "severity": bottleneck.severity,
            "affected_agents": bottleneck.affected_agents,
            "impact": bottleneck.impact,
            "recommendations": bottleneck.recommendations
        }

    def _recommendation_to_dict(self, rec: ScalingRecommendation) -> Dict[str, Any]:
        """Convert recommendation to dictionary"""
        return {
            "action": rec.action,
            "target_agents": rec.target_agents,
            "target_capabilities": [c.value for c in rec.target_capabilities],
            "rationale": rec.rationale,
            "expected_improvement": rec.expected_improvement,
            "estimated_cost_impact": rec.estimated_cost_impact,
            "priority": rec.priority
        }
