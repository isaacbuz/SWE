"""
Swarm Coordinator Agent

Manages parallel agent execution for large tasks. Decomposes tasks into subtasks,
assigns to appropriate agents, monitors progress, aggregates results, handles failures,
and optimizes for cost and time.
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import uuid

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base import BaseAgent, Task, Context, AgentResult, TaskType, Priority
from protocol import (
    AgentMessage, HandoffRequest, HandoffReason, Evidence,
    MessageIntent, MessagePriority
)
from registry import AgentRegistry, AgentCapability


@dataclass
class SubTask:
    """Subtask within a swarm execution"""
    id: str
    parent_task_id: str
    task: Task
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, assigned, running, completed, failed
    result: Optional[AgentResult] = None
    dependencies: List[str] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class SwarmExecution:
    """State for a swarm execution"""
    swarm_id: str
    parent_task: Task
    subtasks: List[SubTask]
    strategy: str  # parallel, sequential, dag
    total_subtasks: int = 0
    completed_subtasks: int = 0
    failed_subtasks: int = 0
    total_cost: float = 0.0
    total_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SwarmCoordinator(BaseAgent):
    """
    Swarm Coordinator for parallel agent orchestration

    Features:
    - Task decomposition into parallel subtasks
    - Intelligent agent assignment based on capabilities
    - Progress monitoring and aggregation
    - Failure handling with retry and reassignment
    - Cost and time optimization
    - Dynamic load balancing
    """

    def __init__(
        self,
        agent_id: str = "swarm_coordinator",
        registry: Optional[AgentRegistry] = None,
        max_parallel_agents: int = 10,
        enable_cost_optimization: bool = True,
        enable_time_optimization: bool = True,
        **kwargs
    ):
        """
        Initialize swarm coordinator

        Args:
            agent_id: Agent identifier
            registry: Agent registry for agent management
            max_parallel_agents: Maximum parallel agents
            enable_cost_optimization: Enable cost optimization
            enable_time_optimization: Enable time optimization
            **kwargs: Additional BaseAgent arguments
        """
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.PLANNING,
            **kwargs
        )

        self.registry = registry
        self.max_parallel_agents = max_parallel_agents
        self.enable_cost_optimization = enable_cost_optimization
        self.enable_time_optimization = enable_time_optimization

        # Active swarms
        self.active_swarms: Dict[str, SwarmExecution] = {}

        self.logger = logging.getLogger(f"Agent.{agent_id}")

    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return """You are a Swarm Coordinator agent responsible for decomposing large tasks
into parallel subtasks and orchestrating their execution across multiple specialized agents.

Your responsibilities:
1. Analyze complex tasks and decompose them into independent subtasks
2. Identify dependencies between subtasks
3. Assign subtasks to the most appropriate agents based on capabilities
4. Monitor progress and handle failures
5. Aggregate results from all subtasks
6. Optimize for both cost and execution time

When decomposing tasks:
- Break down into the smallest independent units
- Identify and document dependencies clearly
- Ensure each subtask has clear inputs and outputs
- Consider agent capabilities and availability
- Balance load across available agents

Provide decomposition in JSON format:
{
  "subtasks": [
    {
      "description": "subtask description",
      "type": "task_type",
      "dependencies": ["subtask_id1", "subtask_id2"],
      "estimated_complexity": "low|medium|high",
      "required_capabilities": ["capability1", "capability2"]
    }
  ],
  "execution_strategy": "parallel|sequential|dag",
  "estimated_total_time_minutes": 10,
  "rationale": "explanation of decomposition approach"
}"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute task by coordinating a swarm of agents

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Aggregated result from all subtasks
        """
        start_time = datetime.utcnow()
        swarm_id = str(uuid.uuid4())

        try:
            # Step 1: Decompose task into subtasks
            self.logger.info(f"Decomposing task {task.id} into subtasks")
            subtasks = await self._decompose_task(task, context)

            if not subtasks:
                return AgentResult(
                    success=False,
                    output={},
                    evidence=[],
                    error="Failed to decompose task into subtasks"
                )

            # Create swarm execution
            swarm = SwarmExecution(
                swarm_id=swarm_id,
                parent_task=task,
                subtasks=subtasks,
                strategy=self._determine_strategy(subtasks),
                total_subtasks=len(subtasks)
            )
            self.active_swarms[swarm_id] = swarm

            # Step 2: Execute subtasks
            self.logger.info(
                f"Executing {len(subtasks)} subtasks with strategy: {swarm.strategy}"
            )
            results = await self._execute_swarm(swarm, context)

            # Step 3: Aggregate results
            self.logger.info(f"Aggregating results from {len(results)} subtasks")
            aggregated = await self._aggregate_results(swarm, results, context)

            # Update swarm stats
            swarm.completed_at = datetime.utcnow()
            total_time = (swarm.completed_at - swarm.created_at).total_seconds() * 1000
            swarm.total_time_ms = int(total_time)

            # Create evidence
            evidence = [
                self.create_evidence(
                    "swarm_execution",
                    f"Coordinated {swarm.total_subtasks} subtasks, "
                    f"{swarm.completed_subtasks} completed, "
                    f"{swarm.failed_subtasks} failed"
                )
            ]

            return AgentResult(
                success=swarm.failed_subtasks == 0,
                output=aggregated,
                evidence=evidence,
                metadata={
                    "swarm_id": swarm_id,
                    "total_subtasks": swarm.total_subtasks,
                    "completed_subtasks": swarm.completed_subtasks,
                    "failed_subtasks": swarm.failed_subtasks,
                    "total_cost": swarm.total_cost,
                    "total_time_ms": swarm.total_time_ms,
                    "strategy": swarm.strategy
                }
            )

        except Exception as e:
            self.logger.error(f"Swarm coordination failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    async def _decompose_task(
        self,
        task: Task,
        context: Context
    ) -> List[SubTask]:
        """
        Decompose task into subtasks using LLM

        Args:
            task: Task to decompose
            context: Execution context

        Returns:
            List of subtasks
        """
        prompt = f"""Decompose the following task into independent subtasks that can be executed in parallel:

Task: {task.description}
Type: {task.type.value}
Priority: {task.priority.value}

Input Data: {task.input_data}

Context:
Project: {context.project_path}
Additional Context: {context.metadata}

Analyze the task and break it down into the smallest independent units of work.
Identify dependencies between subtasks and recommend an execution strategy."""

        try:
            # Invoke model for decomposition
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_json=True,
                max_tokens=4096
            )

            # Parse decomposition
            import json
            decomposition = json.loads(response["content"])

            # Create subtasks
            subtasks = []
            for i, subtask_def in enumerate(decomposition.get("subtasks", [])):
                subtask = SubTask(
                    id=f"{task.id}_subtask_{i}",
                    parent_task_id=task.id,
                    task=Task(
                        id=f"{task.id}_subtask_{i}",
                        type=TaskType(subtask_def.get("type", task.type.value)),
                        description=subtask_def["description"],
                        input_data=subtask_def.get("input_data", {}),
                        priority=task.priority,
                        dependencies=subtask_def.get("dependencies", []),
                        metadata={
                            "required_capabilities": subtask_def.get("required_capabilities", []),
                            "estimated_complexity": subtask_def.get("estimated_complexity", "medium")
                        }
                    ),
                    dependencies=subtask_def.get("dependencies", [])
                )
                subtasks.append(subtask)

            self.logger.info(f"Decomposed into {len(subtasks)} subtasks")
            return subtasks

        except Exception as e:
            self.logger.error(f"Task decomposition failed: {e}")
            return []

    def _determine_strategy(self, subtasks: List[SubTask]) -> str:
        """Determine execution strategy based on dependencies"""
        has_dependencies = any(st.dependencies for st in subtasks)

        if not has_dependencies:
            return "parallel"
        elif all(len(st.dependencies) <= 1 for st in subtasks):
            return "sequential"
        else:
            return "dag"  # Directed acyclic graph

    async def _execute_swarm(
        self,
        swarm: SwarmExecution,
        context: Context
    ) -> List[AgentResult]:
        """
        Execute all subtasks in the swarm

        Args:
            swarm: Swarm execution state
            context: Execution context

        Returns:
            List of results from all subtasks
        """
        if swarm.strategy == "parallel":
            return await self._execute_parallel(swarm, context)
        elif swarm.strategy == "sequential":
            return await self._execute_sequential(swarm, context)
        else:
            return await self._execute_dag(swarm, context)

    async def _execute_parallel(
        self,
        swarm: SwarmExecution,
        context: Context
    ) -> List[AgentResult]:
        """Execute subtasks in parallel"""
        results = []

        # Create semaphore to limit parallelism
        semaphore = asyncio.Semaphore(self.max_parallel_agents)

        async def execute_subtask(subtask: SubTask) -> Optional[AgentResult]:
            async with semaphore:
                return await self._execute_subtask(subtask, swarm, context)

        # Execute all subtasks in parallel
        task_results = await asyncio.gather(
            *[execute_subtask(st) for st in swarm.subtasks],
            return_exceptions=True
        )

        # Filter valid results
        for result in task_results:
            if isinstance(result, AgentResult):
                results.append(result)

        return results

    async def _execute_sequential(
        self,
        swarm: SwarmExecution,
        context: Context
    ) -> List[AgentResult]:
        """Execute subtasks sequentially"""
        results = []

        for subtask in swarm.subtasks:
            result = await self._execute_subtask(subtask, swarm, context)
            if result:
                results.append(result)

        return results

    async def _execute_dag(
        self,
        swarm: SwarmExecution,
        context: Context
    ) -> List[AgentResult]:
        """Execute subtasks respecting DAG dependencies"""
        results = []
        completed_ids = set()
        pending_subtasks = swarm.subtasks.copy()

        while pending_subtasks:
            # Find subtasks with satisfied dependencies
            ready = [
                st for st in pending_subtasks
                if all(dep in completed_ids for dep in st.dependencies)
            ]

            if not ready:
                self.logger.error("Circular dependency detected in subtasks")
                break

            # Execute ready subtasks in parallel
            semaphore = asyncio.Semaphore(self.max_parallel_agents)

            async def execute_ready(subtask: SubTask) -> Optional[AgentResult]:
                async with semaphore:
                    return await self._execute_subtask(subtask, swarm, context)

            batch_results = await asyncio.gather(
                *[execute_ready(st) for st in ready],
                return_exceptions=True
            )

            # Process results
            for subtask, result in zip(ready, batch_results):
                if isinstance(result, AgentResult):
                    results.append(result)
                    if result.success:
                        completed_ids.add(subtask.id)

                pending_subtasks.remove(subtask)

        return results

    async def _execute_subtask(
        self,
        subtask: SubTask,
        swarm: SwarmExecution,
        context: Context
    ) -> Optional[AgentResult]:
        """
        Execute a single subtask

        Args:
            subtask: Subtask to execute
            swarm: Parent swarm
            context: Execution context

        Returns:
            AgentResult or None
        """
        if not self.registry:
            self.logger.error("No agent registry configured")
            return None

        subtask.status = "running"
        subtask.started_at = datetime.utcnow()

        # Try execution with retry
        for attempt in range(subtask.max_attempts):
            subtask.attempts = attempt + 1

            try:
                # Select agent
                agent_id = await self._select_agent_for_subtask(subtask)
                if not agent_id:
                    self.logger.error(f"No agent available for subtask {subtask.id}")
                    continue

                subtask.assigned_agent = agent_id

                # Acquire agent
                acquired = await self.registry.acquire_agent(agent_id, subtask.id)
                if not acquired:
                    self.logger.warning(f"Failed to acquire agent {agent_id}")
                    continue

                # Execute task
                result = await self.registry.execute_task(
                    subtask.task,
                    context,
                    preferred_agent=agent_id
                )

                # Release agent
                if result:
                    await self.registry.release_agent(
                        agent_id,
                        subtask.id,
                        result.success,
                        result.execution_time_ms or 0
                    )

                if result and result.success:
                    subtask.status = "completed"
                    subtask.result = result
                    subtask.completed_at = datetime.utcnow()
                    swarm.completed_subtasks += 1
                    swarm.total_cost += result.cost or 0.0
                    return result

            except Exception as e:
                self.logger.error(f"Subtask {subtask.id} attempt {attempt + 1} failed: {e}")

        # All attempts failed
        subtask.status = "failed"
        subtask.completed_at = datetime.utcnow()
        swarm.failed_subtasks += 1

        return AgentResult(
            success=False,
            output={},
            evidence=[],
            error=f"Failed after {subtask.max_attempts} attempts"
        )

    async def _select_agent_for_subtask(
        self,
        subtask: SubTask
    ) -> Optional[str]:
        """
        Select best agent for subtask

        Args:
            subtask: Subtask to assign

        Returns:
            Agent ID or None
        """
        if not self.registry:
            return None

        # Get required capabilities from metadata
        required_caps = subtask.task.metadata.get("required_capabilities", [])

        if required_caps:
            # Find agents with required capabilities
            for cap_name in required_caps:
                try:
                    capability = AgentCapability(cap_name)
                    agents = await self.registry.find_agents_by_capability(
                        capability,
                        only_available=True
                    )
                    if agents:
                        return agents[0]
                except ValueError:
                    continue

        # Fall back to task type routing
        agent_id = self.registry.route_task(subtask.task)
        return agent_id

    async def _aggregate_results(
        self,
        swarm: SwarmExecution,
        results: List[AgentResult],
        context: Context
    ) -> Dict[str, Any]:
        """
        Aggregate results from all subtasks

        Args:
            swarm: Swarm execution
            results: List of results
            context: Execution context

        Returns:
            Aggregated output
        """
        # Collect all outputs
        outputs = []
        all_evidence = []
        all_artifacts = []

        for result in results:
            if result.success:
                outputs.append(result.output)
                all_evidence.extend(result.evidence)
                all_artifacts.extend(result.artifacts)

        return {
            "swarm_id": swarm.swarm_id,
            "parent_task_id": swarm.parent_task.id,
            "total_subtasks": swarm.total_subtasks,
            "completed_subtasks": swarm.completed_subtasks,
            "failed_subtasks": swarm.failed_subtasks,
            "outputs": outputs,
            "evidence": [
                {
                    "id": e.id,
                    "source": e.source,
                    "description": e.description
                }
                for e in all_evidence
            ],
            "artifacts": all_artifacts,
            "total_cost": swarm.total_cost,
            "total_time_ms": swarm.total_time_ms,
            "success_rate": swarm.completed_subtasks / swarm.total_subtasks if swarm.total_subtasks > 0 else 0.0
        }
